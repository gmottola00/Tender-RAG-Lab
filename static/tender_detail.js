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
  document.getElementById("meta-id").textContent = tender.id;
  document.getElementById("meta-created").textContent = tender.created_at || "";
  document.getElementById("meta-updated").textContent = tender.updated_at || "";
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
    document.getElementById("detail-message").textContent = "Nessun id fornito";
    return;
  }
  try {
    const tender = await fetchJSON("${apiBase}/tenders/${id}");
    fillForm(tender);
    fillMeta(tender);
  } catch (err) {
    document.getElementById("detail-message").textContent = "Errore: ${err.message}";
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
    const updated = await fetchJSON("${apiBase}/tenders/${id}", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    document.getElementById("detail-message").textContent = "Aggiornamento eseguito";
    fillForm(updated);
    fillMeta(updated);
  } catch (err) {
    document.getElementById("detail-message").textContent = "Errore: ${err.message}";
  }
}

async function handleCreateDocument(e) {
  e.preventDefault();
  const form = e.target;
  const tenderId = getTenderId();
  if (!tenderId) {
    document.getElementById("document-message").textContent = "ID gara mancante";
    return;
  }
  const payload = {
    tender_id: tenderId,
    lot_id: form.lot_id.value || null,
    filename: form.filename?.value || null,
    document_type: form.document_type.value || null,
    file_hash: form.file_hash.value || null,
    uploaded_by: form.uploaded_by.value || null,
  };
  try {
    const url = "${apiBase}/documents";
    console.log("POST document ->", url, payload);
    const data = await fetchJSON(url, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    document.getElementById("document-message").textContent = "Documento registrato: ${data.id}";
    form.reset();
    document.getElementById("filename-input").value = "";
    document.getElementById("doc-dropzone")?.querySelector("p").textContent = "Trascina un file qui oppure clicca per selezionarlo";
  } catch (err) {
    document.getElementById("document-message").textContent = "Errore: ${err.message}";
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
      dropzone.querySelector("p").textContent = "File selezionato: ${file.name}";
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
});
