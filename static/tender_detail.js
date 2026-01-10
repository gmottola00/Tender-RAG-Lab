const apiBase = "/api";

function getTenderId() {
  const params = new URLSearchParams(window.location.search);
  return params.get("id");
}

async function fetchJSON(url, options = {}) {
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || resp.statusText);
  }
  return resp.json();
}

function fillMeta(tender) {
  const metaId = document.getElementById("meta-id");
  const metaCreated = document.getElementById("meta-created");
  const metaUpdated = document.getElementById("meta-updated");
  if (metaId) metaId.textContent = tender.id;
  if (metaCreated) metaCreated.textContent = tender.created_at || "";
  if (metaUpdated) metaUpdated.textContent = tender.updated_at || "";
  const hiddenTenderId = document.getElementById("doc-tender-id");
  if (hiddenTenderId) {
    hiddenTenderId.value = tender.id;
  }
}

function fillForm(tender) {
  const form = document.getElementById("tender-detail-form");
  form.code.value = tender.code ?? "";
  form.title.value = tender.title ?? "";
  form.description.value = tender.description ?? "";
  form.buyer.value = tender.buyer ?? "";
  form.status.value = tender.status ?? "";
  form.publish_date.value = tender.publish_date ?? "";
  form.closing_date.value = tender.closing_date ?? "";
}

async function loadTender() {
  const id = getTenderId();
  if (!id) {
    showMessage("detail-message", "Nessun id fornito", "danger");
    return;
  }
  try {
    const tender = await fetchJSON(`${apiBase}/tenders/${id}`);
    fillForm(tender);
    fillMeta(tender);
    updatePageTitle(tender);
  } catch (err) {
    showMessage("detail-message", `Errore: ${err.message}`, "danger");
  }
}

function updatePageTitle(tender) {
  const pageTitle = document.getElementById("page-title");
  if (pageTitle && tender.title) {
    pageTitle.textContent = tender.title;
  }
}

async function handleUpdate(e) {
  e.preventDefault();
  const id = getTenderId();
  if (!id) return;
  const form = e.target;
  const payload = {
    code: form.code.value || null,
    title: form.title.value || null,
    description: form.description.value || null,
    buyer: form.buyer.value || null,
    status: form.status.value || null,
    publish_date: form.publish_date.value || null,
    closing_date: form.closing_date.value || null,
  };
  try {
    const updated = await fetchJSON(`${apiBase}/tenders/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    showMessage("detail-message", "Modifiche salvate con successo!", "success");
    fillForm(updated);
    fillMeta(updated);
    updatePageTitle(updated);
  } catch (err) {
    showMessage("detail-message", `Errore: ${err.message}`, "danger");
  }
}

async function handleCreateDocument(e) {
  e.preventDefault();
  const form = e.target;
  const tenderId = getTenderId();
  if (!tenderId) {
    showMessage("document-message", "ID gara mancante", "danger");
    return;
  }
  const fd = new FormData();
  fd.append("tender_id", tenderId);
  if (form.lot_id.value) fd.append("lot_id", form.lot_id.value);
  fd.append("document_type", form.document_type.value || "");

  const fileInput = document.getElementById("doc-file-input");
  const file = fileInput?.files?.[0];
  if (!file) {
    showMessage("document-message", "Seleziona un file", "warning");
    return;
  }
  fd.append("file", file);

  try {
    const url = `${apiBase}/documents`;
    console.log("POST document ->", url, fd);
    const resp = await fetch(url, { method: "POST", body: fd });
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(text || resp.statusText);
    }
    const data = await resp.json();
    showMessage("document-message", `Documento caricato con successo! ID: ${data.id}`, "success");
    form.reset();
    if (fileInput) fileInput.value = "";
    document.getElementById("filename-input").value = "";
    const dz = document.getElementById("doc-dropzone");
    if (dz) {
      const p = dz.querySelector("p");
      if (p) p.textContent = "Trascina un file qui oppure clicca per selezionarlo";
    }
    loadDocuments();
  } catch (err) {
    showMessage("document-message", `Errore: ${err.message}`, "danger");
  }
}

function setupDropzone() {
  const dropzone = document.getElementById("doc-dropzone");
  const fileInput = document.getElementById("doc-file-input");
  const filenameInput = document.getElementById("filename-input");
  if (!dropzone || !fileInput || !filenameInput) return;
  console.log("Inizializzo dropzone (detail)");

  const setFilename = (file) => {
    if (file) {
      filenameInput.value = file.name;
      dropzone.querySelector("p").textContent = `File selezionato: ${file.name}`;
    } else {
      filenameInput.value = "";
      dropzone.querySelector("p").textContent = "Trascina un file qui oppure clicca per selezionarlo";
    }
  };

  dropzone.addEventListener("click", () => {
    console.log("Dropzone click -> open file dialog");
    fileInput.click();
  });
  dropzone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      fileInput.click();
    }
  });
  fileInput.addEventListener("change", (e) => {
    const file = e.target.files?.[0];
    setFilename(file);
  });

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    const file = e.dataTransfer?.files?.[0];
    if (file) {
      setFilename(file);
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("tender-detail-form").addEventListener("submit", handleUpdate);
  document.getElementById("document-form")?.addEventListener("submit", handleCreateDocument);
  setupDropzone();
  loadTender();
  loadDocuments();
  loadGraphEntities();
  const ingestAllBtn = document.getElementById("ingest-all-btn");
  if (ingestAllBtn) {
    ingestAllBtn.addEventListener("click", ingestAllDocuments);
  }
  const refreshEntitiesBtn = document.getElementById("refresh-entities-btn");
  if (refreshEntitiesBtn) {
    refreshEntitiesBtn.addEventListener("click", loadGraphEntities);
  }
  const deleteTenderBtn = document.getElementById("delete-tender-btn");
  if (deleteTenderBtn) {
    deleteTenderBtn.addEventListener("click", handleDeleteTender);
  }
});

async function loadDocuments() {
  const listEl = document.getElementById("documents-list");
  if (!listEl) return;
  const tenderId = getTenderId();
  if (!tenderId) return;

  listEl.innerHTML = '<li class="list-group-item text-center py-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Caricamento...</span></div></li>';

  try {
    const docs = await fetchJSON(`${apiBase}/documents?tender_id=${tenderId}&limit=200`);

    if (docs.length === 0) {
      listEl.innerHTML = `
        <li class="list-group-item text-center py-5">
          <i class="bi bi-folder-x text-muted fs-1 mb-3 d-block"></i>
          <p class="text-muted mb-0">Nessun documento caricato</p>
        </li>
      `;
      return;
    }

    listEl.innerHTML = "";
    docs.forEach((d) => {
      const li = document.createElement("li");
      li.className = "list-group-item d-flex justify-content-between align-items-center";

      const docTypeIcon = getDocumentIcon(d.document_type);
      const docTypeLabel = getDocumentTypeLabel(d.document_type);

      li.innerHTML = `
        <div class="d-flex align-items-center gap-3 flex-grow-1">
          <div class="doc-icon">
            <i class="bi bi-${docTypeIcon} fs-4 text-primary"></i>
          </div>
          <div>
            <div class="fw-semibold">${escapeHtml(d.filename)}</div>
            <div class="small text-muted">
              <span class="badge bg-secondary-subtle text-secondary">${docTypeLabel}</span>
              <span class="ms-2">ID: ${d.id}</span>
            </div>
          </div>
        </div>
        <button class="btn btn-sm btn-primary" data-doc-id="${d.id}">
          <i class="bi bi-lightning-charge me-1"></i>Indicizza
        </button>
      `;

      const btn = li.querySelector("button");
      btn.addEventListener("click", () => ingestDocument(d.id));
      listEl.appendChild(li);
    });
  } catch (err) {
    listEl.innerHTML = `
      <li class="list-group-item">
        <div class="alert alert-danger mb-0">
          <i class="bi bi-exclamation-triangle me-2"></i>
          Errore caricamento documenti: ${err.message}
        </div>
      </li>
    `;
  }
}

function getDocumentIcon(type) {
  const icons = {
    bando: 'file-earmark-text',
    capitolato: 'file-earmark-ruled',
    disciplinare: 'file-earmark-check',
    rettifica: 'file-earmark-diff',
    avviso: 'megaphone',
    chiarimenti: 'question-circle',
    qa: 'chat-left-text',
    altro: 'file-earmark'
  };
  return icons[type] || 'file-earmark-pdf';
}

function getDocumentTypeLabel(type) {
  const labels = {
    bando: 'Bando',
    capitolato: 'Capitolato',
    disciplinare: 'Disciplinare',
    rettifica: 'Rettifica',
    avviso: 'Avviso',
    chiarimenti: 'Chiarimenti',
    qa: 'Q&A',
    altro: 'Altro'
  };
  return labels[type] || type || 'N/D';
}

async function ingestDocument(documentId) {
  try {
    const resp = await fetchJSON(`${apiBase}/documents/${documentId}/ingest`, { method: "POST" });
    showMessage("documents-message", `Documento indicizzato con successo! Chunks inseriti: ${resp.inserted}`, "success");
  } catch (err) {
    showMessage("documents-message", `Errore indicizzazione: ${err.message}`, "danger");
  }
}

function showMessage(elementId, message, type = "info") {
  const element = document.getElementById(elementId);
  if (!element) return;

  const iconMap = {
    success: "check-circle-fill",
    danger: "exclamation-triangle-fill",
    warning: "exclamation-circle-fill",
    info: "info-circle-fill"
  };

  element.innerHTML = `
    <div class="alert alert-${type} alert-dismissible fade show" role="alert">
      <i class="bi bi-${iconMap[type]} me-2"></i>
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>
  `;

  setTimeout(() => {
    const alert = element.querySelector('.alert');
    if (alert) {
      alert.classList.remove('show');
      setTimeout(() => element.innerHTML = '', 150);
    }
  }, 5000);
}

async function ingestAllDocuments() {
  const tenderId = getTenderId();
  if (!tenderId) return;
  document.getElementById("documents-message").textContent = "Indicizzazione in corso...";
  const docs = await fetchJSON(`${apiBase}/documents?tender_id=${tenderId}&limit=200`);
  for (const d of docs) {
    try {
      await ingestDocument(d.id);
    } catch (err) {
      // swallow per non fermare gli altri
      console.error("Errore indicizzazione doc", d.id, err);
    }
  }
}

async function loadGraphEntities() {
  const container = document.getElementById("graph-entities-container");
  if (!container) return;

  const tenderId = getTenderId();
  if (!tenderId) {
    container.innerHTML = '<div class="p-4 text-center text-muted">ID gara mancante</div>';
    return;
  }

  container.innerHTML = `
    <div class="text-center py-5">
      <div class="spinner-border text-success" role="status">
        <span class="visually-hidden">Caricamento entità...</span>
      </div>
    </div>
  `;

  try {
    const response = await fetch(`${apiBase}/tenders/${tenderId}/entities`);
    if (!response.ok) {
      throw new Error("Impossibile recuperare le entità dal grafo");
    }
    const entities = await response.json();
    renderGraphEntities(entities);
  } catch (err) {
    container.innerHTML = `
      <div class="p-4">
        <div class="alert alert-warning mb-0">
          <i class="bi bi-exclamation-triangle me-2"></i>
          ${err.message}
        </div>
      </div>
    `;
  }
}

function renderGraphEntities(entities) {
  const container = document.getElementById("graph-entities-container");
  if (!container) return;

  if (!entities || Object.keys(entities).length === 0) {
    container.innerHTML = `
      <div class="p-4 text-center">
        <i class="bi bi-diagram-3 text-muted fs-1 mb-3 d-block"></i>
        <p class="text-muted mb-0">Nessuna entità estratta dal grafo</p>
      </div>
    `;
    return;
  }

  const entityTypeConfig = {
    organization: { icon: 'building', color: 'primary', label: 'Organizzazioni' },
    person: { icon: 'person', color: 'info', label: 'Persone' },
    location: { icon: 'geo-alt', color: 'warning', label: 'Luoghi' },
    requirement: { icon: 'clipboard-check', color: 'success', label: 'Requisiti' },
    date: { icon: 'calendar-event', color: 'danger', label: 'Date' },
    amount: { icon: 'cash', color: 'secondary', label: 'Importi' },
    cpv_code: { icon: 'tag', color: 'dark', label: 'Codici CPV' }
  };

  let html = '<div class="p-4">';

  Object.entries(entities).forEach(([type, items]) => {
    if (!items || items.length === 0) return;

    const config = entityTypeConfig[type] || { icon: 'circle', color: 'secondary', label: type };

    html += `
      <div class="entity-group mb-4">
        <h6 class="entity-group-header text-${config.color} mb-3">
          <i class="bi bi-${config.icon} me-2"></i>
          ${config.label} <span class="badge bg-${config.color} ms-2">${items.length}</span>
        </h6>
        <div class="entity-list">
    `;

    items.forEach(entity => {
      const name = entity.name || entity.value || entity.text || 'N/D';
      const properties = entity.properties || {};
      const propsHtml = Object.entries(properties)
        .map(([key, value]) => `<small class="text-muted">${key}: ${value}</small>`)
        .join(' · ');

      html += `
        <div class="entity-badge bg-${config.color}-subtle">
          <i class="bi bi-${config.icon} text-${config.color} me-2"></i>
          <div class="entity-content">
            <span class="entity-name">${escapeHtml(name)}</span>
            ${propsHtml ? `<div class="entity-props">${propsHtml}</div>` : ''}
          </div>
        </div>
      `;
    });

    html += `
        </div>
      </div>
    `;
  });

  html += '</div>';
  container.innerHTML = html;
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

async function handleDeleteTender() {
  const tenderId = getTenderId();
  if (!tenderId) return;

  if (!confirm('Sei sicuro di voler eliminare questa gara? Questa azione non può essere annullata.')) {
    return;
  }

  try {
    await fetchJSON(`${apiBase}/tenders/${tenderId}`, { method: 'DELETE' });
    window.location.href = '/demo';
  } catch (err) {
    alert(`Errore durante l'eliminazione: ${err.message}`);
  }
}
