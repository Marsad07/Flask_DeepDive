    function positionTables() {
        const canvas = document.getElementById('table-canvas');
        const w = canvas.offsetWidth;
        const h = canvas.offsetHeight;
        document.querySelectorAll('.table-item').forEach(el => {
            el.style.left = (parseFloat(el.dataset.px) / w * 100) + '%';
            el.style.top  = (parseFloat(el.dataset.py) / h * 100) + '%';
        });
    }

    positionTables();
    window.addEventListener('resize', positionTables);

    const tables       = document.querySelectorAll('.table-item');
    const tableInput   = document.getElementById('table_num');
    const guestsSelect = document.getElementById('guests_num');
    const tableError   = document.getElementById('table-error');

    const bookedSlots = {{ booked_slots | tojson }}.map(s => ({
        table_num: String(s.table_num),
        date: s.date,
        time: s.time
    }));

    function refreshTableAvailability() {
        const selectedDate = document.getElementById('resv_date').value;
        const selectedTime = document.getElementById('resv_time').value;
        const guests = parseInt(guestsSelect.value) || 0;

        tables.forEach(el => el.classList.remove('unavailable'));

        if (selectedDate && selectedTime) {
            bookedSlots.forEach(slot => {
                if (slot.date === selectedDate && slot.time === selectedTime) {
                    const el = document.querySelector(`.table-item[data-table="${slot.table_num}"]`);
                    if (el) {
                        el.classList.add('unavailable');
                        el.classList.remove('selected');
                        if (String(tableInput.value) === slot.table_num) tableInput.value = '';
                    }
                }
            });
        }

        if (guests > 0) {
            tables.forEach(t => {
                if (parseInt(t.dataset.seats) !== guests) {
                    t.classList.add('unavailable');
                    t.classList.remove('selected');
                    if (tableInput.value === t.dataset.table) tableInput.value = '';
                }
            });
        }
    }

    document.getElementById('resv_date').addEventListener('change', refreshTableAvailability);
    document.getElementById('resv_time').addEventListener('change', refreshTableAvailability);
    guestsSelect.addEventListener('change', function() {
        tableInput.value = '';
        refreshTableAvailability();
    });

    const socket = io();

    socket.on('tables_updated', (positions) => {
        positions.forEach(pos => {
            const el = document.querySelector(`.table-item[data-table="${pos.id}"]`);
            if (el) { el.dataset.px = pos.x; el.dataset.py = pos.y; }
        });
        positionTables();
    });

    socket.on('table_unavailable', (data) => {
        bookedSlots.push({ table_num: String(data.table_num), date: data.date, time: data.time });
        const selectedDate = document.getElementById('resv_date').value;
        const selectedTime = document.getElementById('resv_time').value;
        if (data.date === selectedDate && data.time === selectedTime) {
            const el = document.querySelector(`.table-item[data-table="${String(data.table_num)}"]`);
            if (el) {
                el.classList.add('unavailable');
                el.classList.remove('selected');
                if (String(tableInput.value) === String(data.table_num)) tableInput.value = '';
            }
        }
    });

    socket.on('table_available', (data) => {
        const idx = bookedSlots.findIndex(
            s => s.table_num === String(data.table_num) && s.date === data.date && s.time === data.time
        );
        if (idx !== -1) bookedSlots.splice(idx, 1);
        const selectedDate = document.getElementById('resv_date').value;
        const selectedTime = document.getElementById('resv_time').value;
        if (data.date === selectedDate && data.time === selectedTime) refreshTableAvailability();
    });

    tables.forEach(t => {
        t.addEventListener('click', function() {
            if (this.classList.contains('unavailable')) return;
            tables.forEach(x => x.classList.remove('selected'));
            this.classList.add('selected');
            tableInput.value = this.dataset.table;
            tableError.style.display = 'none';
        });
    });

    const modal = document.getElementById('reservation-confirm-modal');

    function showReservationConfirm() {
        if (!tableInput.value) {
            tableError.style.display = 'block';
            tableError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return;
        }
        modal.classList.add('open');
        document.body.style.overflow = 'hidden';
    }

    function showReservationConfirm() {
        // Validate all required fields before opening the modal
        const date    = document.getElementById('resv_date').value;
        const time    = document.getElementById('resv_time').value;
        const guests  = document.getElementById('guests_num').value;
        const name    = document.getElementById('fullname').value.trim();
        const email   = document.getElementById('email').value.trim();
        const phone   = document.getElementById('phoneNum').value.trim();

        if (!name || !email || !phone || !date || !time || !guests) {
            alert('Please fill in all fields before confirming.');
            return;
        }

        if (!tableInput.value) {
            tableError.style.display = 'block';
            tableError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return;
        }

        modal.classList.add('open');
        document.body.style.overflow = 'hidden';
    }