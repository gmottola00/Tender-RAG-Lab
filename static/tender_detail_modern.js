// Modern Tender Detail JavaScript
const apiBase = "/api";

// Get tender ID from URL
function getTenderId() {
  const params = new URLSearchParams(window.location.search);
  return params.get("id");
}

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  const tenderId = getTenderId();
  if (!tenderId) {
    showError("ID gara non fornito");
    return;
  }

  loadTender();
  loadDocuments();
  setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
  // Tender form submission
  const tenderForm = document.getElementById("tender-detail-form");
  if (tenderForm) {
    tenderForm.addEventListener("submit", handleUpdateTender);
  }

  // Document form submission
  const documentForm = document.getElementById("document-form");
  if (documentForm) {
    documentForm.addEventListener("submit", handleCreateDocument);
  }

  // Delete tender button
  const deleteBtn = document.getElementById("delete-tender-btn");
  if (deleteBtn) {
    deleteBtn.addEventListener("click", handleDeleteTender);
  }

  // Ingest all button
  const ingestBtn = document.getElementById("ingest-all-btn");
  if (ingestBtn) {
    ingestBtn.addEventListener("click", handleIngestAll);
  }

  // File dropzone
  setupDropzone();
}

// Load tender data
async function loadTender() {
  const id = getTenderId();
  try {
    const response = await fetch(`${apiBase}/tenders/${id}`);
    if (!response.ok) throw new Error("Errore nel caricamento della gara");

    const tender = await response.json();
    fillTenderForm(tender);
    updatePageTitle(tender);

    // Set hidden tender_id
    const hiddenInput = document.getElementById("doc-tender-id");
    if (hiddenInput) hiddenInput.value = tender.id;

  } catch (error) {
    console.error("Errore:", error);
    showError("Impossibile caricare i dati della gara");
  }
}

// Fill tender form with data
function fillTenderForm(tender) {
  const form = document.getElementById("tender-detail-form");
  if (!form) return;

  form.code.value = tender.code || "";
  form.title.value = tender.title || "";
  form.description.value = tender.description || "";
  form.buyer.value = tender.buyer || "";
  form.status.value = tender.status || "";
  form.publish_date.value = tender.publish_date || "";
  form.closing_date.value = tender.closing_date || "";
}

// Update page title
function updatePageTitle(tender) {
  const titleEl = document.getElementById("page-title");
  if (titleEl) {
    titleEl.innerHTML = `
      <span class="text-muted">${escapeHtml(tender.code)}</span>
      ${escapeHtml(tender.title)}
    `;
  }
}

// Handle tender update
async function handleUpdateTender(e) {
  e.preventDefault();

  const id = getTenderId();
  const form = e.target;
  const submitBtn = form.querySelector('button[type="submit"]');
  const messageEl = document.getElementById("detail-message");

  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Salvataggio...';

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
    const response = await fetch(`${apiBase}/tenders/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || "Errore nell'aggiornamento");
    }

    const updated = await response.json();
    showSuccess(messageEl, "Gara aggiornata con successo!");
    fillTenderForm(updated);
    updatePageTitle(updated);

  } catch (error) {
    showError(messageEl, error.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="bi bi-check-lg me-2"></i>Salva modifiche';
  }
}

// Load documents
async function loadDocuments() {
  const id = getTenderId();
  const container = document.getElementById("documents-list-container");
  if (!container) return;

  try {
    const response = await fetch(`${apiBase}/tenders/${id}/documents`);
    if (!response.ok) throw new Error("Errore nel caricamento dei documenti");

    const documents = await response.json();
    renderDocuments(documents);

  } catch (error) {
    console.error("Errore:", error);
    container.innerHTML = `
      <div class="empty-state">
        <i class="bi bi-exclamation-triangle text-warning"></i>
        <h5>Errore nel caricamento</h5>
        <p>${escapeHtml(error.message)}</p>
      </div>
    `;
  }
}

// Render documents list
function renderDocuments(documents) {
  const container = document.getElementById("documents-list-container");
  if (!container) return;

  if (documents.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <i class="bi bi-file-earmark-x"></i>
        <h5>Nessun documento</h5>
        <p>Carica il primo documento per questa gara</p>
      </div>
    `;
    return;
  }

  const html = documents.map(doc => `
    <div class="document-item">
      <div class="d-flex align-items-start gap-3">
        <div class="doc-icon">
          <i class="bi bi-file-earmark-pdf text-danger"></i>
        </div>
        <div class="flex-grow-1">
          <h6 class="mb-1">${escapeHtml(doc.filename || 'Documento')}</h6>
          <div class="d-flex flex-wrap gap-2 mb-2">
            <span class="badge bg-primary">${escapeHtml(doc.document_type || 'N/D')}</span>
            ${doc.ingestion_status ? `<span class="badge bg-success">Indicizzato</span>` : ''}
          </div>
          <div class="small text-muted">
            <i class="bi bi-calendar me-1"></i>
            ${formatDate(doc.created_at)}
            ${doc.uploaded_by ? ` • <i class="bi bi-person me-1"></i>${escapeHtml(doc.uploaded_by)}` : ''}
          </div>
        </div>
        <div class="btn-group">
          <button class="btn btn-sm btn-outline-primary" onclick="handleIngestDocument('${doc.id}')">
            <i class="bi bi-lightning-charge"></i>
          </button>
          <button class="btn btn-sm btn-outline-danger" onclick="handleDeleteDocument('${doc.id}')">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      </div>
    </div>
  `).join('');

  container.innerHTML = html;
}

// Handle document creation
async function handleCreateDocument(e) {
  e.preventDefault();

  const form = e.target;
  const submitBtn = form.querySelector('button[type="submit"]');
  const messageEl = document.getElementById("document-message");
  const fileInput = document.getElementById("doc-file-input");

  if (!fileInput.files || fileInput.files.length === 0) {
    showError(messageEl, "Seleziona un file");
    return;
  }

  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Upload...';

  const formData = new FormData();
  formData.append("tender_id", getTenderId());
  formData.append("document_type", form.document_type.value);
  formData.append("file", fileInput.files[0]);

  if (form.lot_id.value) formData.append("lot_id", form.lot_id.value);
  if (form.uploaded_by.value) formData.append("uploaded_by", form.uploaded_by.value);
  if (form.file_hash.value) formData.append("file_hash", form.file_hash.value);

  try {
    const response = await fetch(`${apiBase}/documents`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || "Errore nel caricamento");
    }

    const data = await response.json();
    showSuccess(messageEl, `Documento caricato con successo! ID: ${data.id}`);
    form.reset();
    document.getElementById("filename-input").value = "";

    // Reload documents
    setTimeout(() => loadDocuments(), 1000);

  } catch (error) {
    showError(messageEl, error.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="bi bi-upload me-2"></i>Carica documento';
  }
}

// Setup file dropzone
function setupDropzone() {
  const dropzone = document.getElementById("doc-dropzone");
  const fileInput = document.getElementById("doc-file-input");
  const filenameInput = document.getElementById("filename-input");

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener("click", () => fileInput.click());

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      fileInput.files = e.dataTransfer.files;
      filenameInput.value = e.dataTransfer.files[0].name;
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      filenameInput.value = e.target.files[0].name;
    }
  });
}

// Handle ingest single document
async function handleIngestDocument(docId) {
  const messageEl = document.getElementById("documents-message");

  try {
    const response = await fetch(`${apiBase}/documents/${docId}/ingest`, {
      method: "POST",
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || "Errore nell'indicizzazione");
    }

    showSuccess(messageEl, "Documento indicizzato con successo!");
    setTimeout(() => loadDocuments(), 1000);

  } catch (error) {
    showError(messageEl, error.message);
  }
}

// Handle ingest all documents
async function handleIngestAll() {
  const tenderId = getTenderId();
  const messageEl = document.getElementById("documents-message");
  const btn = document.getElementById("ingest-all-btn");

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Indicizzazione...';

  try {
    const response = await fetch(`${apiBase}/tenders/${tenderId}/ingest-all`, {
      method: "POST",
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || "Errore nell'indicizzazione");
    }

    showSuccess(messageEl, "Tutti i documenti sono stati indicizzati!");
    setTimeout(() => loadDocuments(), 1000);

  } catch (error) {
    showError(messageEl, error.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-lightning-charge me-1"></i>Indicizza tutti';
  }
}

// Handle delete document
async function handleDeleteDocument(docId) {
  if (!confirm("Sei sicuro di voler eliminare questo documento?")) return;

  const messageEl = document.getElementById("documents-message");

  try {
    const response = await fetch(`${apiBase}/documents/${docId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || "Errore nell'eliminazione");
    }

    showSuccess(messageEl, "Documento eliminato");
    setTimeout(() => loadDocuments(), 500);

  } catch (error) {
    showError(messageEl, error.message);
  }
}

// Handle delete tender
async function handleDeleteTender() {
  if (!confirm("Sei sicuro di voler eliminare questa gara? L'azione è irreversibile.")) return;

  const tenderId = getTenderId();

  try {
    const response = await fetch(`${apiBase}/tenders/${tenderId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || "Errore nell'eliminazione");
    }

    alert("Gara eliminata con successo!");
    window.location.href = "/demo";

  } catch (error) {
    alert("Errore: " + error.message);
  }
}

// Utility functions
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function formatDate(dateString) {
  if (!dateString) return 'N/D';
  const date = new Date(dateString);
  return date.toLocaleDateString('it-IT', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function showSuccess(element, message) {
  element.innerHTML = `
    <div class="alert alert-success alert-custom">
      <i class="bi bi-check-circle-fill"></i>
      <span>${message}</span>
    </div>
  `;
  setTimeout(() => element.innerHTML = '', 5000);
}

function showError(elementOrMessage, message) {
  if (typeof elementOrMessage === 'string') {
    alert('Errore: ' + elementOrMessage);
  } else {
    elementOrMessage.innerHTML = `
      <div class="alert alert-danger alert-custom">
        <i class="bi bi-exclamation-triangle-fill"></i>
        <span>${message}</span>
      </div>
    `;
    setTimeout(() => elementOrMessage.innerHTML = '', 5000);
  }
}

// Add document item styling
const style = document.createElement('style');
style.textContent = `
  .document-item {
    padding: 1.5rem;
    border-bottom: 1px solid var(--border, #e2e8f0);
    transition: all 0.2s ease;
  }

  .document-item:hover {
    background: #f8fafc;
  }

  .document-item:last-child {
    border-bottom: none;
  }

  .doc-icon {
    font-size: 2rem;
    width: 60px;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #fee2e2;
    border-radius: 12px;
  }
`;
document.head.appendChild(style);
