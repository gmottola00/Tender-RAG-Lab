const apiBase = "/api/milvus";

document.addEventListener("DOMContentLoaded", () => {
    const fieldsContainer = document.getElementById("fields-container");
    const addFieldButton = document.getElementById("add-field");
    const createCollectionBtn = document.getElementById("create-collection-btn");
    const collectionsGrid = document.getElementById("collections-grid");
    const modal = new bootstrap.Modal(document.getElementById('createCollectionModal'));

    // Carica le collection
    loadCollections();

    // Aggiungi campo
    addFieldButton.addEventListener("click", () => {
        const fieldRow = document.createElement("div");
        fieldRow.classList.add("row", "g-2", "mb-2", "field-row");
        fieldRow.innerHTML = `
            <div class="col-md-4">
                <input type="text" class="form-control" placeholder="Nome Campo" required>
            </div>
            <div class="col-md-3">
                <select class="form-select" required>
                    <option value="">Tipo di Dato</option>
                    <option value="FLOAT_VECTOR">Float Vector</option>
                    <option value="INT64">Int64</option>
                    <option value="FLOAT">Float</option>
                    <option value="VARCHAR">String</option>
                </select>
            </div>
            <div class="col-md-2">
                <input type="number" class="form-control" placeholder="Dimensione">
            </div>
            <div class="col-md-2">
                <div class="form-check mt-2">
                    <input class="form-check-input is-primary" type="checkbox">
                    <label class="form-check-label">Primary</label>
                </div>
            </div>
            <div class="col-md-1">
                <button type="button" class="btn btn-danger btn-sm remove-field">&times;</button>
            </div>
        `;
        fieldsContainer.appendChild(fieldRow);

        fieldRow.querySelector(".remove-field").addEventListener("click", () => {
            fieldsContainer.removeChild(fieldRow);
        });
    });

    // Rimuovi primo campo
    fieldsContainer.querySelector(".remove-field").addEventListener("click", (e) => {
        e.target.closest(".field-row").remove();
    });

    // Crea collection
    createCollectionBtn.addEventListener("click", async () => {
        const collectionName = document.getElementById("collection-name").value.trim();
        const shardsNum = parseInt(document.getElementById("shards-num").value, 10);

        if (!collectionName) {
            alert("Inserisci un nome per la collection");
            return;
        }

        const fields = [];
        const fieldRows = fieldsContainer.querySelectorAll(".field-row");
        
        let hasVector = false;
        let hasPrimary = false;
        
        try {
            fieldRows.forEach(row => {
            const fieldName = row.querySelector("input[type='text']").value.trim();
            const dataType = row.querySelector("select").value;
            const dimension = row.querySelector("input[type='number']").value;
            const isPrimary = row.querySelector(".is-primary").checked;

            if (!fieldName || !dataType) return;

            const field = { 
                name: fieldName, 
                dtype: dataType,
            };
            
            if (dataType === "FLOAT_VECTOR") {
                hasVector = true;
                if (!dimension) {
                    alert(`Il campo vettoriale '${fieldName}' richiede una dimensione obbligatoria`);
                    throw new Error("Missing dimension");
                }
                field.dim = parseInt(dimension, 10);
            }
            
            if (dataType === "VARCHAR") {
                if (!dimension) {
                    alert(`Il campo VARCHAR '${fieldName}' richiede max_length obbligatorio`);
                    throw new Error("Missing max_length");
                }
                field.max_length = parseInt(dimension, 10);
            }
            
            if (isPrimary) {
                hasPrimary = true;
                field.is_primary = true;
                field.auto_id = true;
            }

            fields.push(field);
        });
        } catch (error) {
            return; // Stop execution if validation fails
        }

        if (fields.length === 0) {
            alert("Aggiungi almeno un campo allo schema");
            return;
        }

        if (!hasVector) {
            alert("La collection deve contenere almeno un campo vettoriale (FLOAT_VECTOR)");
            return;
        }

        if (!hasPrimary) {
            alert("La collection deve avere un campo primary key. Seleziona la checkbox 'Primary' su un campo INT64");
            return;
        }

        const indexFieldName = document.getElementById("index-field-name").value.trim();
        const indexType = document.getElementById("index-type").value;
        const metricType = document.getElementById("metric-type").value;

        const payload = {
            name: collectionName,
            shards_num: shardsNum,
            schema: fields,
        };

        if (indexFieldName && indexType && metricType) {
            payload.index_params = {
                field_name: indexFieldName,
                index_type: indexType,
                metric_type: metricType
            };
        }

        try {
            const response = await fetch(`${apiBase}/collections`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || "Errore nella creazione");
            }

            modal.hide();
            document.getElementById("create-collection-form").reset();
            loadCollections();
        } catch (error) {
            console.error("Errore:", error);
            alert(`Errore: ${error.message}`);
        }
    });

    async function loadCollections() {
        try {
            const response = await fetch(`${apiBase}/collections`);
            const collections = await response.json();

            collectionsGrid.innerHTML = "";
            
            collections.forEach(collection => {
                const card = document.createElement("div");
                card.className = "col-md-6 col-lg-4";
                card.innerHTML = `
                    <div class="card collection-card h-100" onclick="window.location.href='/milvus/collections/${collection.name}'">
                        <div class="card-body">
                            <h5 class="card-title">
                                <i class="bi bi-collection-fill text-primary"></i>
                                ${collection.name}
                            </h5>
                            <p class="card-text text-muted">
                                <small>
                                    <i class="bi bi-diagram-3"></i> ${collection.row_count ?? 0} record
                                </small>
                            </p>
                        </div>
                    </div>
                `;
                collectionsGrid.appendChild(card);
            });
        } catch (error) {
            console.error("Errore nel caricamento delle collection:", error);
            collectionsGrid.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">Errore nel caricamento delle collection</div>
                </div>
            `;
        }
    }
});