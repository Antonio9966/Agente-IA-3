// ========================================================
// ANTONIO IA · EXTRACTOR CIENTÍFICO DE LITERATURA & MATRICES
// Client Logic: State management, API calls, and UX
// ========================================================

const state = {
  groqApiKey: localStorage.getItem("groq_api_key") || "",
  serverHasGroqKey: false,
  searchArticles: [],
  selectedArticles: [],
  extractedRows: [],
  narrativeData: {
    dominant_technique: "Árboles de decisión",
    lead_title: "Árboles de decisión.",
    narrative: "Árboles de decisión. Los árboles de decisión, incluyendo algoritmos como C4.5 y Random Forest, han demostrado ser altamente efectivos en la clasificación de estudiantes con riesgo de deserción."
  },
  currentTopic: "Técnicas y algoritmos en deserción universitaria",
  citationStyle: "APA 7",
  tableNumber: "Tabla 4",
  tableTitle: "Técnicas y algoritmos utilizados en estudios sobre deserción universitaria",
  journalHeader: "VISIÓN EMPRESARIAL",
  isEditingCells: false
};

// ----------------- DOM Elements -----------------
const elements = {
  // Tabs
  stepTabs: document.querySelectorAll(".step-tab"),
  tabPanes: document.querySelectorAll(".tab-pane"),
  selectedBadge: document.getElementById("selectedBadge"),
  
  // Search Form
  searchForm: document.getElementById("searchForm"),
  topicInput: document.getElementById("topicInput"),
  yearFromInput: document.getElementById("yearFromInput"),
  yearToInput: document.getElementById("yearToInput"),
  languageSelect: document.getElementById("languageSelect"),
  articlesPerSourceInput: document.getElementById("articlesPerSourceInput"),
  expandQueryCheck: document.getElementById("expandQueryCheck"),
  requireDoiCheck: document.getElementById("requireDoiCheck"),
  btnSearch: document.getElementById("btnSearch"),
  
  // Results
  searchSuccessAlert: document.getElementById("searchSuccessAlert"),
  foundCount: document.getElementById("foundCount"),
  resultsWrapper: document.getElementById("resultsWrapper"),
  articlesList: document.getElementById("articlesList"),
  selectAllCheck: document.getElementById("selectAllCheck"),
  selectionCounter: document.getElementById("selectionCounter"),
  btnProceedToExtract: document.getElementById("btnProceedToExtract"),
  
  // Extraction Config
  citationStyleSelect: document.getElementById("citationStyleSelect"),
  groqModelSelect: document.getElementById("groqModelSelect"),
  tableNumberInput: document.getElementById("tableNumberInput"),
  journalHeaderInput: document.getElementById("journalHeaderInput"),
  tableTitleInput: document.getElementById("tableTitleInput"),
  btnStartExtraction: document.getElementById("btnStartExtraction"),
  extractionProgressBox: document.getElementById("extractionProgressBox"),
  progressStatusText: document.getElementById("progressStatusText"),
  progressPercent: document.getElementById("progressPercent"),
  progressBarFill: document.getElementById("progressBarFill"),
  selectedArticlesReview: document.getElementById("selectedArticlesReview"),
  extractCountDisplay: document.getElementById("extractCountDisplay"),
  
  // Sheet & Exports (Tab 3)
  displayJournalHeader: document.getElementById("displayJournalHeader"),
  displayTableNumber: document.getElementById("displayTableNumber"),
  displayTableTitle: document.getElementById("displayTableTitle"),
  academicTableBody: document.getElementById("academicTableBody"),
  narrativeParagraph: document.getElementById("narrativeParagraph"),
  referencesList: document.getElementById("referencesList"),
  btnDownloadDocx: document.getElementById("btnDownloadDocx"),
  btnDownloadXlsx: document.getElementById("btnDownloadXlsx"),
  btnCopyMarkdown: document.getElementById("btnCopyMarkdown"),
  btnToggleEditMode: document.getElementById("btnToggleEditMode"),
  
  // Modals
  groqModal: document.getElementById("groqModal"),
  btnOpenGroqModal: document.getElementById("btnOpenGroqModal"),
  btnCloseGroqModal: document.getElementById("btnCloseGroqModal"),
  groqApiKeyInput: document.getElementById("groqApiKeyInput"),
  btnSaveGroqKey: document.getElementById("btnSaveGroqKey"),
  btnTestGroqKey: document.getElementById("btnTestGroqKey"),
  groqKeyStatusAlert: document.getElementById("groqKeyStatusAlert"),
  groqStatusDot: document.getElementById("groqStatusDot"),
  groqStatusText: document.getElementById("groqStatusText"),
  
  gitModal: document.getElementById("gitModal"),
  btnOpenGitModal: document.getElementById("btnOpenGitModal"),
  btnCloseGitModal: document.getElementById("btnCloseGitModal"),
  btnCloseGitModal2: document.getElementById("btnCloseGitModal2"),
  
  btnLoadSample: document.getElementById("btnLoadSample"),
  toastContainer: document.getElementById("toastContainer")
};

// ----------------- Initialization -----------------
document.addEventListener("DOMContentLoaded", async () => {
  setupEventListeners();
  setupQuickChips();
  await checkHealthAndGroqStatus();
});

// ----------------- Event Listeners -----------------
function setupEventListeners() {
  // Tab switching
  elements.stepTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const targetTab = tab.getAttribute("data-tab");
      switchTab(targetTab);
    });
  });

  // Search Form Submit
  elements.searchForm.addEventListener("submit", handleSearchSubmit);

  // Select all checkbox
  elements.selectAllCheck.addEventListener("change", (e) => {
    const isChecked = e.target.checked;
    const itemChecks = document.querySelectorAll(".article-item-checkbox");
    itemChecks.forEach(cb => {
      cb.checked = isChecked;
      const card = cb.closest(".article-card");
      if (card) {
        card.classList.toggle("selected", isChecked);
      }
    });
    updateSelectedArticlesFromCheckboxes();
  });

  // Proceed to Extract Tab
  elements.btnProceedToExtract.addEventListener("click", () => {
    if (state.selectedArticles.length === 0) {
      showToast("Por favor selecciona al menos un artículo para extraer.", "warning");
      return;
    }
    renderSelectedReviewList();
    switchTab("tab-extract");
  });

  // Start Extraction
  elements.btnStartExtraction.addEventListener("click", handleStartExtraction);

  // Exports
  elements.btnDownloadDocx.addEventListener("click", handleDownloadDocx);
  elements.btnDownloadXlsx.addEventListener("click", handleDownloadXlsx);
  elements.btnCopyMarkdown.addEventListener("click", handleCopyTable);
  elements.btnToggleEditMode.addEventListener("click", toggleEditMode);

  // Sample Data Loader
  elements.btnLoadSample.addEventListener("click", loadSampleData);

  // Modals
  elements.btnOpenGroqModal.addEventListener("click", openGroqModal);
  elements.btnCloseGroqModal.addEventListener("click", closeGroqModal);
  elements.groqModal.addEventListener("click", (e) => {
    if (e.target === elements.groqModal) closeGroqModal();
  });

  elements.btnSaveGroqKey.addEventListener("click", saveGroqKey);
  elements.btnTestGroqKey.addEventListener("click", testGroqKey);

  elements.btnOpenGitModal.addEventListener("click", () => elements.gitModal.style.display = "flex");
  elements.btnCloseGitModal.addEventListener("click", () => elements.gitModal.style.display = "none");
  elements.btnCloseGitModal2.addEventListener("click", () => elements.gitModal.style.display = "none");
  elements.gitModal.addEventListener("click", (e) => {
    if (e.target === elements.gitModal) elements.gitModal.style.display = "none";
  });
}

// ----------------- Quick Query Chips -----------------
function setupQuickChips() {
  document.querySelectorAll(".chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const q = chip.getAttribute("data-query");
      elements.topicInput.value = q;
      elements.topicInput.focus();
    });
  });
}

// ----------------- Tab Navigation -----------------
function switchTab(tabId) {
  elements.stepTabs.forEach(t => {
    t.classList.toggle("active", t.getAttribute("data-tab") === tabId);
  });
  elements.tabPanes.forEach(pane => {
    pane.classList.toggle("active", pane.id === tabId);
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ----------------- Toast Notifications -----------------
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  const icons = { success: "✅", info: "ℹ️", warning: "⚠️", error: "❌" };
  toast.innerHTML = `<span>${icons[type] || ""}</span><span>${message}</span>`;
  elements.toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ----------------- Health & Groq Status -----------------
async function checkHealthAndGroqStatus() {
  try {
    const res = await fetch("/api/health");
    if (res.ok) {
      const data = await res.json();
      state.serverHasGroqKey = data.groq_configured_in_env;
      updateGroqStatusUI();
    }
  } catch (e) {
    console.warn("Could not check health:", e);
  }
}

function updateGroqStatusUI() {
  const hasKey = Boolean(state.groqApiKey || state.serverHasGroqKey);
  if (hasKey) {
    elements.groqStatusDot.className = "status-dot dot-green";
    elements.groqStatusText.textContent = "Groq Activo";
  } else {
    elements.groqStatusDot.className = "status-dot dot-yellow";
    elements.groqStatusText.textContent = "Configurar Groq";
  }
}

function openGroqModal() {
  elements.groqApiKeyInput.value = state.groqApiKey;
  elements.groqKeyStatusAlert.style.display = "none";
  elements.groqModal.style.display = "flex";
}

function closeGroqModal() {
  elements.groqModal.style.display = "none";
}

async function testGroqKey() {
  const key = elements.groqApiKeyInput.value.trim();
  if (!key) {
    showModalAlert("Ingresa una clave de Groq válida (gsk_...)", "error");
    return;
  }
  showModalAlert("Validando conexión con Groq...", "info");
  try {
    const res = await fetch("/api/check-groq", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_key: key })
    });
    const data = await res.json();
    if (data.valid) {
      showModalAlert("✅ Conexión con Groq verificada con éxito", "success");
    } else {
      showModalAlert(`❌ Error de validación: ${data.message}`, "error");
    }
  } catch (err) {
    showModalAlert(`Error al conectar con el servidor: ${err.message}`, "error");
  }
}

function saveGroqKey() {
  const key = elements.groqApiKeyInput.value.trim();
  state.groqApiKey = key;
  localStorage.setItem("groq_api_key", key);
  updateGroqStatusUI();
  closeGroqModal();
  showToast("Clave de Groq guardada correctamente.", "success");
}

function showModalAlert(msg, type) {
  elements.groqKeyStatusAlert.className = `modal-alert ${type}`;
  elements.groqKeyStatusAlert.textContent = msg;
  elements.groqKeyStatusAlert.style.display = "block";
}

// ----------------- Search Execution (Tab 1) -----------------
async function handleSearchSubmit(e) {
  e.preventDefault();
  const query = elements.topicInput.value.trim();
  if (!query) return;

  state.currentTopic = query;
  elements.tableTitleInput.value = `Técnicas y algoritmos utilizados en estudios sobre ${query}`;

  const originalBtnHTML = elements.btnSearch.innerHTML;
  elements.btnSearch.disabled = true;
  elements.btnSearch.innerHTML = `<span class="btn-icon">⏳</span><span class="btn-text">Buscando en OpenAlex y Crossref...</span>`;

  try {
    let expandedQueries = [];
    if (elements.expandQueryCheck.checked) {
      // Step 1: Groq Query Expansion
      try {
        const expRes = await fetch("/api/expand-query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: query,
            api_key: state.groqApiKey || undefined
          })
        });
        if (expRes.ok) {
          const expData = await expRes.json();
          expandedQueries = expData.expanded_queries || [];
          if (expData.english_query) {
            expandedQueries.unshift(expData.english_query);
          }
        }
      } catch (expErr) {
        console.warn("Expansion error:", expErr);
      }
    }

    // Step 2: Academic Search
    const searchRes = await fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: query,
        expanded_queries: expandedQueries,
        year_from: parseInt(elements.yearFromInput.value, 10) || 2020,
        year_to: parseInt(elements.yearToInput.value, 10) || 2026,
        language: elements.languageSelect.value,
        articles_per_source: parseInt(elements.articlesPerSourceInput.value, 10) || 25,
        require_doi: elements.requireDoiCheck.checked
      })
    });

    if (!searchRes.ok) throw new Error("Error en la búsqueda académica");

    const data = await searchRes.json();
    state.searchArticles = data.articles || [];

    // Render results
    renderSearchResults(state.searchArticles);

  } catch (err) {
    console.error("Search failed:", err);
    showToast(`Error al buscar literatura: ${err.message}`, "error");
  } finally {
    elements.btnSearch.disabled = false;
    elements.btnSearch.innerHTML = originalBtnHTML;
  }
}

function renderSearchResults(articles) {
  elements.foundCount.textContent = articles.length;
  elements.searchSuccessAlert.style.display = "flex";
  elements.resultsWrapper.style.display = "block";

  if (articles.length === 0) {
    elements.articlesList.innerHTML = `
      <div style="text-align: center; padding: 40px; color: var(--text-muted);">
        <p>No se encontraron artículos con los filtros aplicados. Intenta ampliar el rango de años o desmarcar "Exigir DOI".</p>
      </div>
    `;
    elements.btnProceedToExtract.disabled = true;
    return;
  }

  // Auto-select top 8 articles by default
  const defaultSelectedCount = Math.min(8, articles.length);

  elements.articlesList.innerHTML = articles.map((art, idx) => {
    const isChecked = idx < defaultSelectedCount;
    const authorLine = art.authors && art.authors.length ? art.authors.slice(0, 3).join(", ") + (art.authors.length > 3 ? " et al." : "") : "Autor no especificado";
    const sourceBadgeClass = art.source === "OpenAlex" ? "badge-openalex" : "badge-crossref";
    const doiUrl = art.doi ? (art.doi.startsWith("http") ? art.doi : `https://doi.org/${art.doi}`) : art.url;

    return `
      <div class="article-card ${isChecked ? 'selected' : ''}" data-index="${idx}">
        <div class="article-check-area">
          <label class="custom-checkbox">
            <input type="checkbox" class="article-item-checkbox" data-index="${idx}" ${isChecked ? 'checked' : ''}>
            <span class="checkmark"></span>
          </label>
        </div>
        <div class="article-content">
          <div class="article-header">
            <h3 class="article-title">
              <a href="${doiUrl || '#'}" target="_blank" rel="noopener">${escapeHtml(art.title)}</a>
            </h3>
            <span class="meta-badge ${sourceBadgeClass}">${art.source}</span>
          </div>
          <div class="article-meta">
            <span class="meta-author">👤 ${escapeHtml(authorLine)}</span>
            <span>📅 ${art.year || 's.f.'}</span>
            <span>🏛️ ${escapeHtml(art.venue || 'Revista')}</span>
            ${art.doi ? `<a href="${doiUrl}" target="_blank" class="meta-doi">🔗 DOI: ${escapeHtml(art.doi)}</a>` : ''}
          </div>
          ${art.abstract ? `
            <div class="article-abstract" id="abstract-${idx}">
              ${escapeHtml(art.abstract)}
            </div>
            <button type="button" class="btn-toggle-abstract" onclick="toggleAbstract(${idx})">Ver más / Ver menos</button>
          ` : '<div style="font-size:0.8rem; color:#94a3b8; font-style:italic;">Resumen completo no disponible en metadatos abiertos</div>'}
        </div>
      </div>
    `;
  }).join("");

  // Attach card checkboxes
  document.querySelectorAll(".article-item-checkbox").forEach(cb => {
    cb.addEventListener("change", (e) => {
      const idx = e.target.getAttribute("data-index");
      const card = e.target.closest(".article-card");
      if (card) {
        card.classList.toggle("selected", e.target.checked);
      }
      updateSelectedArticlesFromCheckboxes();
    });
  });

  updateSelectedArticlesFromCheckboxes();
}

window.toggleAbstract = function(idx) {
  const el = document.getElementById(`abstract-${idx}`);
  if (el) el.classList.toggle("expanded");
};

function updateSelectedArticlesFromCheckboxes() {
  const checkboxes = document.querySelectorAll(".article-item-checkbox:checked");
  state.selectedArticles = [];
  checkboxes.forEach(cb => {
    const idx = parseInt(cb.getAttribute("data-index"), 10);
    if (state.searchArticles[idx]) {
      state.selectedArticles.push(state.searchArticles[idx]);
    }
  });

  const count = state.selectedArticles.length;
  elements.selectionCounter.textContent = `${count} seleccionados`;
  elements.selectedBadge.textContent = count;
  elements.extractCountDisplay.textContent = count;
  elements.btnProceedToExtract.disabled = count === 0;

  // Sync select all state
  const totalCheckboxes = document.querySelectorAll(".article-item-checkbox").length;
  elements.selectAllCheck.checked = totalCheckboxes > 0 && count === totalCheckboxes;
}

// ----------------- Extraction Review (Tab 2) -----------------
function renderSelectedReviewList() {
  elements.extractCountDisplay.textContent = state.selectedArticles.length;
  elements.selectedArticlesReview.innerHTML = state.selectedArticles.map((art, i) => `
    <div class="review-item">
      <div class="review-item-title">${i + 1}. ${escapeHtml(art.title)}</div>
      <div class="review-item-meta">${art.author_citation || 'Autor, Año'} · ${art.venue || 'Revista'}</div>
    </div>
  `).join("");
}

// ----------------- AI Matrix Extraction (Tab 2 -> Tab 3) -----------------
async function handleStartExtraction() {
  if (state.selectedArticles.length === 0) {
    showToast("Selecciona al menos un artículo para procesar.", "warning");
    return;
  }

  const topic = elements.tableTitleInput.value.trim() || state.currentTopic;
  const citationStyle = elements.citationStyleSelect.value;
  const model = elements.groqModelSelect.value;
  state.tableNumber = elements.tableNumberInput.value.trim() || "Tabla 4";
  state.tableTitle = elements.tableTitleInput.value.trim();
  state.journalHeader = elements.journalHeaderInput.value.trim() || "VISIÓN EMPRESARIAL";

  // Show progress
  elements.extractionProgressBox.style.display = "block";
  elements.btnStartExtraction.disabled = true;
  elements.progressBarFill.style.width = "5%";
  elements.progressPercent.textContent = "5%";
  elements.progressStatusText.textContent = "Iniciando análisis semántico con Groq AI...";

  state.extractedRows = [];
  const total = state.selectedArticles.length;

  for (let i = 0; i < total; i++) {
    const paper = state.selectedArticles[i];
    const currentPercent = Math.round(((i) / total) * 80) + 5;
    elements.progressBarFill.style.width = `${currentPercent}%`;
    elements.progressPercent.textContent = `${currentPercent}%`;
    elements.progressStatusText.textContent = `Extrayendo algoritmos de artículo ${i + 1} de ${total}: ${paper.author_citation || '...'}`;

    try {
      const res = await fetch("/api/extract-single", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          paper: paper,
          topic: topic,
          citation_style: citationStyle,
          api_key: state.groqApiKey || undefined,
          model: model
        })
      });

      if (res.ok) {
        const row = await res.json();
        state.extractedRows.push(row);
      }
    } catch (e) {
      console.warn(`Error extracting paper ${i}:`, e);
      // Fallback row
      state.extractedRows.push({
        id: paper.id,
        autor: paper.author_citation || "Autor et al.",
        tecnicas_algoritmos: "Algoritmos de clasificación supervisada",
        mejor_precision: "No especifica",
        hallazgos: "Estudio empírico.",
        cita_completa: `${paper.authors?.join(', ')} (${paper.year}). ${paper.title}.`,
        doi: paper.doi,
        title: paper.title,
        year: paper.year
      });
    }
  }

  // Generate Narrative Synthesis (Under Table, like Image 1)
  elements.progressBarFill.style.width = "90%";
  elements.progressPercent.textContent = "90%";
  elements.progressStatusText.textContent = "Redactando párrafo de síntesis científica comparativa...";

  try {
    const narRes = await fetch("/api/generate-narrative", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        table_rows: state.extractedRows,
        topic: topic,
        api_key: state.groqApiKey || undefined,
        model: model
      })
    });
    if (narRes.ok) {
      state.narrativeData = await narRes.json();
    }
  } catch (narErr) {
    console.warn("Narrative error:", narErr);
  }

  elements.progressBarFill.style.width = "100%";
  elements.progressPercent.textContent = "100%";
  elements.progressStatusText.textContent = "¡Extracción completada con éxito!";

  setTimeout(() => {
    elements.btnStartExtraction.disabled = false;
    elements.extractionProgressBox.style.display = "none";
    renderAcademicSheet();
    switchTab("tab-matrix");
    showToast("Matriz generada con éxito con formato idéntico a publicación científica.", "success");
  }, 600);
}

// ----------------- Render Tab 3 (Academic Journal Sheet) -----------------
function renderAcademicSheet() {
  elements.displayJournalHeader.textContent = state.journalHeader;
  elements.displayTableNumber.textContent = state.tableNumber;
  elements.displayTableTitle.textContent = state.tableTitle;

  // Build table rows (Matching Image 1)
  elements.academicTableBody.innerHTML = state.extractedRows.map((row, idx) => `
    <tr data-row-idx="${idx}">
      <td class="col-author" contenteditable="${state.isEditingCells}">${escapeHtml(row.autor || 'Autor')}</td>
      <td class="col-techs" contenteditable="${state.isEditingCells}">${escapeHtml(row.tecnicas_algoritmos || 'No especifica')}</td>
      <td class="col-best" contenteditable="${state.isEditingCells}">${escapeHtml(row.mejor_precision || 'No especifica')}</td>
    </tr>
  `).join("");

  // Narrative paragraph with bold lead
  const lead = state.narrativeData.lead_title || (state.narrativeData.dominant_technique ? `${state.narrativeData.dominant_technique}.` : "");
  let narrativeText = state.narrativeData.narrative || "";
  
  if (lead && narrativeText.startsWith(lead)) {
    const rest = narrativeText.slice(lead.length).trim();
    elements.narrativeParagraph.innerHTML = `<strong>${escapeHtml(lead)}</strong> ${escapeHtml(rest)}`;
  } else {
    elements.narrativeParagraph.textContent = narrativeText;
  }

  // Bibliographic References (APA 7 hanging indent)
  const citations = state.extractedRows
    .map(r => r.cita_completa)
    .filter(Boolean);

  elements.referencesList.innerHTML = citations.map(c => `
    <div class="reference-item" contenteditable="${state.isEditingCells}">
      ${makeHyperlinks(escapeHtml(c))}
    </div>
  `).join("");
}

function toggleEditMode() {
  state.isEditingCells = !state.isEditingCells;
  elements.btnToggleEditMode.classList.toggle("active", state.isEditingCells);
  elements.btnToggleEditMode.innerHTML = state.isEditingCells ? 
    `<span class="export-icon">💾</span><span>Guardar Edición</span>` : 
    `<span class="export-icon">✏️</span><span>Editar Celdas</span>`;

  document.querySelectorAll(".academic-table td, .reference-item, #narrativeParagraph, #displayJournalHeader, #displayTableNumber, #displayTableTitle").forEach(el => {
    el.setAttribute("contenteditable", state.isEditingCells);
  });

  if (!state.isEditingCells) {
    // Read back edited table rows
    const rows = [];
    document.querySelectorAll("#academicTableBody tr").forEach((tr, i) => {
      const tds = tr.querySelectorAll("td");
      if (tds.length >= 3 && state.extractedRows[i]) {
        state.extractedRows[i].autor = tds[0].innerText.trim();
        state.extractedRows[i].tecnicas_algoritmos = tds[1].innerText.trim();
        state.extractedRows[i].mejor_precision = tds[2].innerText.trim();
      }
    });
    state.journalHeader = elements.displayJournalHeader.innerText.trim();
    state.tableNumber = elements.displayTableNumber.innerText.trim();
    state.tableTitle = elements.displayTableTitle.innerText.trim();
    state.narrativeData.narrative = elements.narrativeParagraph.innerText.trim();
    showToast("Cambios guardados en la matriz.", "success");
  } else {
    showToast("Modo de edición activado. Puedes hacer clic en cualquier celda para modificar su texto.", "info");
  }
}

// ----------------- Export Functions -----------------
async function handleDownloadDocx() {
  if (state.extractedRows.length === 0) {
    showToast("No hay datos en la matriz para exportar.", "warning");
    return;
  }

  showToast("Generando documento Word (.docx) con normas académicas...", "info");

  const references = state.extractedRows.map(r => r.cita_completa).filter(Boolean);

  try {
    const res = await fetch("/api/export/docx", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        table_rows: state.extractedRows,
        table_number: state.tableNumber,
        table_title: state.tableTitle,
        narrative_text: elements.narrativeParagraph.innerText,
        lead_title: state.narrativeData.lead_title || "",
        references: references,
        journal_header: state.journalHeader
      })
    });

    if (!res.ok) throw new Error("Error al generar Word");

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Matriz_${state.tableNumber.replace(/\s+/g, '_')}_Academica.docx`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    showToast("Documento Word (.docx) descargado con éxito.", "success");
  } catch (e) {
    console.error(e);
    showToast("Error descargando archivo Word: " + e.message, "error");
  }
}

async function handleDownloadXlsx() {
  if (state.extractedRows.length === 0) {
    showToast("No hay datos en la matriz para exportar.", "warning");
    return;
  }

  showToast("Generando hoja de cálculo Excel (.xlsx)...", "info");

  try {
    const res = await fetch("/api/export/xlsx", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        table_rows: state.extractedRows,
        table_title: state.tableTitle,
        topic: state.currentTopic
      })
    });

    if (!res.ok) throw new Error("Error al generar Excel");

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Matriz_Literatura_Cientifica.xlsx`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    showToast("Archivo Excel (.xlsx) descargado con éxito.", "success");
  } catch (e) {
    console.error(e);
    showToast("Error descargando archivo Excel: " + e.message, "error");
  }
}

function handleCopyTable() {
  if (state.extractedRows.length === 0) {
    showToast("No hay datos para copiar.", "warning");
    return;
  }

  let md = `### ${state.tableNumber}: ${state.tableTitle}\n\n`;
  md += `| Autor | Técnicas/Algoritmos | Mejor precisión |\n`;
  md += `| :--- | :--- | :--- |\n`;

  state.extractedRows.forEach(r => {
    const techs = (r.tecnicas_algoritmos || '').replace(/\n/g, '<br>');
    md += `| ${r.autor || ''} | ${techs} | ${r.mejor_precision || ''} |\n`;
  });

  md += `\n${elements.narrativeParagraph.innerText}\n`;

  navigator.clipboard.writeText(md).then(() => {
    showToast("Tabla copiada al portapapeles en formato Markdown.", "success");
  }).catch(err => {
    showToast("No se pudo copiar: " + err, "error");
  });
}

// ----------------- Sample Data Loader (Image 1 replica) -----------------
async function loadSampleData() {
  showToast("Cargando ejemplo exacto de la Imagen 1...", "info");
  try {
    const res = await fetch("/api/sample-data");
    if (!res.ok) throw new Error("Error al obtener datos de ejemplo");
    const data = await res.json();

    state.currentTopic = data.topic;
    state.tableNumber = data.table_number;
    state.tableTitle = data.table_title;
    state.journalHeader = data.journal_header;
    state.extractedRows = data.rows;
    state.narrativeData = data.narrative;

    // Sync input fields
    elements.tableNumberInput.value = state.tableNumber;
    elements.tableTitleInput.value = state.tableTitle;
    elements.journalHeaderInput.value = state.journalHeader;
    elements.topicInput.value = "Técnicas y algoritmos utilizados en estudios sobre deserción universitaria";

    // Set count badge
    state.selectedArticles = data.rows.map(r => ({
      title: r.title,
      authors: [r.autor.split(',')[0]],
      year: r.year,
      author_citation: r.autor,
      venue: "Visión Empresarial",
      doi: r.doi,
      url: `https://doi.org/${r.doi}`
    }));
    elements.selectedBadge.textContent = state.selectedArticles.length;
    renderSelectedReviewList();

    // Render tab 3 and switch
    renderAcademicSheet();
    switchTab("tab-matrix");
    showToast("Datos de la Imagen 1 cargados con éxito.", "success");
  } catch (e) {
    showToast("Error cargando ejemplo: " + e.message, "error");
  }
}

// ----------------- Utilities -----------------
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function makeHyperlinks(text) {
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  return text.replace(urlRegex, url => `<a href="${url}" target="_blank" rel="noopener">${url}</a>`);
}
