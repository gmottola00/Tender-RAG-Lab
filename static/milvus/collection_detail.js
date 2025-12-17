const apiBase = "/api/milvus";
let collectionName = "";

document.addEventListener("DOMContentLoaded", () => {
    // Estrai il nome della collection dall'URL
    const pathParts = window.location.pathname.split("/");
    collectionName = pathParts[pathParts.length - 1];
    
    document.getElementById("collection-name-display").textContent = collectionName;
    
    // Carica i dati iniziali
    loadCollectionInfo();
    
    // Event listeners
    document.getElementById("delete-collection-btn").addEventListener("click", deleteCollection);
    document.getElementById("load-data-btn").addEventListener("click", loadData);
    document.getElementById("search-btn").addEventListener("click", performSearch);
    document.getElementById("chat-form").addEventListener("submit", sendChatMessage);
    
    // Carica dati quando si cambia tab
    document.getElementById("data-tab").addEventListener("click", () => {
        if (!document.getElementById("data-table").innerHTML) {
            loadData();
        }
    });
});

async function loadCollectionInfo() {
    try {
        // Carica schema
        const schemaResponse = await fetch(`${apiBase}/collections/${collectionName}/schema`);
        const schema = await schemaResponse.json();
        
        document.getElementById("schema-json").textContent = JSON.stringify(schema, null, 2);
        
        // Aggiorna stats
        if (schema.fields) {
            document.getElementById("stat-field-count").textContent = schema.fields.length;
        }
        
        // Carica info collection per row count
        const collectionsResponse = await fetch(`${apiBase}/collections`);
        const collections = await collectionsResponse.json();
        const currentCollection = collections.find(c => c.name === collectionName);
        
        if (currentCollection) {
            document.getElementById("stat-row-count").textContent = currentCollection.row_count ?? 0;
        }
        
        // Per ora impostiamo indici a 0 (da implementare endpoint specifico)
        document.getElementById("stat-index-count").textContent = "N/A";
        
    } catch (error) {
        console.error("Errore nel caricamento delle info:", error);
        document.getElementById("schema-json").textContent = `Errore: ${error.message}`;
    }
}

async function loadData() {
    const limit = document.getElementById("data-limit").value;
    const dataTable = document.getElementById("data-table");
    
    dataTable.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';
    
    try {
        const response = await fetch(`${apiBase}/collections/${collectionName}/preview?limit=${limit}`);
        const data = await response.json();
        
        if (data.rows && data.rows.length > 0) {
            // Crea tabella
            const keys = Object.keys(data.rows[0]);
            let html = '<table class="table table-striped table-hover"><thead><tr>';
            
            keys.forEach(key => {
                html += `<th>${key}</th>`;
            });
            html += '</tr></thead><tbody>';
            
            data.rows.forEach(row => {
                html += '<tr>';
                keys.forEach(key => {
                    let value = row[key];
                    // Tronca array lunghi
                    if (Array.isArray(value) && value.length > 5) {
                        value = `[${value.slice(0, 5).join(", ")}...]`;
                    } else if (Array.isArray(value)) {
                        value = `[${value.join(", ")}]`;
                    } else if (typeof value === 'object') {
                        value = JSON.stringify(value);
                    }
                    html += `<td>${value}</td>`;
                });
                html += '</tr>';
            });
            
            html += '</tbody></table>';
            dataTable.innerHTML = html;
        } else {
            dataTable.innerHTML = '<p class="text-muted">Nessun dato disponibile</p>';
        }
    } catch (error) {
        console.error("Errore nel caricamento dei dati:", error);
        dataTable.innerHTML = `<div class="alert alert-danger">Errore: ${error.message}</div>`;
    }
}

async function performSearch() {
    const query = document.getElementById("search-query").value.trim();
    const topK = document.getElementById("search-top-k").value;
    const resultsDiv = document.getElementById("search-results");
    
    if (!query) {
        alert("Inserisci una query");
        return;
    }
    
    resultsDiv.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';
    
    try {
        const response = await fetch(`${apiBase}/chunks/vector-search?query=${encodeURIComponent(query)}&top_k=${topK}`);
        const data = await response.json();
        
        if (data.results && data.results.length > 0) {
            let html = '<div class="list-group">';
            data.results.forEach((result, idx) => {
                html += `
                    <div class="list-group-item">
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">Risultato ${idx + 1}</h6>
                            <small>Score: ${result.score?.toFixed(4) || 'N/A'}</small>
                        </div>
                        <p class="mb-1">${result.text || JSON.stringify(result)}</p>
                    </div>
                `;
            });
            html += '</div>';
            resultsDiv.innerHTML = html;
        } else {
            resultsDiv.innerHTML = '<p class="text-muted">Nessun risultato trovato</p>';
        }
    } catch (error) {
        console.error("Errore nella ricerca:", error);
        resultsDiv.innerHTML = `<div class="alert alert-danger">Errore: ${error.message}</div>`;
    }
}

async function sendChatMessage(event) {
    event.preventDefault();
    
    const input = document.getElementById("chat-input");
    const message = input.value.trim();
    
    if (!message) return;
    
    const chatBox = document.getElementById("chat-box");
    
    // Aggiungi messaggio utente
    appendMessage(message, "user");
    input.value = "";
    
    // Aggiungi indicatore di caricamento
    const loadingDiv = document.createElement("div");
    loadingDiv.className = "chat-message bot";
    loadingDiv.innerHTML = '<div class="message-content"><div class="spinner-border spinner-border-sm" role="status"></div> Pensando...</div>';
    chatBox.appendChild(loadingDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
    
    try {
        const response = await fetch(`${apiBase}/chatbot`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                message: message,
                collection_name: collectionName 
            })
        });
        
        const data = await response.json();
        
        // Rimuovi indicatore di caricamento
        chatBox.removeChild(loadingDiv);
        
        // Aggiungi risposta bot
        appendMessage(data.reply || data.response || "Nessuna risposta disponibile", "bot");
    } catch (error) {
        console.error("Errore nella chat:", error);
        chatBox.removeChild(loadingDiv);
        appendMessage("Errore nella comunicazione con il chatbot", "bot");
    }
}

function appendMessage(text, sender) {
    const chatBox = document.getElementById("chat-box");
    
    // Rimuovi messaggio iniziale se presente
    const emptyMessage = chatBox.querySelector(".text-muted.text-center");
    if (emptyMessage) {
        emptyMessage.remove();
    }
    
    const messageDiv = document.createElement("div");
    messageDiv.className = `chat-message ${sender}`;
    messageDiv.innerHTML = `<div class="message-content">${text}</div>`;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function deleteCollection() {
    if (!confirm(`Sei sicuro di voler eliminare la collection '${collectionName}'? Questa azione è irreversibile.`)) {
        return;
    }
    
    try {
        const response = await fetch(`${apiBase}/collections/${collectionName}`, {
            method: "DELETE"
        });
        
        if (response.ok) {
            alert("Collection eliminata con successo");
            window.location.href = "/milvus/collections";
        } else {
            throw new Error("Errore nell'eliminazione");
        }
    } catch (error) {
        console.error("Errore:", error);
        alert(`Errore: ${error.message}`);
    }
}