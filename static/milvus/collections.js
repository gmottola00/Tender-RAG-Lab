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
                    <option value="BOOL">Bool</option>
                    <option value="INT8">Int8</option>
                    <option value="INT16">Int16</option>
                    <option value="INT32">Int32</option>
                    <option value="INT64">Int64</option>
                    <option value="FLOAT">Float</option>
                    <option value="DOUBLE">Double</option>
                    <option value="VARCHAR">VarChar</option>
                    <option value="JSON">JSON</option>
                    <option value="ARRAY">Array</option>
                    <option value="FLOAT_VECTOR">Float Vector</option>
                    <option value="BINARY_VECTOR">Binary Vector</option>
                    <option value="FLOAT16_VECTOR">Float16 Vector</option>
                    <option value="BFLOAT16_VECTOR">BFloat16 Vector</option>
                    <option value="SPARSE_FLOAT_VECTOR">Sparse Float Vector</option>
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

    // Event delegation for remove buttons (handles dynamically added fields)
    fieldsContainer.addEventListener("click", (e) => {
        if (e.target.classList.contains("remove-field") || e.target.closest(".remove-field")) {
            const button = e.target.classList.contains("remove-field") ? e.target : e.target.closest(".remove-field");
            const fieldRow = button.closest(".field-row");
            if (fieldRow) {
                fieldsContainer.removeChild(fieldRow);
            }
        }
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
            fieldRows.forEach((row, index) => {
                const fieldName = row.querySelector("input[type='text']").value.trim();
                const dataType = row.querySelector("select").value;
                const dimension = row.querySelector("input[type='number']").value;
                const isPrimary = row.querySelector(".is-primary").checked;

                // Validation: both name and type are required
                if (!fieldName) {
                    alert(`Campo #${index + 1}: il nome del campo è obbligatorio`);
                    throw new Error("Missing field name");
                }
                
                if (!dataType) {
                    alert(`Campo "${fieldName}": il tipo di dato è obbligatorio`);
                    throw new Error("Missing data type");
                }

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
                    <div class="card collection-card h-100">
                        <div class="card-body" onclick="window.location.href='/milvus/collections/${collection.name}'" style="cursor: pointer;">
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
                        <div class="card-footer bg-transparent border-top-0">
                            <button class="btn btn-sm btn-outline-info" onclick="event.stopPropagation(); copyExistingCollection('${collection.name}')">
                                <i class="bi bi-files"></i> Copia Schema
                            </button>
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

// Import/Export functionality
function showImportSchemaModal() {
    const modal = new bootstrap.Modal(document.getElementById('importSchemaModal'));
    modal.show();
}

function importSchema() {
    const textarea = document.getElementById('schemaImportText');
    try {
        const imported = JSON.parse(textarea.value);
        
        // Clear existing fields
        const fieldsContainer = document.getElementById('fields-container');
        fieldsContainer.innerHTML = '';
        
        // Import schema fields
        if (imported.schema && Array.isArray(imported.schema)) {
            imported.schema.forEach(field => {
                addFieldFromData(field);
            });
        }
        
        // Import index params if present
        if (imported.index_params) {
            document.getElementById('index-field-name').value = imported.index_params.field_name || '';
            document.getElementById('index-type').value = imported.index_params.index_type || '';
            document.getElementById('metric-type').value = imported.index_params.metric_type || '';
        }
        
        // Import shards_num if present
        if (imported.shards_num) {
            document.getElementById('shards-num').value = imported.shards_num;
        }
        
        bootstrap.Modal.getInstance(document.getElementById('importSchemaModal')).hide();
        showToast('Schema importato con successo!', 'success');
    } catch (error) {
        showToast('JSON non valido: ' + error.message, 'danger');
    }
}

function addFieldFromData(fieldData) {
    const fieldsContainer = document.getElementById('fields-container');
    const fieldRow = document.createElement('div');
    fieldRow.classList.add('row', 'g-2', 'mb-2', 'field-row');
    
    const dimensionValue = fieldData.dim || fieldData.max_length || '';
    
    fieldRow.innerHTML = `
        <div class="col-md-4">
            <input type="text" class="form-control" placeholder="Nome Campo" value="${fieldData.name || ''}" required>
        </div>
        <div class="col-md-3">
            <select class="form-select" required>
                <option value="">Tipo di Dato</option>
                <option value="BOOL" ${fieldData.dtype === 'BOOL' ? 'selected' : ''}>Bool</option>
                <option value="INT8" ${fieldData.dtype === 'INT8' ? 'selected' : ''}>Int8</option>
                <option value="INT16" ${fieldData.dtype === 'INT16' ? 'selected' : ''}>Int16</option>
                <option value="INT32" ${fieldData.dtype === 'INT32' ? 'selected' : ''}>Int32</option>
                <option value="INT64" ${fieldData.dtype === 'INT64' ? 'selected' : ''}>Int64</option>
                <option value="FLOAT" ${fieldData.dtype === 'FLOAT' ? 'selected' : ''}>Float</option>
                <option value="DOUBLE" ${fieldData.dtype === 'DOUBLE' ? 'selected' : ''}>Double</option>
                <option value="VARCHAR" ${fieldData.dtype === 'VARCHAR' ? 'selected' : ''}>VarChar</option>
                <option value="JSON" ${fieldData.dtype === 'JSON' ? 'selected' : ''}>JSON</option>
                <option value="ARRAY" ${fieldData.dtype === 'ARRAY' ? 'selected' : ''}>Array</option>
                <option value="FLOAT_VECTOR" ${fieldData.dtype === 'FLOAT_VECTOR' ? 'selected' : ''}>Float Vector</option>
                <option value="BINARY_VECTOR" ${fieldData.dtype === 'BINARY_VECTOR' ? 'selected' : ''}>Binary Vector</option>
                <option value="FLOAT16_VECTOR" ${fieldData.dtype === 'FLOAT16_VECTOR' ? 'selected' : ''}>Float16 Vector</option>
                <option value="BFLOAT16_VECTOR" ${fieldData.dtype === 'BFLOAT16_VECTOR' ? 'selected' : ''}>BFloat16 Vector</option>
                <option value="SPARSE_FLOAT_VECTOR" ${fieldData.dtype === 'SPARSE_FLOAT_VECTOR' ? 'selected' : ''}>Sparse Float Vector</option>
            </select>
        </div>
        <div class="col-md-2">
            <input type="number" class="form-control" placeholder="Dimensione" value="${dimensionValue}">
        </div>
        <div class="col-md-2">
            <div class="form-check mt-2">
                <input class="form-check-input is-primary" type="checkbox" ${fieldData.is_primary ? 'checked' : ''}>
                <label class="form-check-label">Primary</label>
            </div>
        </div>
        <div class="col-md-1">
            <button type="button" class="btn btn-danger btn-sm remove-field">&times;</button>
        </div>
    `;
    
    fieldsContainer.appendChild(fieldRow);
    // Event listener gestito da event delegation
}

function exportSchema() {
    const fieldsContainer = document.getElementById('fields-container');
    const fields = [];
    const fieldRows = fieldsContainer.querySelectorAll('.field-row');
    
    fieldRows.forEach(row => {
        const fieldName = row.querySelector('input[type="text"]').value.trim();
        const dataType = row.querySelector('select').value;
        const dimension = row.querySelector('input[type="number"]').value;
        const isPrimary = row.querySelector('.is-primary').checked;
        
        if (!fieldName || !dataType) return;
        
        const field = {
            name: fieldName,
            dtype: dataType,
        };
        
        if (dataType === 'FLOAT_VECTOR' && dimension) {
            field.dim = parseInt(dimension, 10);
        }
        
        if (dataType === 'VARCHAR' && dimension) {
            field.max_length = parseInt(dimension, 10);
        }
        
        if (isPrimary) {
            field.is_primary = true;
            field.auto_id = true;
        }
        
        fields.push(field);
    });
    
    const exportData = {
        schema: fields,
        shards_num: parseInt(document.getElementById('shards-num').value) || 2
    };
    
    const indexFieldName = document.getElementById('index-field-name').value.trim();
    const indexType = document.getElementById('index-type').value;
    const metricType = document.getElementById('metric-type').value;
    
    if (indexFieldName && indexType && metricType) {
        exportData.index_params = {
            field_name: indexFieldName,
            index_type: indexType,
            metric_type: metricType
        };
    }
    
    const json = JSON.stringify(exportData, null, 2);
    document.getElementById('schemaExportText').value = json;
    
    const modal = new bootstrap.Modal(document.getElementById('exportSchemaModal'));
    modal.show();
}

function copyExportedSchema() {
    const textarea = document.getElementById('schemaExportText');
    textarea.select();
    navigator.clipboard.writeText(textarea.value).then(() => {
        showToast('Schema copiato negli appunti!', 'success');
    }).catch(() => {
        document.execCommand('copy');
        showToast('Schema copiato negli appunti!', 'success');
    });
}

function downloadSchema() {
    const json = document.getElementById('schemaExportText').value;
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'milvus-schema.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

async function copyExistingCollection(collectionName) {
    try {
        // Fetch schema
        const schemaResponse = await fetch(`${apiBase}/collections/${collectionName}/schema`);
        if (!schemaResponse.ok) {
            throw new Error('Impossibile recuperare lo schema della collection');
        }
        const schemaData = await schemaResponse.json();
        
        // Clear and populate schema fields
        const fieldsContainer = document.getElementById('fields-container');
        fieldsContainer.innerHTML = '';
        
        if (schemaData.fields && Array.isArray(schemaData.fields)) {
            schemaData.fields.forEach(field => {
                addFieldFromData(field);
            });
        }
        
        // Show success message
        showToast(`Schema copiato da "${collectionName}"`, 'success');
        
        // Open the create modal
        const modal = new bootstrap.Modal(document.getElementById('createCollectionModal'));
        modal.show();
        
    } catch (error) {
        showToast('Errore nel copiare la collection: ' + error.message, 'danger');
    }
}

function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '11';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
    toast.show();
    
    // Remove toast after it's hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}