(function () {
  const fileInput = document.getElementById("atlas-file");
  const chip = document.getElementById("atlas-file-chip");
  const fileName = document.getElementById("atlas-file-name");
  const removeBtn = document.getElementById("atlas-file-remove");

  if (!fileInput || !chip || !fileName || !removeBtn) return;

  function showChip(name) {
    fileName.textContent = name;
    chip.classList.remove("hidden");
  }

  function hideChip() {
    fileName.textContent = "";
    chip.classList.add("hidden");
  }

  fileInput.addEventListener("change", () => {
    const f = fileInput.files && fileInput.files[0];
    if (f) showChip(f.name);
    else hideChip();
  });

  removeBtn.addEventListener("click", () => {
    fileInput.value = "";
    hideChip();
  });
})();