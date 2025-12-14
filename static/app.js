const apiBase = "/api";
console.log("apiBase:", apiBase);

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

async function loadTenders() {
  const listEl = document.getElementById("tender-list");
  const selectEl = document.getElementById("tender-select"); // può non esistere su alcune pagine
  console.log("Carico gare da", `${apiBase}/tenders`);
  if (!listEl) {
    console.warn("Elemento tender-list non trovato");
    return;
  }
  listEl.innerHTML = "";
  if (selectEl) {
    selectEl.innerHTML = "";
  }
  const tenders = await fetchJSON(`${apiBase}/tenders?limit=100`);
  tenders.forEach((t) => {
    const li = document.createElement("li");
    const link = document.createElement("a");
    link.href = `/tender-detail?id=${t.id}`;
    link.textContent = `${t.code} — ${t.title} (${t.status ?? "n/d"})`;
    li.appendChild(link);
    listEl.appendChild(li);

    if (selectEl) {
      const opt = document.createElement("option");
      opt.value = t.id;
      opt.textContent = `${t.code} — ${t.title}`;
      selectEl.appendChild(opt);
    }
  });
}

async function handleCreateTender(e) {
  e.preventDefault();
  const form = e.target;
  const payload = {
    code: form.code.value,
    title: form.title.value,
    description: form.description.value || null,
    buyer: form.buyer.value || null,
    publish_date: form.publish_date.value || null,
    closing_date: form.closing_date.value || null,
  };
  try {
    const url = `${apiBase}/tenders`;
    console.log("POST tender ->", url, payload);
    const data = await fetchJSON(url, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    document.getElementById("tender-message").textContent = `Gara creata: ${data.id}`;
    form.reset();
    await loadTenders();
  } catch (err) {
    document.getElementById("tender-message").textContent = `Errore: ${err.message}`;
  }
}

async function handleCreateDocument(e) {
  // placeholder removed from demo page
  e.preventDefault();
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("tender-form").addEventListener("submit", handleCreateTender);
  const refreshBtn = document.getElementById("refresh-tenders");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", loadTenders);
  }
  loadTenders();
});
