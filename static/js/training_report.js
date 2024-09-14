// Store charts to manage canvas reuse
let charts = {};

window.onload = function () {
    // Validation Summary Plot
    if (document.getElementById('validationPlot_one') !== null) {
        createPlot('validationPlot_one', 'Validation Summary', window.validation_summary);
    }

    if (document.getElementById('validationPlot_two') !== null) {
        createPlot('validationPlot_two', 'Validation Status Reasons', window.validation_status_reasons);
    }

    // New Plot for No Duplicate Rows
    if (document.getElementById('noDuplicateRowsPlot') !== null) {
        createNoDuplicateRowsPlot(window.preprocessing_summary.total_records, window.preprocessing_summary.no_of_duplicate_rows);
    }

    // New Plot for Remaining Preprocessing Summary
    if (document.getElementById('remainingPreprocessingPlot') !== null) {
        createRemainingPreprocessingPlot(window.preprocessing_summary.total_columns, {
            zero_std_columns: window.preprocessing_summary.zero_std_columns,
            nan_contains_columns: window.preprocessing_summary.nan_contains_columns,
            highskew_columns: window.preprocessing_summary.highskew_columns,
            outlier_columns: window.preprocessing_summary.outlier_columns
        });
    }

    // Dynamically handle plots for all models clusters and models
    if (window.clusters_data) {
        Object.keys(window.clusters_data).forEach(clusterName => {
            window.clusters_data[clusterName].forEach(model => {
                const canvasId = `plot_${clusterName.replace(/\s/g, '_')}_${model.model_name.replace(/\s/g, '_')}`;
                createModelPlot(canvasId, model.model_name, model.model_scores);
            });
        });
    }

    // Dynamically handle plots for best models clusters and models
    if (window.best_model_clusters_data) {
        Object.keys(window.best_model_clusters_data).forEach(clusterName => {
            window.best_model_clusters_data[clusterName].forEach(model => {
                const canvasId = `best_plot_${clusterName.replace(/\s/g, '_')}_${model.model_name.replace(/\s/g, '_')}`;
                createModelPlot(canvasId, model.model_name, model.model_scores);
            });
        });
    }
};

// Function to create a generic plot
function createPlot(canvasId, title, data) {
    const canvasElement = document.getElementById(canvasId);
    if (canvasElement === null) {
        console.warn(`Canvas element with ID '${canvasId}' not found.`);
        return; // Exit the function if the canvas element is not found
    }

    destroyExistingChart(canvasId); // Destroy any existing chart before creating a new one

    const ctx = canvasElement.getContext('2d');
    charts[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(data),
            datasets: [{
                label: title,
                data: Object.values(data),
                backgroundColor: ['#4CAF50', '#FF5733', '#33C3FF', '#FFB3BA', '#B2FF59'],
                borderColor: '#333',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Function to create a model-specific plot dynamically
function createModelPlot(canvasId, modelName, modelScores) {
    const canvasElement = document.getElementById(canvasId);
    if (canvasElement === null) {
        console.warn(`Canvas element with ID '${canvasId}' not found.`);
        return; // Exit if the canvas element is not found
    }

    destroyExistingChart(canvasId); // Destroy any existing chart before creating a new one

    const ctx = canvasElement.getContext('2d');
    charts[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(modelScores),
            datasets: [{
                label: modelName,
                data: Object.values(modelScores),
                backgroundColor: ['#4CAF50', '#FF5733', '#33C3FF', '#FFB3BA', '#B2FF59'],
                borderColor: '#333',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Function to create the "No Duplicate Rows" plot
function createNoDuplicateRowsPlot(totalRecords, noOfDuplicateRows) {
    const canvasElement = document.getElementById('noDuplicateRowsPlot');
    if (canvasElement === null) {
        console.warn(`Canvas element with ID 'noDuplicateRowsPlot' not found.`);
        return;
    }

    destroyExistingChart('noDuplicateRowsPlot'); // Destroy existing chart if exists

    const ctx = canvasElement.getContext('2d');
    charts['noDuplicateRowsPlot'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['No of Duplicate Rows'],
            datasets: [{
                label: 'Total Records: ' + totalRecords,
                data: [noOfDuplicateRows],
                backgroundColor: '#4CAF50',
                borderColor: '#333',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Function to create the "Remaining Preprocessing Summary" plot
function createRemainingPreprocessingPlot(totalColumns, data) {
    const canvasElement = document.getElementById('remainingPreprocessingPlot');
    if (canvasElement === null) {
        console.warn(`Canvas element with ID 'remainingPreprocessingPlot' not found.`);
        return;
    }

    destroyExistingChart('remainingPreprocessingPlot'); // Destroy existing chart if exists

    const ctx = canvasElement.getContext('2d');
    charts['remainingPreprocessingPlot'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Zero Std Columns', 'NaN Contains Columns', 'High Skew Columns', 'Outlier Columns'],
            datasets: [{
                label: 'Total Columns: ' + totalColumns,
                data: [
                    data.zero_std_columns,
                    data.nan_contains_columns,
                    data.highskew_columns,
                    data.outlier_columns
                ],
                backgroundColor: ['#FF5733', '#33C3FF', '#FFC300', '#DAF7A6'],
                borderColor: '#333',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Function to destroy any existing chart on the canvas
function destroyExistingChart(canvasId) {
    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }
}
