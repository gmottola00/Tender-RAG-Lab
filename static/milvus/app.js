const apiBase = "/api/milvus";

async function fetchJSON(url, options = {}) {
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || resp.statusText);
  }
  return resp.json();
}

async function loadCollections() {
  const listEl = document.getElementById("collections");
  listEl.innerHTML = "Loading...";
  try {
    const data = await fetchJSON(`${apiBase}/collections`);
    listEl.innerHTML = "";
    data.forEach((c) => {
      const li = document.createElement("li");
      li.classList.add("collection-item");
      li.textContent = `${c.name} (rows: ${c.row_count ?? "n/d"})`;
      li.addEventListener("click", () => loadSchema(c.name));
      listEl.appendChild(li);
    });
  } catch (err) {
    listEl.innerHTML = `Errore: ${err.message}`;
  }
}

async function loadSchema(name) {
  const el = document.getElementById("schema");
  el.classList.remove("d-none");
  el.textContent = "Loading...";
  try {
    const data = await fetchJSON(`${apiBase}/collections/${name}/schema`);
    el.textContent = JSON.stringify(data, null, 2);
    document.getElementById("preview-collection").value = name;
  } catch (err) {
    el.textContent = `Errore: ${err.message}`;
  }
}

async function doPreview() {
  const name = document.getElementById("preview-collection").value || "tender_chunks";
  const limit = Number(document.getElementById("preview-limit").value || 20);
  const out = document.getElementById("preview-output");
  const tableWrap = document.getElementById("preview-table");
  out.style.display = "none";
  tableWrap.innerHTML = "<p class='text-muted small mb-0'>Loading...</p>";
  try {
    const data = await fetchJSON(`${apiBase}/collections/${name}/preview?limit=${limit}`);
    renderTable(tableWrap, data.rows || []);
  } catch (err) {
    tableWrap.innerHTML = "";
    out.style.display = "block";
    out.textContent = `Errore: ${err.message}`;
  }
}

async function doVectorSearch() {
  const q = document.getElementById("search-query").value || "";
  const topk = Number(document.getElementById("search-topk").value || 5);
  const out = document.getElementById("search-output");
  out.textContent = "Loading...";
  try {
    const data = await fetchJSON(`${apiBase}/chunks/vector-search?query=${encodeURIComponent(q)}&top_k=${topk}`);
    out.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    out.textContent = `Errore: ${err.message}`;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("reload-collections").addEventListener("click", loadCollections);
  document.getElementById("btn-preview").addEventListener("click", doPreview);
  document.getElementById("btn-search").addEventListener("click", doVectorSearch);
  loadCollections();
});

function renderTable(container, rows) {
  if (!rows || rows.length === 0) {
    container.innerHTML = "<p>Nessun dato</p>";
    return;
  }
  const headers = Array.from(
    rows.reduce((set, row) => {
      Object.keys(row).forEach((k) => set.add(k));
      return set;
    }, new Set())
  );
  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const trh = document.createElement("tr");
  headers.forEach((h) => {
    const th = document.createElement("th");
    th.textContent = h;
    trh.appendChild(th);
  });
  thead.appendChild(trh);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    headers.forEach((h) => {
      const td = document.createElement("td");
      const val = row[h];
      td.textContent = typeof val === "object" ? JSON.stringify(val) : val;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  container.innerHTML = "";
  container.appendChild(table);
}
