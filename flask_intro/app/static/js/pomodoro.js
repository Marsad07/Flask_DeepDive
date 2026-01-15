let minutes = 25;
let seconds = 0;
let timerInterval = null;

const minutesDisplay = document.getElementById("minutes");
const secondsDisplay = document.getElementById("seconds");
const durationSelect = document.getElementById("duration");
const modeSelect = document.getElementById("mode");

function updateDisplay() {
    minutesDisplay.textContent = String(minutes).padStart(2, "0");
    secondsDisplay.textContent = String(seconds).padStart(2, "0");
}

modeSelect.addEventListener("change", () => {
    durationSelect.disabled = false;
    minutes = parseInt(durationSelect.value);
    seconds = 0;
    updateDisplay();
});

function startTimer() {
    if (timerInterval !== null) return;

    minutes = parseInt(durationSelect.value);
    seconds = 0;
    updateDisplay();

    timerInterval = setInterval(() => {
        if (seconds === 0) {
            if (minutes === 0) {
                clearInterval(timerInterval);
                timerInterval = null;
                return;
            }
            minutes--;
            seconds = 59;
        } else {
            seconds--;
        }
        updateDisplay();
    }, 1000);
}

function pauseTimer() {
    clearInterval(timerInterval);
    timerInterval = null;
}

function resetTimer() {
    clearInterval(timerInterval);
    timerInterval = null;
    minutes = parseInt(durationSelect.value);
    seconds = 0;
    updateDisplay();
}

document.getElementById("startBtn").addEventListener("click", startTimer);
document.getElementById("pauseBtn").addEventListener("click", pauseTimer);
document.getElementById("resetBtn").addEventListener("click", resetTimer);

updateDisplay();