window.onload = function() {
    fetch('/validation_summary')
        .then(response => response.json())
        .then(data => {
            createPlot('validationPlot', 'Overall Validation Status', data.validation_summary);
            createPlot('statusReasonPlot', 'Validation Failure Occurred Reasons', data.status_reasons);
        })
        .catch(error => console.error('Error fetching validation data:', error));

    fetch('/predictions')
        .then(response => response.json())
        .then(data => {
            createPlot('predictionPlot', 'Prediction Summary', data.predictions_summary);
        })
        .catch(error => console.error('Error fetching predictions data:', error));

    fetch('/bad_raw_files')
        .then(response => response.json())
        .then(data => {
            populateBadFilesList(data.bad_files);
        })
        .catch(error => console.error('Error fetching bad raw files:', error));
};

function createPlot(canvasId, title, data) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(data),
            datasets: [{
                label: title,
                data: Object.values(data),
                backgroundColor: ['#4CAF50', '#FF5733', '#33C3FF'],
                borderColor: '#333',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            animation: {
                duration: 1000,
                easing: 'easeInOutBounce'
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function populateBadFilesList(files) {
    const list = document.getElementById('badRawFilesList');
    files.forEach(file => {
        const li = document.createElement('li');
        li.textContent = file;
        list.appendChild(li);
    });
}

document.getElementById('downloadValidationReport').addEventListener('click', function() {
    downloadData('/download/validation_report', 'validation_logs.xlsx');
});

document.getElementById('downloadFailedFiles').addEventListener('click', function() {
    downloadData('/download/failed_files', 'failed_files.zip');
});

document.getElementById('downloadPredictions').addEventListener('click', function() {
    downloadData('/download/predictions', 'predictions.csv');
});

function downloadData(url, filename) {
    fetch(url)
        .then(response => {
            if (response.ok) {
                return response.blob();
            }
            throw new Error('Failed to download file');
        })
        .then(blob => {
            const link = document.createElement('a');
            link.href = window.URL.createObjectURL(blob);
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        })
        .catch(error => {
            console.error('Error downloading the file:', error);
            alert('An error occurred while downloading the file.');
        });
}
