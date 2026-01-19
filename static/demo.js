// Demo Dashboard JavaScript
const apiBase = "/api";

// Global state
let allTenders = [];
let currentSection = 'dashboard';
let uploadedFiles = [];

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  initializeDashboard();
  setupEventListeners();
  loadTenders();
});

// Initialize dashboard
function initializeDashboard() {
  // Set initial active section
  showSection('dashboard');
}

// Setup all event listeners
function setupEventListeners() {
  // Navigation
  document.querySelectorAll('[data-section]').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const section = link.dataset.section;
      showSection(section);

      // Update active state in navbar
      document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
      link.classList.add('active');
    });
  });

  // Search
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.addEventListener('input', handleSearch);
  }

  // Create section upload
  setupCreateUpload();
}

// Delete all tenders
async function deleteAllTenders() {
  if (!confirm('Sei sicuro di voler eliminare TUTTE le gare? Questa operazione non può essere annullata.')) {
    return;
  }

  try {
    const response = await fetch(`${apiBase}/tenders`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      throw new Error('Errore nell\'eliminazione delle gare');
    }

    const data = await response.json();
    showToast(`${data.deleted_count} gara/e eliminate con successo`, 'success');
    
    // Reload tenders list
    await loadTenders();

  } catch (error) {
    console.error('Errore:', error);
    showToast('Errore nell\'eliminazione delle gare', 'danger');
  }
}

// Show section
function showSection(sectionName) {
  currentSection = sectionName;
  document.querySelectorAll('.content-section').forEach(section => {
    section.classList.remove('active');
  });

  const targetSection = document.getElementById(`${sectionName}-section`);
  if (targetSection) {
    targetSection.classList.add('active');
  }
}

// Load tenders from API
async function loadTenders() {
  try {
    const response = await fetch(`${apiBase}/tenders?limit=100`);
    if (!response.ok) throw new Error('Errore nel caricamento delle gare');

    allTenders = await response.json();
    renderTenderList(allTenders);
    updateStats(allTenders);
  } catch (error) {
    console.error('Errore:', error);
    showError('Impossibile caricare le gare');
  }
}

// Render tender list
function renderTenderList(tenders) {
  const container = document.getElementById('tender-list-container');
  if (!container) return;

  if (tenders.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <i class="bi bi-folder-x"></i>
        <h5>Nessuna gara trovata</h5>
        <p>Crea la tua prima gara per iniziare</p>
        <button class="btn btn-primary btn-lg mt-4 px-5 rounded-pill fw-semibold shadow" onclick="showSection('create')">
          <i class="bi bi-plus-lg me-2"></i>Crea Prima Gara
        </button>
      </div>
    `;
    return;
  }

  const html = tenders.map(tender => `
    <a href="/tender-detail?id=${tender.id}" class="tender-item">
      <div class="tender-code">
        <i class="bi bi-file-earmark-text me-2"></i>
        ${escapeHtml(tender.code)}
      </div>
      <div class="tender-title">${escapeHtml(tender.title)}</div>
      <span class="tender-status status-${tender.status || 'draft'}">
        ${tender.status || 'bozza'}
      </span>
      <div class="tender-date">
        <i class="bi bi-calendar-event me-1"></i>
        ${formatDate(tender.publish_date || tender.created_at)}
      </div>
    </a>
  `).join('');

  container.innerHTML = html;

  // Add animation
  container.querySelectorAll('.tender-item').forEach((item, index) => {
    item.style.animation = `fadeIn 0.3s ease-out ${index * 0.05}s both`;
  });
}

// Update stats
function updateStats(tenders) {
  const totalElement = document.getElementById('total-tenders');
  const activeElement = document.getElementById('active-tenders');

  if (totalElement) {
    animateCounter(totalElement, tenders.length);
  }

  if (activeElement) {
    const activeCount = tenders.filter(t => t.status === 'active').length;
    animateCounter(activeElement, activeCount);
  }
}

// Animate counter
function animateCounter(element, endValue) {
  const startValue = parseInt(element.textContent) || 0;
  const duration = 1000;
  const startTime = performance.now();

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const current = Math.floor(startValue + (endValue - startValue) * progress);

    element.textContent = current;

    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }

  requestAnimationFrame(update);
}

// Setup create upload dropzone
function setupCreateUpload() {
  const dropzone = document.getElementById('create-dropzone');
  const fileInput = document.getElementById('create-file-input');
  const extractBtn = document.getElementById('extract-btn');
  const resetBtn = document.getElementById('reset-upload-btn');

  if (!dropzone || !fileInput) return;

  // Dropzone click
  dropzone.addEventListener('click', () => fileInput.click());

  // Dropzone drag events
  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFilesSelected(Array.from(e.dataTransfer.files));
    }
  });

  // File input change
  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFilesSelected(Array.from(e.target.files));
    }
  });

  // Extract button
  extractBtn.addEventListener('click', handleExtractData);

  // Reset button
  resetBtn.addEventListener('click', resetUpload);
}

// Handle files selected
function handleFilesSelected(files) {
  uploadedFiles = files;
  renderFilesList();
  document.getElementById('files-list').style.display = 'block';
  document.getElementById('extract-btn').disabled = false;
}

// Render files list
function renderFilesList() {
  const container = document.getElementById('files-container');

  const html = uploadedFiles.map((file, index) => `
    <div class="file-item">
      <div class="file-item-info">
        <div class="file-icon">
          <i class="bi bi-file-earmark-pdf"></i>
        </div>
        <div>
          <div class="fw-semibold">${escapeHtml(file.name)}</div>
          <div class="small text-muted">${formatFileSize(file.size)}</div>
        </div>
      </div>
      <i class="bi bi-x-circle file-remove" onclick="removeFile(${index})"></i>
    </div>
  `).join('');

  container.innerHTML = html;
}

// Remove file
function removeFile(index) {
  uploadedFiles.splice(index, 1);

  if (uploadedFiles.length === 0) {
    document.getElementById('files-list').style.display = 'none';
    document.getElementById('extract-btn').disabled = true;
    document.getElementById('create-file-input').value = '';
  } else {
    renderFilesList();
  }
}

// Handle extract data
async function handleExtractData() {
  const extractBtn = document.getElementById('extract-btn');
  const messageEl = document.getElementById('tender-message');

  if (uploadedFiles.length === 0) {
    showError(messageEl, 'Nessun file selezionato');
    return;
  }

  // Disable button
  extractBtn.disabled = true;
  extractBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Estrazione in corso...';

  const formData = new FormData();
  // The endpoint expects a single 'file' parameter
  formData.append('file', uploadedFiles[0]);

  try {
    const response = await fetch(`${apiBase}/ingestion/extract-all`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || 'Errore nell\'estrazione');
    }

    const data = await response.json();

    // Show success message
    showSuccess(messageEl, `Gara ${data.tender_code} creata con successo!`);

    // Redirect to tender detail page
    window.location.href = `/tender-detail?id=${data.tender_id}`;

  } catch (error) {
    showError(messageEl, error.message);
  } finally {
    extractBtn.disabled = false;
    extractBtn.innerHTML = '<i class="bi bi-magic me-2"></i>Estrai dati con AI';
  }
}

// Display extracted data
function displayExtractedData(data) {
  const container = document.getElementById('extracted-data-content');
  const section = document.getElementById('extracted-data');

  let html = '<div class="row g-3">';

  if (data.tender) {
    html += `
      <div class="col-12">
        <strong>Codice:</strong> ${escapeHtml(data.tender.code || 'N/D')}
      </div>
      <div class="col-12">
        <strong>Titolo:</strong> ${escapeHtml(data.tender.title || 'N/D')}
      </div>
      <div class="col-12">
        <strong>Buyer:</strong> ${escapeHtml(data.tender.buyer || 'N/D')}
      </div>
      <div class="col-md-6">
        <strong>Data pubblicazione:</strong> ${escapeHtml(data.tender.publish_date || 'N/D')}
      </div>
      <div class="col-md-6">
        <strong>Data chiusura:</strong> ${escapeHtml(data.tender.closing_date || 'N/D')}
      </div>
      <div class="col-12">
        <strong>Descrizione:</strong><br>
        ${escapeHtml(data.tender.description || 'N/D')}
      </div>
    `;
  }

  html += '</div>';
  container.innerHTML = html;
  section.style.display = 'block';
}

// Reset upload
function resetUpload() {
  uploadedFiles = [];
  document.getElementById('files-list').style.display = 'none';
  document.getElementById('extract-btn').disabled = true;
  document.getElementById('create-file-input').value = '';
  document.getElementById('tender-message').innerHTML = '';
  document.getElementById('extracted-data').style.display = 'none';
}

// Format file size
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Handle search
function handleSearch(e) {
  const query = e.target.value.toLowerCase();

  if (!query) {
    renderTenderList(allTenders);
    return;
  }

  const filtered = allTenders.filter(t =>
    t.code.toLowerCase().includes(query) ||
    t.title.toLowerCase().includes(query)
  );

  renderTenderList(filtered);
}

// Utility functions
function escapeHtml(text) {
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
    day: 'numeric'
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
    showToast(elementOrMessage, 'danger');
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

function showToast(message, type = 'info') {
  // Create toast container if it doesn't exist
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `alert alert-${type} alert-custom mb-2`;
  toast.style.cssText = 'min-width: 300px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);';
  toast.innerHTML = `
    <i class="bi bi-info-circle-fill"></i>
    <span>${message}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}
