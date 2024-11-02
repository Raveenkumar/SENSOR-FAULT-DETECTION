document.getElementById('predictBtn').addEventListener('click', function() {
    const loadingAnimation = document.getElementById('loading');
    loadingAnimation.style.display = 'block'; // Show loading animation

    // First, trigger the prediction API call
    fetch('/data_prediction', { 
        method: 'POST',
    })
    .then(response => response.json())
    .then(data => {
        loadingAnimation.style.display = 'none'; // Hide loading animation
        // Check if prediction was successful
        if (data.message === "Prediction successful!") {
            alert('Prediction completed successfully!');
            // After the prediction is successful, navigate to the dashboard
            window.location.href = '/dashboard';
        } else {
            alert('Prediction failed!');
        }
    })
    .catch(error => {
        loadingAnimation.style.display = 'none'; // Hide loading animation
        console.error('Error during prediction:', error);
        alert('Prediction failed!');
    });
});

// adding training
document.getElementById('uploadForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const files = document.getElementById('folderUpload').files;
    const formData = new FormData();
    
    // Add files to FormData
    for (let file of files) {
        formData.append('files', file);
    }

    // Upload files to the correct endpoint
    fetch('/upload', {  // Corrected endpoint
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const predictionSection = document.getElementById('predictionSection');
        predictionSection.classList.add('show');
        alert('Files uploaded successfully!');
    })
    .catch(error => console.error('Error uploading files:', error));
});


// Training Button Click Event
document.getElementById('trainBtn').addEventListener('click', function() {
    const trainingStatus = document.getElementById('trainingStatus');
    trainingStatus.textContent = 'Training in Progress...';

    fetch('/train')
        .then(response => response.json())
        .then(data => {
            trainingStatus.textContent = 'Training Completed!';
            alert('Training Completed. Check the dashboard for reports.');
        })
        .catch(error => {
            trainingStatus.textContent = 'Training Failed!';
            console.error('Error during training:', error);
        });
});

// Modify the upload path to the correct route '/upload'
document.getElementById('uploadForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const files = document.getElementById('folderUpload').files;
    const formData = new FormData();
    
    // Add files to FormData
    for (let file of files) {
        formData.append('files', file);
    }

    // Upload files to the correct endpoint
    fetch('/upload', {  // Corrected endpoint
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const predictionSection = document.getElementById('predictionSection');
        predictionSection.classList.add('show');
        alert('Files uploaded successfully!');
    })
    .catch(error => console.error('Error uploading files:', error));
});
