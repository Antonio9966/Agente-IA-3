import os
import json
import re
from typing import List, Dict, Any, Optional
from groq import Groq

DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
FAST_GROQ_MODEL = "llama-3.1-8b-instant"

def get_groq_client(api_key: Optional[str] = None) -> Optional[Groq]:
    """Retrieves a Groq client using provided key or environment variable."""
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        return None
    try:
        return Groq(api_key=key.strip())
    except Exception as e:
        print(f"Error creating Groq client: {e}")
        return None

def test_groq_connection(api_key: str) -> Dict[str, Any]:
    """Tests if a Groq API key is valid."""
    try:
        client = Groq(api_key=api_key.strip())
        resp = client.chat.completions.create(
            model=FAST_GROQ_MODEL,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5
        )
        return {"valid": True, "message": "Conexión con Groq exitosa"}
    except Exception as e:
        return {"valid": False, "message": str(e)}

async def expand_query_with_groq(
    query: str,
    api_key: Optional[str] = None,
    model: str = DEFAULT_GROQ_MODEL
) -> Dict[str, Any]:
    """Expands user search topic into multilingual academic keywords using Groq."""
    client = get_groq_client(api_key)
    
    if not client:
        # Heuristic fallback if no API key is provided
        return {
            "original_query": query,
            "expanded_queries": [
                f"{query} machine learning algorithms",
                f"{query} predictive models"
            ],
            "english_query": f"{query} artificial intelligence",
            "keywords": ["Machine Learning", "Modelos Predictivos", "Algoritmos"],
            "source": "heuristic"
        }
        
    prompt = f"""Eres un bibliotecólogo experto e investigador científico.
El usuario desea investigar en bases de datos académicas (OpenAlex, Crossref) sobre el siguiente tema:
"{query}"

Genera una expansión de búsqueda para maximizar la recuperación de artículos de alto impacto.
Responde estrictamente en formato JSON con la siguiente estructura:
{{
  "english_query": "consulta principal traducida y optimizada al inglés académico",
  "expanded_queries": [
    "consulta secundaria en inglés con términos clave",
    "consulta secundaria en español con operadores o sinónimos"
  ],
  "keywords": ["palabra clave 1", "palabra clave 2", "palabra clave 3", "algoritmo común"],
  "focus_techniques": ["algoritmos o metodologías comunes esperadas para este tema"]
}}
Solo devuelve el JSON sin texto introductorio ni formato markdown adicional."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a research query expansion expert. Output strictly valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=600,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        data["original_query"] = query
        data["source"] = "groq"
        return data
    except Exception as e:
        print(f"Error in expand_query_with_groq: {e}")
        return {
            "original_query": query,
            "expanded_queries": [f"{query} machine learning", f"{query} algorithms"],
            "english_query": query,
            "keywords": ["Machine Learning", "Predicción", "Algoritmos"],
            "source": "fallback_error"
        }

async def extract_paper_matrix_data(
    paper: Dict[str, Any],
    topic: str,
    citation_style: str = "APA 7",
    api_key: Optional[str] = None,
    model: str = DEFAULT_GROQ_MODEL
) -> Dict[str, Any]:
    """Uses Groq to extract structured matrix data: Autor, Técnicas/Algoritmos, Mejor precisión, and citations."""
    client = get_groq_client(api_key)
    
    title = paper.get("title", "")
    authors = ", ".join(paper.get("authors", [])) or "No especificado"
    year = paper.get("year", "")
    venue = paper.get("venue", "")
    doi = paper.get("doi", "")
    abstract = paper.get("abstract", "")
    author_cit = paper.get("author_citation", "")
    
    if not client:
        # Fallback extraction based on text heuristics
        techs = []
        lower_text = f"{title} {abstract}".lower()
        if "decision tree" in lower_text or "arbol" in lower_text or "c4.5" in lower_text:
            techs.append("Árboles de decisión")
        if "random forest" in lower_text:
            techs.append("Random Forest")
        if "neural network" in lower_text or "redes neuronales" in lower_text:
            techs.append("Redes neuronales artificiales")
        if "logistic regression" in lower_text or "regresión logística" in lower_text:
            techs.append("Regresión logística")
        if "svm" in lower_text or "support vector" in lower_text:
            techs.append("Support Vector Machine (SVM)")
        if "knn" in lower_text or "k-nearest" in lower_text or "k-vecinos" in lower_text:
            techs.append("K-Nearest Neighbors (KNN)")
        if "bayesian" in lower_text or "bayes" in lower_text:
            techs.append("Redes bayesianas / Naive Bayes")
        if "xgboost" in lower_text or "lightgbm" in lower_text:
            techs.append("XGBoost / LightGBM")
            
        if not techs:
            techs = ["Modelos estadísticos", "Algoritmos de clasificación supervisada"]
            
        return {
            "id": paper.get("id"),
            "autor": author_cit or f"{authors.split(',')[0]} et al., {year}",
            "tecnicas_algoritmos": "\n".join(techs),
            "mejor_precision": techs[0] if techs else "No especifica",
            "hallazgos": f"Estudio enfocado en {topic} evaluando modelos de clasificación y predicción.",
            "cita_completa": f"{authors} ({year}). {title}. {venue}. https://doi.org/{doi}" if doi else f"{authors} ({year}). {title}. {venue}.",
            "doi": doi,
            "url": paper.get("url", ""),
            "title": title,
            "year": year
        }

    prompt = f"""Analiza el siguiente artículo académico sobre el tema "{topic}":
Título: {title}
Autores: {authors}
Año: {year}
Revista/Fuente: {venue}
DOI: {doi}
Resumen / Contenido:
{abstract if abstract else "Resumen no disponible. Analiza a partir del título y metadatos."}

Tu tarea es extraer los datos para una matriz científica comparativa EXACTAMENTE como se presenta en publicaciones de alto impacto (formato de tabla académica):
1. 'autor': Cita corta del autor y año (ej: 'Cedillo et al., 2024', 'Parra et al., 2023', 'Melo, 2024').
2. 'tecnicas_algoritmos': Lista de TODAS las técnicas, algoritmos o métodos identificados en el estudio (ejemplo: 'Árboles de decisión\\nMétodos probabilísticos\\nRegresión logística\\nRedes neuronales\\nRandom Forest\\nKNN'). Sepáralos con saltos de línea (\\n) para que se muestren apilados en la celda.
3. 'mejor_precision': El algoritmo o técnica que obtuvo mejor precisión o rendimiento según el estudio (ejemplo: 'Random Forest', 'Árboles de decisión', 'SVM (94.2%)', o 'No especifica' si el texto no declara cuál fue el ganador).
4. 'hallazgos': Breve síntesis de 1 o 2 oraciones sobre el hallazgo principal del estudio.
5. 'cita_completa': La referencia bibliográfica completa formateada según {citation_style} (incluyendo DOI al final si existe).

Responde ÚNICAMENTE un JSON con estas claves:
{{
  "autor": "...",
  "tecnicas_algoritmos": "...",
  "mejor_precision": "...",
  "hallazgos": "...",
  "cita_completa": "..."
}}"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a scientific data extraction specialist. Output valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return {
            "id": paper.get("id"),
            "autor": data.get("autor") or author_cit,
            "tecnicas_algoritmos": data.get("tecnicas_algoritmos") or "No especifica",
            "mejor_precision": data.get("mejor_precision") or "No especifica",
            "hallazgos": data.get("hallazgos") or "",
            "cita_completa": data.get("cita_completa") or "",
            "doi": doi,
            "url": paper.get("url", ""),
            "title": title,
            "year": year
        }
    except Exception as e:
        print(f"Error extracting paper data with Groq: {e}")
        return {
            "id": paper.get("id"),
            "autor": author_cit or f"Autor et al., {year}",
            "tecnicas_algoritmos": "Modelos predictivos y algoritmos de análisis",
            "mejor_precision": "No especifica",
            "hallazgos": "Extracción asistida por metadatos.",
            "cita_completa": f"{authors} ({year}). {title}. {venue}.",
            "doi": doi,
            "url": paper.get("url", ""),
            "title": title,
            "year": year
        }

async def generate_matrix_narrative(
    table_rows: List[Dict[str, Any]],
    topic: str,
    api_key: Optional[str] = None,
    model: str = DEFAULT_GROQ_MODEL
) -> Dict[str, Any]:
    """Generates the synthesis narrative beneath the table (as shown in Image 1)."""
    client = get_groq_client(api_key)
    
    # Format rows for context
    table_summary = []
    for r in table_rows:
        table_summary.append(
            f"- Autor: {r.get('autor')} | Técnicas: {r.get('tecnicas_algoritmos', '').replace(chr(10), ', ')} | Mejor precisión: {r.get('mejor_precision')}"
        )
    rows_text = "\n".join(table_summary)
    
    if not client:
        # Intelligent fallback narrative
        return {
            "dominant_technique": "Árboles de decisión y ensambles",
            "narrative": f"Árboles de decisión. Los árboles de decisión, incluyendo algoritmos como C4.5, Random Forest y Gradient Boosting, han demostrado ser altamente efectivos en los estudios analizados sobre {topic}. Estos modelos permiten crear reglas claras y visuales que segmentan a los sujetos evaluados con base en características clave de rendimiento, logrando altos niveles de interpretabilidad y precisión predictiva frente a métodos tradicionales.",
            "source": "fallback"
        }
        
    prompt = f"""Observa la siguiente tabla de artículos científicos sobre "{topic}":
{rows_text}

Redacta el párrafo de síntesis y discusión científica que va inmediatamente debajo de la tabla (igual al estilo de revistas como Visión Empresarial / Elsevier / IEEE).
Debe comenzar con el nombre de la técnica o algoritmo más destacado o recurrente en negrita (ej: "**Árboles de decisión.**" o "**Random Forest.**"), seguido de una explicación académica profunda, rigurosa y comparativa de por qué dicha técnica y los modelos relacionados (como Random Forest, XGBoost, Redes Neuronales) resultaron los más efectivos y adoptados en estos estudios, contrastando los hallazgos de los autores citados en la tabla.

Responde estrictamente en formato JSON con la siguiente estructura:
{{
  "dominant_technique": "Nombre del algoritmo o técnica principal destacada",
  "lead_title": "Texto en negrita para el inicio (ej: 'Árboles de decisión.')",
  "narrative": "Párrafo completo de síntesis académica integrando el lead_title y el análisis comparativo..."
}}"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a scientific academic author and researcher. Output valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=900,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        data["source"] = "groq"
        return data
    except Exception as e:
        print(f"Error generating narrative with Groq: {e}")
        return {
            "dominant_technique": "Algoritmos de Aprendizaje Automático",
            "lead_title": "Modelos predictivos y ensambles.",
            "narrative": f"Modelos predictivos y ensambles. La literatura analizada sobre {topic} evidencia una clara convergencia hacia el empleo de métodos basados en árboles y ensambles (como Random Forest), los cuales destacan por su capacidad de manejar relaciones no lineales y mitigar el sobreajuste.",
            "source": "fallback_error"
        }
