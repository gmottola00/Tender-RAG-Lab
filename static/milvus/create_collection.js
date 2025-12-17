document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("create-collection-form");
    const fieldsContainer = document.getElementById("fields-container");
    const addFieldButton = document.getElementById("add-field");

    addFieldButton.addEventListener("click", () => {
        const fieldRow = document.createElement("div");
        fieldRow.classList.add("field-row", "row");
        fieldRow.innerHTML = `
            <div class="col-md-4">
                <input type="text" class="form-control" placeholder="Field Name" required>
            </div>
            <div class="col-md-4">
                <select class="form-select" required>
                    <option value="">Select Data Type</option>
                    <option value="FLOAT_VECTOR">Float Vector</option>
                    <option value="INT64">Int64</option>
                    <option value="FLOAT">Float</option>
                    <option value="STRING">String</option>
                </select>
            </div>
            <div class="col-md-3">
                <input type="number" class="form-control" placeholder="Dimension (if applicable)">
            </div>
            <div class="col-md-1">
                <button type="button" class="btn btn-danger remove-field">&times;</button>
            </div>
        `;
        fieldsContainer.appendChild(fieldRow);

        fieldRow.querySelector(".remove-field").addEventListener("click", () => {
            fieldsContainer.removeChild(fieldRow);
        });
    });

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const collectionName = document.getElementById("collection-name").value;
        const shardsNum = parseInt(document.getElementById("shards-num").value, 10);

        const fields = Array.from(fieldsContainer.querySelectorAll(".field-row")).map(row => {
            const fieldName = row.querySelector("input[type='text']").value;
            const dataType = row.querySelector("select").value;
            const dimension = row.querySelector("input[type='number']").value;

            const field = { name: fieldName, dtype: dataType };
            if (dataType === "FLOAT_VECTOR" && dimension) {
                field.dim = parseInt(dimension, 10);
            }
            return field;
        });

        const indexFieldName = document.getElementById("index-field-name").value;
        const indexType = document.getElementById("index-type").value;
        const metricType = document.getElementById("metric-type").value;

        const indexParams = indexFieldName && indexType && metricType ? {
            field_name: indexFieldName,
            index_type: indexType,
            metric_type: metricType
        } : null;

        const payload = {
            name: collectionName,
            shards_num: shardsNum,
            schema: fields,
            index_params: indexParams
        };

        try {
            const response = await axios.post("/api/milvus/collections", payload);
            alert("Collection created successfully!");
        } catch (error) {
            console.error(error);
            alert("Failed to create collection.");
        }
    });
});