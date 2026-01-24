(function () {
  function typeText(el, fullText, speed) {
    el.textContent = "";
    el.classList.add("atlas-typing-cursor");

    let i = 0;
    const timer = setInterval(() => {
      i++;
      el.textContent = fullText.slice(0, i);
      el.scrollIntoView({ block: "end" });

      if (i >= fullText.length) {
        clearInterval(timer);
        el.classList.remove("atlas-typing-cursor");
      }
    }, speed);
  }

  window.addEventListener("DOMContentLoaded", () => {
    const msgs = document.querySelectorAll(".atlas-typing-target");
    if (!msgs.length) return;

    const last = msgs[msgs.length - 1];

    const alreadyTyped = last.dataset.typed === "1";
    if (alreadyTyped) return;

    const fullText = last.textContent;
    last.dataset.typed = "1";

    const speed = fullText.length > 600 ? 4 : 12;
    typeText(last, fullText, speed);
  });
})();
