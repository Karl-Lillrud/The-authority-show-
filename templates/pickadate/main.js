document.addEventListener("DOMContentLoaded", function () {
    const bookingForm = document.getElementById("booking-form");
    const uploadInput = document.getElementById("upload");
    const uploadButton = document.getElementById("upload-btn");
    const uploadStatus = document.getElementById("upload-status");
    const submitButton = document.getElementById("submit-btn");

    let uploadedFileUrl = null; // Stores the uploaded file URL

    // Upload File to Azure Blob Storage
    uploadButton.addEventListener("click", function () {
        if (uploadInput.files.length === 0) {
            uploadStatus.innerHTML = "⚠ No file selected!";
            return;
        }

        let file = uploadInput.files[0];
        let formData = new FormData();
        formData.append("file", file);

        uploadStatus.innerHTML = "🔄 Uploading...";

        fetch("/upload-file", {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.fileUrl) {
                uploadedFileUrl = data.fileUrl; // Store the uploaded file URL
                uploadStatus.innerHTML = "✅ File uploaded successfully!";
                submitButton.disabled = false; // Enable submit button
            } else {
                uploadStatus.innerHTML = "❌ Upload failed!";
            }
        })
        .catch(error => {
            console.error("Upload error:", error);
            uploadStatus.innerHTML = "❌ Upload failed!";
        });
    });

    // Submit Booking Form After File Upload
    bookingForm.addEventListener("submit", function (event) {
        event.preventDefault(); // Prevent default form submission

        if (!uploadedFileUrl) {
            uploadStatus.innerHTML = "⚠ Please upload a file before submitting.";
            return;
        }

        let formData = new FormData(bookingForm);
        formData.append("fileUrl", uploadedFileUrl); // Attach uploaded file URL

        fetch(bookingForm.action, {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.bookingId) {
                alert("✅ Booking confirmed! Your ID: " + data.bookingId);
                bookingForm.reset();
                uploadStatus.innerHTML = "";
                submitButton.disabled = true; // Disable submit button again
            } else {
                alert("❌ Booking failed! Please try again.");
            }
        })
        .catch(error => {
            console.error("Booking error:", error);
            alert("❌ Booking failed! Please try again.");
        });
    });
});
