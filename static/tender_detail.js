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
    document.getElementById("detail-message").textContent = "Nessun id fornito";
    return;
  }
  try {
    const tender = await fetchJSON(`${apiBase}/tenders/${id}`);
    fillForm(tender);
    fillMeta(tender);
  } catch (err) {
    document.getElementById("detail-message").textContent = `Errore: ${err.message}`;
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
    document.getElementById("detail-message").textContent = "Aggiornamento eseguito";
    fillForm(updated);
    fillMeta(updated);
  } catch (err) {
    document.getElementById("detail-message").textContent = `Errore: ${err.message}`;
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
  const fd = new FormData();
  fd.append("tender_id", tenderId);
  if (form.lot_id.value) fd.append("lot_id", form.lot_id.value);
  fd.append("document_type", form.document_type.value || "");

  const fileInput = document.getElementById("doc-file-input");
  const file = fileInput?.files?.[0];
  if (!file) {
    document.getElementById("document-message").textContent = "Seleziona un file";
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
    document.getElementById("document-message").textContent = `Documento registrato: ${data.id}`;
    form.reset();
    if (fileInput) fileInput.value = "";
    document.getElementById("filename-input").value = "";
    const dz = document.getElementById("doc-dropzone");
    if (dz) {
      const p = dz.querySelector("p");
      if (p) p.textContent = "Trascina un file qui oppure clicca per selezionarlo";
    }
  } catch (err) {
    document.getElementById("document-message").textContent = `Errore: ${err.message}`;
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
  const ingestAllBtn = document.getElementById("ingest-all-btn");
  if (ingestAllBtn) {
    ingestAllBtn.addEventListener("click", ingestAllDocuments);
  }
});

async function loadDocuments() {
  const listEl = document.getElementById("documents-list");
  if (!listEl) return;
  const tenderId = getTenderId();
  if (!tenderId) return;
  listEl.innerHTML = "";
  try {
    const docs = await fetchJSON(`${apiBase}/documents?tender_id=${tenderId}&limit=200`);
    docs.forEach((d) => {
      const li = document.createElement("li");
      li.innerHTML = `<strong>${d.filename}</strong> — ${d.document_type || "n/d"} (${d.id})`;
      const btn = document.createElement("button");
      btn.textContent = "Indicizza";
      btn.style.marginLeft = "0.5rem";
      btn.addEventListener("click", () => ingestDocument(d.id));
      li.appendChild(btn);
      listEl.appendChild(li);
    });
  } catch (err) {
    document.getElementById("documents-message").textContent = `Errore caricamento documenti: ${err.message}`;
  }
}

async function ingestDocument(documentId) {
  try {
    const resp = await fetchJSON(`${apiBase}/documents/${documentId}/ingest`, { method: "POST" });
    document.getElementById("documents-message").textContent = `Indicizzato documento ${documentId} (chunks: ${resp.inserted})`;
  } catch (err) {
    document.getElementById("documents-message").textContent = `Errore indicizzazione: ${err.message}`;
  }
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
