// Generic close modal
    function closeModal(id) {
        document.getElementById(id).classList.remove('open');
    }

    // Generic open modal
    function openModal(id) {
        document.getElementById(id).classList.add('open');
    }

    // Close on backdrop click
    document.querySelectorAll('.modal-overlay').forEach(function(modal) {
        modal.addEventListener('click', function(e) {
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

    // Add table confirmation
    function confirmAddTable() {
        const form = document.querySelector('form[action="{{ url_for("admin.add_table") }}"]');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        document.getElementById('add-table-confirm-btn').onclick = function() {
            form.submit();
        };
        openModal('add-table-modal');
    }

    // Save layout confirmation
    function confirmSaveLayout() {
        openModal('save-layout-modal');
    }

    // Drag and drop
    const canvas = document.getElementById('layout-canvas');
    let dragging = null;
    let offsetX = 0;
    let offsetY = 0;

    document.querySelectorAll('.draggable-table').forEach(function(el) {
        el.addEventListener('mousedown', function(e) {
            dragging = this;
            dragging.style.cursor = 'grabbing';
            dragging.style.zIndex = 1000;
            const rect = dragging.getBoundingClientRect();
            offsetX = e.clientX - rect.left;
            offsetY = e.clientY - rect.top;
            e.preventDefault();
        });

        el.addEventListener('touchstart', function(e) {
            dragging = this;
            dragging.style.zIndex = 1000;
            const touch = e.touches[0];
            const rect = dragging.getBoundingClientRect();
            offsetX = touch.clientX - rect.left;
            offsetY = touch.clientY - rect.top;
            e.preventDefault();
        }, { passive: false });
    });

    document.addEventListener('mousemove', function(e) {
        if (!dragging) return;
        moveTable(e.clientX, e.clientY);
    });

    document.addEventListener('touchmove', function(e) {
        if (!dragging) return;
        moveTable(e.touches[0].clientX, e.touches[0].clientY);
        e.preventDefault();
    }, { passive: false });

    function moveTable(clientX, clientY) {
        const canvasRect = canvas.getBoundingClientRect();
        let x = clientX - canvasRect.left - offsetX;
        let y = clientY - canvasRect.top - offsetY;
        x = Math.max(0, Math.min(x, canvasRect.width - 80));
        y = Math.max(0, Math.min(y, canvasRect.height - 80));
        dragging.style.left = x + 'px';
        dragging.style.top  = y + 'px';
    }

    document.addEventListener('mouseup', function() {
        if (dragging) {
            dragging.style.cursor = 'grab';
            dragging.style.zIndex = '';
            dragging = null;
        }
    });

    document.addEventListener('touchend', function() {
        if (dragging) {
            dragging.style.zIndex = '';
            dragging = null;
        }
    });

    // Save positions
    function savePositions() {
        closeModal('save-layout-modal');

        const positions = [];
        document.querySelectorAll('.draggable-table').forEach(function(t) {
            const x = t.style.left ? parseInt(t.style.left) : t.offsetLeft;
            const y = t.style.top  ? parseInt(t.style.top)  : t.offsetTop;
            positions.push({
                id: parseInt(t.dataset.id),
                x: isNaN(x) ? 0 : x,
                y: isNaN(y) ? 0 : y
            });
        });

        const saveBtn = document.querySelector('button[onclick="confirmSaveLayout()"]');
        if (saveBtn) { saveBtn.textContent = 'Saving...'; saveBtn.disabled = true; }

        fetch('{{ url_for("admin.save_table_positions") }}', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ positions: positions })
        })
        .then(function(r) {
            if (!r.ok) return r.text().then(function(txt) { throw new Error('Server error ' + r.status + ': ' + txt); });
            return r.json();
        })
        .then(function(data) {
            if (data.success) {
                openModal('save-success-modal');
            } else {
                alert('Save failed: ' + (data.message || 'Unknown error'));
            }
        })
        .catch(function(err) {
            alert('Could not save layout.\n\n' + err.message);
        })
        .finally(function() {
            if (saveBtn) { saveBtn.textContent = 'Save Layout'; saveBtn.disabled = false; }
        });
    }

    // Edit table modal
    function openEditTable(id, seats, location, shape, isActive) {
        document.getElementById('edit-seats').value    = seats;
        document.getElementById('edit-location').value = location;
        document.getElementById('edit-shape').value    = shape;
        document.getElementById('edit-active').value   = isActive;
        document.getElementById('edit-table-form').action = '/admin/tables/update/' + id;
        openModal('edit-table-modal');
    }

    function confirmEditTable() {
        closeModal('edit-table-modal');
        document.getElementById('edit-confirm-btn').onclick = function() {
            document.getElementById('edit-table-form').submit();
        };
        openModal('edit-confirm-modal');
    }

    // Delete confirmation
    function showDeleteConfirm(id, tableNum) {
        document.getElementById('delete-modal-msg').textContent =
            'Are you sure you want to remove Table ' + tableNum + '? This cannot be undone.';
        document.getElementById('delete-confirm-btn').onclick = function() {
            document.getElementById('delete-table-' + id).submit();
        };
        openModal('delete-modal');
    }