# 📚 Antonio IA · Extractor Científico de Literatura & Generador de Matrices

Aplicativo web completo para búsqueda de literatura científica en **OpenAlex** y **Crossref**, enriquecimiento semántico mediante **Groq AI (Llama 3.3 70B)**, extracción estructurada de modelos, algoritmos y técnicas de estudio, y generación de documentos académicos con formato de revista científica (**Normas APA 7**, **IEEE**, **Vancouver**) exportables a **Word (.docx)** y **Excel (.xlsx)**.

---

## 🌟 Características Principales

1. **Búsqueda Científica Multifuente:**
   - Consulta simultánea en **OpenAlex** y **Crossref** sin necesidad de claves de pago.
   - Filtrado por rango de años (ej. 2020 a 2026), idioma (Español, Inglés, Todos) y exigencia de DOI verificable.
   - Expansión semántica de consulta mediante **Groq AI** (genera sinónimos académicos en inglés y español para maximizar el hallazgo de literatura relevante).

2. **Extracción y Citación Automatizada con Groq:**
   - Identifica y extrae en cada artículo:
     - **Autor / Cita corta** (ej. *Cedillo et al., 2024*).
     - **Técnicas / Algoritmos** empleados (ej. *Árboles de decisión, Random Forest, Redes neuronales, SVM, KNN*).
     - **Mejor precisión / Rendimiento** reportado en el estudio (ej. *Random Forest*, *RandomTree*, o *No especifica*).
     - **Cita bibliográfica completa** en APA 7, IEEE o Vancouver.

3. **Matriz Académica y Documento Idéntico a Revista Científica:**
   - Renderizado con estética de publicación científica (ejemplo: *Revista Visión Empresarial*).
   - Tabla formal APA 7 (sin líneas verticales, bordes superior e inferior limpios).
   - **Párrafo de Síntesis y Discusión Científica:** Redacción automática del análisis comparativo debajo de la tabla con término destacado en negrita (ej. **Árboles de decisión.**).
   - Modo de edición interactivo: Permite editar cualquier celda de la tabla directamente en pantalla antes de descargar.

4. **Exportaciones Profesionales:**
   - **Word (.docx):** Documento con márgenes de 2.54 cm, fuentes académicas, tabla con bordes APA 7, párrafo de síntesis y lista de referencias con sangría francesa (*hanging indent*).
   - **Excel (.xlsx):** Matriz estructurada con estilos, filtros y enlaces DOI activos.
   - **Copiar Markdown/HTML:** Para pegar en Google Docs o Notion.

---

## 🛠️ Estructura del Proyecto

```
Agente IA-3/
├── main.py                     # API principal FastAPI y servidor de estáticos
├── services/
│   ├── academic_search.py      # Conectores OpenAlex & Crossref
│   ├── groq_service.py         # Integración Groq AI (Llama 3.3 / Llama 3.1)
│   └── doc_generator.py        # Generador de documentos Word (.docx) y Excel (.xlsx)
├── static/
│   ├── index.html              # Interfaz de usuario (3 pestañas del flujo)
│   ├── style.css               # Estilos modernos y formato de hoja académica
│   └── app.js                  # Lógica frontend reactiva
├── requirements.txt            # Dependencias Python
├── Procfile                    # Comando de inicio para Render
├── render.yaml                 # Blueprint opcional de Render
├── .env.example                # Plantilla de variables de entorno
└── .gitignore                  # Archivos ignorados por Git
```

---

## 💻 Ejecución Local

### 1. Clonar o abrir el proyecto
Asegúrate de estar en la carpeta raíz del proyecto.

### 2. Crear y activar el entorno virtual
En Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate
```

En Linux/Mac:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variable de entorno (Opcional)
Copia `.env.example` a `.env` y coloca tu clave gratuita de Groq:
```env
GROQ_API_KEY=gsk_tu_clave_de_groq_aqui
```
*(Nota: Si no la configuras en el archivo `.env`, puedes ingresarla directamente desde el botón **"Groq API"** en la interfaz web).*

### 5. Iniciar la aplicación
```bash
python -m uvicorn main:app --reload --port 8000
```
Abre tu navegador en: **`http://localhost:8000`**

---

## 🚀 Subir a Git / GitHub

Abre tu terminal en la carpeta del proyecto y ejecuta:

```bash
# 1. Inicializar el repositorio Git
git init

# 2. Agregar todos los archivos
git add .

# 3. Crear el primer commit
git commit -m "feat: extractor cientifico de literatura y matrices con Groq y Render"

# 4. Cambiar la rama principal a main
git branch -M main

# 5. Conectar con tu repositorio remoto en GitHub
# (Reemplaza la URL por la de tu repositorio creado en github.com/new)
git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git

# 6. Subir el código
git push -u origin main
```

---

## ☁️ Despliegue en Render

Para desplegar este aplicativo en **Render.com** (servicio gratuito y rápido):

1. Ingresa a [dashboard.render.com](https://dashboard.render.com).
2. Haz clic en el botón **New +** y selecciona **Web Service**.
3. Selecciona tu repositorio de GitHub que acabas de subir y presiona **Connect**.
4. Completa la configuración básica:
   - **Name:** `antonio-extractor-ia` *(o el nombre que prefieras)*
   - **Region:** Elige la más cercana (ej. *Oregon* o *Frankfurt*)
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:**
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```
5. En la sección **Environment Variables**, añade:
   - **Key:** `GROQ_API_KEY`
   - **Value:** `gsk_tu_clave_de_groq_aqui`
6. Haz clic en **Create Web Service**.
7. En 2 o 3 minutos, Render habrá construido el proyecto y te proporcionará una URL pública segura `https://tu-app.onrender.com`.

---

## 🔑 Obtener API Key de Groq

1. Visita [console.groq.com](https://console.groq.com).
2. Crea una cuenta gratuita o inicia sesión con Google/GitHub.
3. Ve a **API Keys** y presiona **Create API Key**.
4. Copia tu clave (empieza con `gsk_...`) e ingrésala en la app o en las variables de Render.

---

## 📄 Licencia y Créditos
Desarrollado con arquitectura Python (FastAPI), OpenAlex, Crossref, Groq Cloud API y generadores nativos Office OpenXML.
