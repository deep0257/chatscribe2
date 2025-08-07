// Custom JavaScript for ChatScribe

document.addEventListener('DOMContentLoaded', function() {
    // File upload drag-and-drop
    const fileUploadArea = document.querySelector('.file-upload-area');
    const fileInput = document.getElementById('file');

    if (fileUploadArea) {
        fileUploadArea.addEventListener('click', () => fileInput.click());

        fileUploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileUploadArea.classList.add('dragover');
        });

        fileUploadArea.addEventListener('dragleave', () => {
            fileUploadArea.classList.remove('dragover');
        });

        fileUploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            fileUploadArea.classList.remove('dragover');
            fileInput.files = e.dataTransfer.files;
        });
    }
});

