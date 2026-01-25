(function () {
  const overlay = document.getElementById("atlas-loading");
  const statusEl = document.getElementById("atlas-loading-status");
  const detailEl = document.getElementById("atlas-loading-detail");
  const pctEl = document.getElementById("atlas-loading-percent");

  if (!overlay) return;

  let pctTimer = null;
  let pctValue = 0;

  function stopPercent() {
    if (pctTimer) clearInterval(pctTimer);
    pctTimer = null;
  }

  function startPercent() {
    stopPercent();
    pctValue = 0;
    if (pctEl) pctEl.textContent = "0%";

    pctTimer = setInterval(() => {
      if (pctValue < 92) {
        pctValue += Math.max(1, Math.round((92 - pctValue) * 0.08));
        if (pctEl) pctEl.textContent = pctValue + "%";
      }
    }, 120);
  }

  function finishPercent() {
    stopPercent();
    pctValue = 100;
    if (pctEl) pctEl.textContent = "100%";
  }

  function show(status, detail) {
    if (statusEl) statusEl.textContent = status || "Processing…";
    if (detailEl) detailEl.textContent = detail || "Atlas AI is thinking";

    document.body.classList.add("atlas-busy");

    overlay.classList.remove("is-on");
    overlay.offsetHeight;
    overlay.classList.add("is-on");

    startPercent();
  }

  function hide() {
    overlay.classList.remove("is-on");
    document.body.classList.remove("atlas-busy");
    stopPercent();
  }

  function hideSoon() {
    finishPercent();
    setTimeout(hide, 120);
  }

  window.addEventListener("pageshow", hideSoon);
  document.addEventListener("DOMContentLoaded", hideSoon);

  document.addEventListener(
    "submit",
    (e) => {
      const form = e.target;
      if (!form) return;
      if (!form.classList.contains("atlas-form")) return;

      const textarea = form.querySelector("textarea[name='message']");
      const fileInput = form.querySelector("input[type='file']");
      const sendBtn = form.querySelector(".atlas-sendbtn");

      const text = textarea ? textarea.value.trim().toLowerCase() : "";
      const hasFile = !!(fileInput && fileInput.files && fileInput.files.length > 0);

      const HEAVY_KEYWORDS = [
        "summarise","summarize","explain","notes","study",
        "flashcards","practice","questions","revise",
        "analyze","analyse","generate","quiz","test"
      ];

      const isHeavy =
        hasFile ||
        text.length > 80 ||
        HEAVY_KEYWORDS.some((k) => text.includes(k));

      if (sendBtn) {
        sendBtn.disabled = true;
        sendBtn.style.opacity = "0.7";
        sendBtn.style.cursor = "not-allowed";
      }

      if (isHeavy) show("Generating response…", "Running model inference");
    },
    true
  );
})();
