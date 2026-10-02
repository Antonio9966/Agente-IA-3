import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from services.academic_search import search_academic_literature
from services.groq_service import (
    expand_query_with_groq,
    extract_paper_matrix_data,
    generate_matrix_narrative,
    test_groq_connection,
    DEFAULT_GROQ_MODEL
)
from services.doc_generator import generate_word_matrix_doc, generate_excel_matrix_sheet

load_dotenv()

app = FastAPI(
    title="Antonio IA · Extractor Científico",
    description="Herramienta de búsqueda en literatura científica (OpenAlex & Crossref) y extracción de matrices comparativas con Groq AI.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Pydantic Models -----------------

class GroqKeyCheckRequest(BaseModel):
    api_key: str

class QueryExpansionRequest(BaseModel):
    query: str
    api_key: Optional[str] = None
    model: Optional[str] = DEFAULT_GROQ_MODEL

class AcademicSearchRequest(BaseModel):
    query: str
    expanded_queries: Optional[List[str]] = None
    year_from: int = 2020
    year_to: int = 2026
    language: str = "all"
    articles_per_source: int = 25
    require_doi: bool = True

class ExtractPaperRequest(BaseModel):
    paper: Dict[str, Any]
    topic: str
    citation_style: str = "APA 7"
    api_key: Optional[str] = None
    model: Optional[str] = DEFAULT_GROQ_MODEL

class ExtractBatchRequest(BaseModel):
    papers: List[Dict[str, Any]]
    topic: str
    citation_style: str = "APA 7"
    api_key: Optional[str] = None
    model: Optional[str] = DEFAULT_GROQ_MODEL

class NarrativeRequest(BaseModel):
    table_rows: List[Dict[str, Any]]
    topic: str
    api_key: Optional[str] = None
    model: Optional[str] = DEFAULT_GROQ_MODEL

class DocxExportRequest(BaseModel):
    table_rows: List[Dict[str, Any]]
    table_number: str = "Tabla 4"
    table_title: str = "Técnicas y algoritmos utilizados en estudios sobre deserción universitaria"
    narrative_text: str = ""
    lead_title: str = "Árboles de decisión."
    references: Optional[List[str]] = None
    journal_header: str = "VISIÓN EMPRESARIAL"

class XlsxExportRequest(BaseModel):
    table_rows: List[Dict[str, Any]]
    table_title: str = "Matriz de Literatura Científica"
    topic: str = ""

# ----------------- Sample / Reference Data -----------------
# Matches Image 1 from user reference
SAMPLE_DATA = [
    {
        "id": "ref-cedillo-2024",
        "autor": "Cedillo et al., 2024",
        "tecnicas_algoritmos": "Estadísticas y algebraicas\nRedes bayesianas\nAlgoritmos evolutivos\nTablas de contingencia Árboles de decisión\nRedes neuronales artificiales\nEstocásticas y borrosas",
        "mejor_precision": "No especifica",
        "hallazgos": "Revisión sistemática de múltiples paradigmas algorítmicos aplicados a la predicción del abandono universitario.",
        "cita_completa": "Cedillo, C. A., Grón, H. D., & Ronquillo, A. L. (2024). Minería de datos para la predicción de la deserción estudiantil universitaria. Visión Empresarial, 14(2), 45-58. https://doi.org/10.32645/ve.2024.14",
        "doi": "10.32645/ve.2024.14",
        "title": "Minería de datos para la predicción de la deserción estudiantil universitaria",
        "year": 2024
    },
    {
        "id": "ref-parra-2023",
        "autor": "Parra et al., 2023",
        "tecnicas_algoritmos": "Árboles de decisión\nMétodos probabilísticos\nRegresión logística\nRedes neuronales\nK-means\nK-vecinos",
        "mejor_precision": "Árboles de decisión",
        "hallazgos": "Comparativa entre 6 familias de algoritmos; los árboles de decisión demostraron mayor capacidad explicativa y precisión.",
        "cita_completa": "Parra, M. A., Gómez, C. A., & Girón, H. D. (2023). Modelos de aprendizaje automático para el análisis de permanencia académica. Revista Iberoamericana de Educación Superior, 14(40), 89-106.",
        "doi": "10.22201/ries.2023.40",
        "title": "Modelos de aprendizaje automático para el análisis de permanencia académica",
        "year": 2023
    },
    {
        "id": "ref-cornejo-2023",
        "autor": "Cornejo et al., 2023",
        "tecnicas_algoritmos": "DecisionTable\nJRip OneR\nDecisionStump HoeffdingTree\nJ48\nLMT\nRandomForest RandomTree\nREPTree PART",
        "mejor_precision": "RandomTree",
        "hallazgos": "Evaluación extensiva en entornos Weka de algoritmos de reglas y árboles de decisión jerárquicos.",
        "cita_completa": "Cornejo, L., Véliz, F., & Zambrano, R. (2023). Desempeño predictivo de clasificadores basados en árboles y reglas en deserción estudiantil. Ingeniare. Revista Chilena de Ingeniería, 31(3), 320-335.",
        "doi": "10.4067/S0718-33052023000300320",
        "title": "Desempeño predictivo de clasificadores basados en árboles y reglas en deserción estudiantil",
        "year": 2023
    },
    {
        "id": "ref-melo-2024",
        "autor": "Melo, 2024",
        "tecnicas_algoritmos": "Regresión logística\nÁrboles de decisión Random Forest\nK-Nearest Neighbors (KNN)\nSupport Vector Machine (SVM)",
        "mejor_precision": "Random Forest",
        "hallazgos": "Random Forest superó a SVM y regresión logística en métricas F1 y AUC-ROC en cohortes universitarias.",
        "cita_completa": "Melo, S. (2024). Algoritmos de ensamble aplicados a la retención de estudiantes de primer año. Cuadernos de Investigación Educativa, 15(1), 112-129.",
        "doi": "10.18861/cied.2024.15.1",
        "title": "Algoritmos de ensamble aplicados a la retención de estudiantes de primer año",
        "year": 2024
    },
    {
        "id": "ref-patino-2024",
        "autor": "Patiño et al., 2024",
        "tecnicas_algoritmos": "Random Forest\nNaive Bayes LightGBM XGBoost",
        "mejor_precision": "Random Forest",
        "hallazgos": "Comprobación del balance entre precisión y costo computacional de Random Forest frente a algoritmos de boosting.",
        "cita_completa": "Patiño, J. C., Moreno, A., & Tapia, K. (2024). Boosting versus bagging en la predicción temprana del abandono escolar superior. Revista Latinoamericana de Tecnología Educativa, 23(2), 75-92.",
        "doi": "10.17398/1695-288X.23.2.75",
        "title": "Boosting versus bagging en la predicción temprana del abandono escolar superior",
        "year": 2024
    }
]

SAMPLE_NARRATIVE = {
    "dominant_technique": "Árboles de decisión",
    "lead_title": "Árboles de decisión.",
    "narrative": "Árboles de decisión. Los árboles de decisión, incluyendo algoritmos como C4.5 y Random Forest, han demostrado ser altamente efectivos en la clasificación de estudiantes con riesgo de deserción. Estos modelos permiten crear reglas claras y visuales que segmentan a los estudiantes con base en características como desempeño académico, número de materias reprobadas o asistencia."
}

# ----------------- API Endpoints -----------------

@app.get("/api/health")
async def health_check():
    has_key = bool(os.getenv("GROQ_API_KEY"))
    return {
        "status": "online",
        "groq_configured_in_env": has_key,
        "default_model": DEFAULT_GROQ_MODEL
    }

@app.post("/api/check-groq")
async def check_groq(req: GroqKeyCheckRequest):
    result = test_groq_connection(req.api_key)
    return result

@app.post("/api/expand-query")
async def api_expand_query(req: QueryExpansionRequest):
    result = await expand_query_with_groq(
        query=req.query,
        api_key=req.api_key,
        model=req.model or DEFAULT_GROQ_MODEL
    )
    return result

@app.post("/api/search")
async def api_search(req: AcademicSearchRequest):
    articles = await search_academic_literature(
        query=req.query,
        expanded_queries=req.expanded_queries,
        year_from=req.year_from,
        year_to=req.year_to,
        language=req.language,
        articles_per_source=req.articles_per_source,
        require_doi=req.require_doi
    )
    return {
        "total": len(articles),
        "query": req.query,
        "articles": articles
    }

@app.post("/api/extract-single")
async def api_extract_single(req: ExtractPaperRequest):
    extracted = await extract_paper_matrix_data(
        paper=req.paper,
        topic=req.topic,
        citation_style=req.citation_style,
        api_key=req.api_key,
        model=req.model or DEFAULT_GROQ_MODEL
    )
    return extracted

@app.post("/api/extract-batch")
async def api_extract_batch(req: ExtractBatchRequest):
    rows = []
    for paper in req.papers:
        row = await extract_paper_matrix_data(
            paper=paper,
            topic=req.topic,
            citation_style=req.citation_style,
            api_key=req.api_key,
            model=req.model or DEFAULT_GROQ_MODEL
        )
        rows.append(row)
    return {
        "total": len(rows),
        "rows": rows
    }

@app.post("/api/generate-narrative")
async def api_generate_narrative(req: NarrativeRequest):
    narrative = await generate_matrix_narrative(
        table_rows=req.table_rows,
        topic=req.topic,
        api_key=req.api_key,
        model=req.model or DEFAULT_GROQ_MODEL
    )
    return narrative

@app.get("/api/sample-data")
async def get_sample_data():
    """Returns the reference dataset from Image 1 for instant preview and testing."""
    return {
        "topic": "deserción universitaria",
        "table_number": "Tabla 4",
        "table_title": "Técnicas y algoritmos utilizados en estudios sobre deserción universitaria",
        "journal_header": "VISIÓN EMPRESARIAL",
        "rows": SAMPLE_DATA,
        "narrative": SAMPLE_NARRATIVE
    }

@app.post("/api/export/docx")
async def export_docx(req: DocxExportRequest):
    buffer = generate_word_matrix_doc(
        table_rows=req.table_rows,
        table_number=req.table_number,
        table_title=req.table_title,
        narrative_text=req.narrative_text,
        lead_title=req.lead_title,
        references=req.references,
        journal_header=req.journal_header
    )
    filename = f"Matriz_Cientifica_{req.table_number.replace(' ', '_')}.docx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.post("/api/export/xlsx")
async def export_xlsx(req: XlsxExportRequest):
    buffer = generate_excel_matrix_sheet(
        table_rows=req.table_rows,
        table_title=req.table_title,
        topic=req.topic
    )
    filename = "Matriz_Literatura_Cientifica.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

# Static files mount
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
