    function closeModal(id) {
        document.getElementById(id).classList.remove('open');
    }

    function showConfirm(type) {
        if (type === 'password') {
            const currentPass = document.getElementById('current-pass').value;
            const newPass = document.getElementById('new-pass').value;
            const confirmPass = document.getElementById('confirm-pass').value;
            if (!currentPass) {
                alert('Please enter your current password.');
                return;
            }
            if (newPass.length < 8) {
                alert('Password must be at least 8 characters.');
                return;
            }
            if (newPass !== confirmPass) {
                alert('Passwords do not match.');
                return;
            }
        }
        document.getElementById(type + '-modal').classList.add('open');
    }

    // Toggle password eye
    function toggleEye(inputId, btn) {
        const input = document.getElementById(inputId);
        const icon = btn.querySelector('i');
        if (input.type === 'password') {
            input.type = 'text';
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        } else {
            input.type = 'password';
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
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

    // Password strength indicator
    document.getElementById('new-pass').addEventListener('input', function() {
        const val = this.value;
        const bar = document.getElementById('strength-bar');
        const label = document.getElementById('strength-label');
        let strength = 0;
        if (val.length >= 8) strength++;
        if (/[A-Z]/.test(val)) strength++;
        if (/[0-9]/.test(val)) strength++;
        if (/[^A-Za-z0-9]/.test(val)) strength++;

        const levels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
        const colors = ['', '#dc3545', '#ffc107', '#17a2b8', '#28a745'];
        const widths = ['0%', '25%', '50%', '75%', '100%'];

        bar.style.width = widths[strength];
        bar.style.background = colors[strength];
        label.textContent = strength > 0 ? levels[strength] : '';
        label.style.color = colors[strength];
    });

    // Auto hide toast
    const toast = document.getElementById('settings-toast');
    if (toast) {
        setTimeout(function() { toast.classList.remove('show'); }, 4000);
    }