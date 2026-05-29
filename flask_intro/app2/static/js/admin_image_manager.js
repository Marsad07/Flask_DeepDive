    // This opens the confirmation modal for image uploads
    function confirmImageUpload(key) {
        document.getElementById("modal-title").innerText = "Upload Image";
        document.getElementById("modal-message").innerText =
            "Are you sure you want to upload this image? It will replace the current one.";

        const confirmBtn = document.getElementById("modal-confirm-btn");
        confirmBtn.onclick = function () {
            document.getElementById(`form-${key}`).submit();
        };

        document.getElementById("confirm-modal").classList.add("open");
    }

    // This closes the modal
    function closeModal() {
        document.getElementById("confirm-modal").classList.remove("open");
    }

    // Close modal when clicking outside the box
    document.getElementById("confirm-modal").addEventListener("click", function(e) {
        if (e.target === this) closeModal();
    });