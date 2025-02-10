document.addEventListener("DOMContentLoaded", function () { 
    const bookingForm = document.getElementById("booking-form");
    const uploadInput = document.getElementById("upload");
    const uploadStatus = document.getElementById("upload-status") || document.createElement("div");
    uploadInput.insertAdjacentElement("afterend", uploadStatus);
    const submitButton = document.querySelector("button[type='submit']");

    let uploadedFileUrl = null; // Stores the uploaded file URL

    // Upload File to Azure Blob Storage
    function uploadFile(file) {
        return new Promise((resolve, reject) => {
            let formData = new FormData();
            formData.append("file", file);

            uploadStatus.innerHTML = "🔄 Uploading...";
            fetch("/upload-file", {
                method: "POST",
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                console.log("Upload response:", data); // Debugging log
                if (data.fileUrl) {
                    uploadedFileUrl = data.fileUrl; // Store the uploaded file URL
                    uploadStatus.innerHTML = `File uploaded successfully! <br> <a href="${uploadedFileUrl}" target="_blank">View File</a>`;
                    resolve(uploadedFileUrl);
                } else {
                    uploadStatus.innerHTML = "Upload failed!";
                    reject("Upload failed");
                }
            })
            .catch(error => {
                console.error("Upload error:", error);
                uploadStatus.innerHTML = "Upload failed!";
                reject(error);
            });
        });
    }

    // Ensure file is uploaded before submitting the form
    bookingForm.addEventListener("submit", async function (event) {
        event.preventDefault(); // Prevent default form submission

        if (uploadInput.files.length > 0) {
            try {
                uploadedFileUrl = await uploadFile(uploadInput.files[0]);
            } catch (error) {
                console.error("Upload Error:", error);
                return;
            }
        }

        if (!uploadedFileUrl) {
            uploadStatus.innerHTML = "⚠ Please upload a file before submitting.";
            return;
        }

        let formData = new FormData(bookingForm);
        formData.append("fileUrl", uploadedFileUrl); // Attach uploaded file URL

        console.log("Submitting form with fileUrl:", uploadedFileUrl); // Debugging log

        fetch(bookingForm.action, {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log("Booking response:", data); // Debugging log
            if (data.bookingId) {
                alert("Booking confirmed! Your ID: " + data.bookingId);
                bookingForm.reset();
                uploadStatus.innerHTML = "";
                uploadedFileUrl = null; // Reset file URL
            } else {
                alert(" Booking failed! Please try again.");
            }
        })
        .catch(error => {
            console.error("Booking error:", error);
            alert(" Booking failed! Please try again.");
        });
    });
});
