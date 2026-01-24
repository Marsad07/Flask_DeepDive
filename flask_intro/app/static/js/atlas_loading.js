(function () {
  const overlay = document.getElementById("atlas-loading");
  const statusEl = document.getElementById("atlas-loading-status");
  const detailEl = document.getElementById("atlas-loading-detail");

  if (!overlay) return;

  function show(status, detail) {
    if (statusEl) statusEl.textContent = status || "Processing…";
    if (detailEl) detailEl.textContent = detail || "Atlas AI is thinking";

    document.body.classList.add("atlas-busy");
    overlay.classList.remove("is-on");
    overlay.offsetHeight;
    overlay.classList.add("is-on");
  }

  window.addEventListener("pageshow", () => {
    overlay.classList.remove("is-on");
    document.body.classList.remove("atlas-busy");
  });

  document.addEventListener("submit", (e) => {
    const form = e.target;
    if (!form) return;

    const action = (form.getAttribute("action") || "").toLowerCase();

    if (action.includes("/atlas/chat/send")) {
      const textarea = form.querySelector("textarea[name='message']");
      const fileInput = form.querySelector("input[type='file']");
      const text = textarea ? textarea.value.trim() : "";
      const hasFile = fileInput && fileInput.files && fileInput.files.length > 0;

      if (!text && !hasFile) return;

      const chatBox = document.getElementById("chat-box");
      if (chatBox) {
        const wrap = document.createElement("div");
        wrap.className = "atlas-msg atlas-thinking-msg";
        wrap.innerHTML = `
          <div class="atlas-role">Atlas:</div>
          <div class="atlas-content atlas-dots">Thinking</div>
        `;
        chatBox.appendChild(wrap);
        chatBox.scrollTop = chatBox.scrollHeight;
      }

      show("Generating response…", "Running model inference");
    }
  }, true);
})();
