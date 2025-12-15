document.addEventListener("DOMContentLoaded", () => {
  const existing = document.getElementById("global-offcanvas");
  if (existing) return;

  const links = [
    { href: "/", label: "🏠 Home" },
    { href: "/demo", label: "📄 Tender Management" },
    { href: "/milvus", label: "🧭 Milvus Explorer" },
  ];

  const current = window.location.pathname;
  const wrapper = document.createElement("div");
  wrapper.innerHTML = `
    <div class="offcanvas offcanvas-start" tabindex="-1" id="global-offcanvas" aria-labelledby="global-offcanvas-label">
      <div class="offcanvas-header">
        <h5 class="offcanvas-title" id="global-offcanvas-label">Navigation</h5>
        <button type="button" class="btn-close text-reset" data-bs-dismiss="offcanvas" aria-label="Close"></button>
      </div>
      <div class="offcanvas-body">
        <div class="list-group" id="global-offcanvas-links"></div>
        <hr>
        <p class="text-muted small mb-1">Tips</p>
        <ul class="small text-muted ps-3 mb-0">
          <li>Clicca una collection per vedere schema e dati</li>
          <li>Usa la preview per ispezionare i documenti</li>
          <li>Vector search per sanity check sui chunks</li>
        </ul>
      </div>
    </div>
  `;

  document.body.appendChild(wrapper);
  const list = document.getElementById("global-offcanvas-links");
  links.forEach((link) => {
    const a = document.createElement("a");
    a.className = "list-group-item list-group-item-action";
    if (current === link.href) {
      a.classList.add("active");
    }
    a.href = link.href;
    a.textContent = link.label;
    list.appendChild(a);
  });
});
