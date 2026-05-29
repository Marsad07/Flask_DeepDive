function confirmKitchenAction(orderId, message) {
        document.getElementById("modal-title").innerText = "Confirm Action";
        document.getElementById("modal-message").innerText = message;
        document.getElementById("modal-confirm-btn").onclick = function() {
            document.getElementById(`kitchen-form-${orderId}`).submit();
        };
        document.getElementById("confirm-modal").classList.add("open");
    }

    function closeModal() {
        document.getElementById("confirm-modal").classList.remove("open");
    }

    document.getElementById("confirm-modal").addEventListener("click", function(e) {
        if (e.target === this) closeModal();
    });

    function toggleItems(id) {
        const list = document.getElementById(id);
        list.style.display = list.style.display === "none" ? "block" : "none";
    }

    const socket = io();
    socket.on('connect', function() {
        socket.emit('join_kitchen');
    });

    if (!sessionStorage.getItem('audioUnlocked')) {
        sessionStorage.setItem('audioUnlocked', 'false');
    }

    document.addEventListener('click', function() {
        sessionStorage.setItem('audioUnlocked', 'true');
    });

    function playOrderAlert() {
        if (sessionStorage.getItem('audioUnlocked') !== 'true') return;
        const audio = new Audio('/static/sounds/sound1.mp3');
        audio.play().catch(err => console.log('Audio error:', err));
    }

    socket.on('new_order', function() {
        playOrderAlert();
        setTimeout(() => location.reload(), 1500);
    });

    socket.on('kitchen_update', function(data) {
        if (data.new_status === 'confirmed') playOrderAlert();
        setTimeout(() => location.reload(), 1500);
    });

    function updateTimers() {
        const now = new Date();
        document.querySelectorAll('.order-timer').forEach(timer => {
            const created = new Date(timer.getAttribute('data-created'));
            const diffMs = now - created;
            const diffMins = Math.floor(diffMs / 60000);
            const diffSecs = Math.floor((diffMs % 60000) / 1000);

            timer.classList.remove('warning', 'urgent');
            if (diffMins >= 15) timer.classList.add('urgent');
            else if (diffMins >= 10) timer.classList.add('warning');

            timer.textContent = diffMins > 0
                ? `${diffMins}m ${diffSecs}s`
                : `${diffSecs}s`;
        });
    }

    updateTimers();
    setInterval(updateTimers, 1000);