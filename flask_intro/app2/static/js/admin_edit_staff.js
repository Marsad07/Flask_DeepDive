    function closeModal(id) {
        document.getElementById(id).classList.remove('open');
    }

    function showSaveConfirm() {
        document.getElementById('save-modal').classList.add('open');
    }

    function showManualResetConfirm() {
        const newPass = document.getElementById('new-password-input').value;
        if (!newPass) {
            alert('Please enter a new password first.');
            return;
        }
        document.getElementById('manual-reset-modal').classList.add('open');
    }

    function showResetDefaultConfirm() {
        document.getElementById('reset-default-modal').classList.add('open');
    }

    function showResetEmailConfirm() {
        document.getElementById('reset-email-modal').classList.add('open');
    }

    function showDisableConfirm() {
        document.getElementById('disable-modal').classList.add('open');
    }

    function togglePasswordReveal() {
        const dots = document.getElementById('password-dots');
        const revealed = document.getElementById('password-revealed');
        const btn = document.querySelector('.edit-staff-reveal-btn');
        if (revealed.style.display === 'none') {
            dots.style.display = 'none';
            revealed.style.display = 'block';
            btn.textContent = '🙈 Hide';
        } else {
            dots.style.display = 'block';
            revealed.style.display = 'none';
            btn.textContent = '👁 Show';
        }
    }

    // Close modals on backdrop click
    document.querySelectorAll('.modal-overlay').forEach(function(m) {
        m.addEventListener('click', function(e) {
            if (e.target === this) this.classList.remove('open');
        });
    });

    // Close on Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay.open').forEach(function(m) {
                m.classList.remove('open');
            });
        }
    });

    // Auto hide toast
    const toast = document.getElementById('staff-toast');
    if (toast) {
        setTimeout(function() { toast.classList.remove('show'); }, 4000);
    }