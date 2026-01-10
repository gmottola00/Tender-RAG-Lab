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
  loadGraphEntities();
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

  // Refresh entities button
  const refreshEntitiesBtn = document.getElementById("refresh-entities-btn");
  if (refreshEntitiesBtn) {
    refreshEntitiesBtn.addEventListener("click", loadGraphEntities);
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
  const container = document.getElementById("documents-list");
  if (!container) return;

  try {
    const response = await fetch(`${apiBase}/tenders/${id}/documents`);
    if (!response.ok) throw new Error("Errore nel caricamento dei documenti");

    const documents = await response.json();
    renderDocuments(documents);

  } catch (error) {
    console.error("Errore:", error);
    container.innerHTML = `
      <li class="list-group-item">
        <div class="empty-state">
          <i class="bi bi-exclamation-triangle text-warning"></i>
          <h5>Errore nel caricamento</h5>
          <p>${escapeHtml(error.message)}</p>
        </div>
      </li>
    `;
  }
}

// Load graph entities from Neo4j
async function loadGraphEntities() {
  const id = getTenderId();
  const container = document.getElementById("graph-entities-container");
  if (!container) return;

  // Show loading
  container.innerHTML = `
    <div class="text-center py-5">
      <div class="spinner-border text-success" role="status">
        <span class="visually-hidden">Caricamento entità...</span>
      </div>
    </div>
  `;

  try {
    const response = await fetch(`${apiBase}/tenders/${id}/entities`);
    if (!response.ok) throw new Error("Errore nel caricamento delle entità");

    const data = await response.json();
    console.log('Neo4j entities received:', data);
    console.log('Entity keys:', Object.keys(data));
    
    // Log each entity type
    Object.entries(data).forEach(([key, value]) => {
      console.log(`${key}:`, value?.length || 0, 'items', value?.[0]);
    });
    
    renderGraphEntities(data);

  } catch (error) {
    console.error("Errore:", error);
    container.innerHTML = `
      <div class="empty-state p-4">
        <i class="bi bi-exclamation-triangle text-warning"></i>
        <h5>Errore nel caricamento</h5>
        <p class="text-muted mb-0">${escapeHtml(error.message)}</p>
      </div>
    `;
  }
}

// Render documents list
function renderDocuments(documents) {
  const container = document.getElementById("documents-list");
  if (!container) return;

  if (documents.length === 0) {
    container.innerHTML = `
      <li class="list-group-item">
        <div class="empty-state">
          <i class="bi bi-file-earmark-x"></i>
          <h5>Nessun documento</h5>
          <p>Carica il primo documento per questa gara</p>
        </div>
      </li>
    `;
    return;
  }

  const html = documents.map(doc => `
    <li class="list-group-item">
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
    </li>
  `).join('');

  container.innerHTML = html;
}

// Render graph entities from Neo4j
function renderGraphEntities(data) {
  const container = document.getElementById("graph-entities-container");
  if (!container) return;

  // Check if entities exist
  if (!data || Object.keys(data).length === 0) {
    container.innerHTML = `
      <div class="empty-state p-4">
        <i class="bi bi-diagram-3 text-muted"></i>
        <h5>Nessuna entità estratta</h5>
        <p class="text-muted mb-0">Carica e indicizza i documenti per estrarre entità nel grafo</p>
      </div>
    `;
    return;
  }

  // Map Neo4j keys to display labels (matching the actual API response)
  const entityTypes = [
    { key: 'organization', label: 'Organizzazioni', icon: 'building', color: 'primary' },
    { key: 'requirement', label: 'Requisiti', icon: 'list-check', color: 'info' },
    { key: 'date', label: 'Scadenze', icon: 'calendar-event', color: 'warning' },
    { key: 'lot', label: 'Lotti', icon: 'box', color: 'success' },
    { key: 'location', label: 'Luoghi', icon: 'geo-alt', color: 'danger' },
    { key: 'person', label: 'Persone', icon: 'person', color: 'secondary' },
    { key: 'cpv_code', label: 'Codici CPV', icon: 'tag', color: 'dark' },
    { key: 'amount', label: 'Importi', icon: 'cash-coin', color: 'success' },
  ];

  let html = '<div class="p-3">';
  let totalEntities = 0;

  entityTypes.forEach(type => {
    const entities = data[type.key] || [];
    
    // Filter out empty objects (objects with only null/undefined/empty values)
    const validEntities = entities.filter(entity => {
      if (!entity || typeof entity !== 'object') return false;
      
      // Check if at least one property has a meaningful value
      return Object.values(entity).some(val => {
        if (val === null || val === undefined || val === '') return false;
        if (typeof val === 'object' && Object.keys(val).length === 0) return false;
        return true;
      });
    });
    
    if (validEntities.length === 0) return;

    totalEntities += validEntities.length;

    html += `
      <div class="mb-4">
        <h6 class="text-${type.color} mb-3">
          <i class="bi bi-${type.icon} me-2"></i>
          ${type.label}
          <span class="badge bg-${type.color} ms-2">${validEntities.length}</span>
        </h6>
        <div class="entity-list">
    `;

    validEntities.forEach(entity => {
      html += renderEntityItem(entity, type);
    });

    html += `
        </div>
      </div>
    `;
  });

  if (totalEntities === 0) {
    container.innerHTML = `
      <div class="empty-state p-4">
        <i class="bi bi-diagram-3 text-muted"></i>
        <h5>Nessuna entità estratta</h5>
        <p class="text-muted mb-0">Carica e indicizza i documenti per estrarre entità nel grafo</p>
      </div>
    `;
    return;
  }

  html += '</div>';
  container.innerHTML = html;
}

// Render individual entity item
function renderEntityItem(entity, type) {
  let content = '';

  // Different rendering based on entity type
  switch (type.key) {
    case 'organization':
      content = `
        <div class="entity-item">
          <div class="d-flex align-items-start gap-2">
            <i class="bi bi-${type.icon} text-${type.color}"></i>
            <div class="flex-grow-1">
              <div class="fw-semibold">${escapeHtml(entity.name || 'N/D')}</div>
              ${entity.type ? `<div class="small text-muted">Tipo: ${escapeHtml(entity.type)}</div>` : ''}
              ${entity.role ? `<div class="small text-muted">Ruolo: ${escapeHtml(entity.role)}</div>` : ''}
            </div>
          </div>
        </div>
      `;
      break;

    case 'requirement':
      const reqText = entity.description || entity.requirement_text || entity.text || 'N/D';
      const reqType = entity.type || entity.category;
      const isMandatory = entity.mandatory;
      
      content = `
        <div class="entity-item">
          <div class="d-flex align-items-start gap-2">
            <i class="bi bi-${type.icon} text-${type.color}"></i>
            <div class="flex-grow-1">
              <div class="fw-semibold">${escapeHtml(reqText)}</div>
              <div class="d-flex gap-2 mt-1">
                ${reqType ? `<span class="badge bg-${type.color}">${escapeHtml(reqType)}</span>` : ''}
                ${isMandatory ? `<span class="badge bg-danger">Obbligatorio</span>` : ''}
              </div>
            </div>
          </div>
        </div>
      `;
      break;

    case 'date':
      const dateType = entity.type || entity.deadline_type || 'Scadenza';
      const dateValue = entity.date || entity.date_text;
      
      content = `
        <div class="entity-item">
          <div class="d-flex align-items-start gap-2">
            <i class="bi bi-${type.icon} text-${type.color}"></i>
            <div class="flex-grow-1">
              <div class="fw-semibold">${escapeHtml(dateType)}</div>
              ${dateValue ? `<div class="small text-muted"><i class="bi bi-calendar3 me-1"></i>${escapeHtml(dateValue)}</div>` : ''}
              ${entity.description ? `<div class="small text-muted">${escapeHtml(entity.description)}</div>` : ''}
            </div>
          </div>
        </div>
      `;
      break;

    case 'lot':
      const lotName = entity.name || entity.title;
      const lotNumber = entity.lot_number || entity.number;
      const lotAmount = entity.base_amount || entity.amount;
      
      content = `
        <div class="entity-item">
          <div class="d-flex align-items-start gap-2">
            <i class="bi bi-${type.icon} text-${type.color}"></i>
            <div class="flex-grow-1">
              <div class="fw-semibold">${lotName ? escapeHtml(lotName) : (lotNumber ? `Lotto ${escapeHtml(lotNumber)}` : 'Lotto N/D')}</div>
              ${entity.cpv_code ? `<div class="small text-muted">CPV: ${escapeHtml(entity.cpv_code)}</div>` : ''}
              ${lotAmount ? `<div class="small text-muted">Importo: €${escapeHtml(lotAmount)}</div>` : ''}
            </div>
          </div>
        </div>
      `;
      break;

    case 'location':
      const locationName = entity.name || entity.location;
      const locationType = entity.type;
      const locationAddress = entity.address;
      
      content = `
        <div class="entity-item">
          <div class="d-flex align-items-start gap-2">
            <i class="bi bi-${type.icon} text-${type.color}"></i>
            <div class="flex-grow-1">
              <div class="fw-semibold">${escapeHtml(locationName || 'N/D')}</div>
              ${locationAddress ? `<div class="small text-muted">${escapeHtml(locationAddress)}</div>` : ''}
              ${locationType ? `<div class="small text-muted">${escapeHtml(locationType)}</div>` : ''}
            </div>
          </div>
        </div>
      `;
      break;

    case 'person':
      content = `
        <div class="entity-item">
          <div class="d-flex align-items-start gap-2">
            <i class="bi bi-${type.icon} text-${type.color}"></i>
            <div class="flex-grow-1">
              <div class="fw-semibold">${escapeHtml(entity.name || 'N/D')}</div>
              ${entity.role ? `<div class="small text-muted">${escapeHtml(entity.role)}</div>` : ''}
            </div>
          </div>
        </div>
      `;
      break;

    case 'cpv_code':
      content = `
        <div class="entity-item">
          <div class="d-flex align-items-start gap-2">
            <i class="bi bi-${type.icon} text-${type.color}"></i>
            <div class="flex-grow-1">
              <div class="fw-semibold font-monospace">${escapeHtml(entity.code || 'N/D')}</div>
              ${entity.description ? `<div class="small text-muted">${escapeHtml(entity.description)}</div>` : ''}
            </div>
          </div>
        </div>
      `;
      break;

    case 'amount':
      content = `
        <div class="entity-item">
          <div class="d-flex align-items-start gap-2">
            <i class="bi bi-${type.icon} text-${type.color}"></i>
            <div class="flex-grow-1">
              <div class="fw-semibold">€ ${escapeHtml(entity.value || entity.amount || 'N/D')}</div>
              ${entity.currency ? `<div class="small text-muted">${escapeHtml(entity.currency)}</div>` : ''}
              ${entity.type ? `<div class="small text-muted">${escapeHtml(entity.type)}</div>` : ''}
            </div>
          </div>
        </div>
      `;
      break;

    default:
      content = `
        <div class="entity-item">
          <div class="small">${escapeHtml(JSON.stringify(entity))}</div>
        </div>
      `;
  }

  return content;
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

  .entity-item {
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    background: #f8fafc;
    border-radius: 8px;
    border-left: 3px solid var(--bs-primary);
    transition: all 0.2s ease;
  }

  .entity-item:hover {
    background: #f1f5f9;
    transform: translateX(2px);
  }

  .entity-list {
    display: flex;
    flex-direction: column;
  }

  .empty-state {
    padding: 3rem 2rem;
    text-align: center;
    color: #64748b;
  }

  .empty-state i {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.5;
  }

  .empty-state h5 {
    color: #475569;
    margin-bottom: 0.5rem;
  }
`;
document.head.appendChild(style);
