    const socket = io();

    socket.on("connect", () => {
        socket.emit("join_admin");
    });

    // This is for the admin notification when driver responds
    socket.on("driver_response_update", function(data) {
        const toast = document.getElementById("admin-toast");
        const text  = document.getElementById("admin-toast-text");

        if (data.accepted === true || data.accepted === "true") {
            text.textContent = "✓ Driver accepted order #" + data.order_id;
        } else {
            text.textContent = "✗ Driver declined order #" + data.order_id;
        }

        toast.classList.add("show");
        setTimeout(() => toast.classList.remove("show"), 5000);
    });

    // This shows the driver warning modal
    function showDriverWarning(message) {
        document.getElementById("driver-warning-text").textContent = message;
        document.getElementById("driver-warning-modal").classList.add("open");
    }

    // This closes the driver warning modal
    function closeDriverWarning() {
        document.getElementById("driver-warning-modal").classList.remove("open");
    }

    document.getElementById("driver-warning-modal").addEventListener("click", function(e) {
        if (e.target === this) closeDriverWarning();
    });

    // This shows/hides the partial amount input depending on refund type selection
    function togglePartial(radio) {
        document.getElementById('partial-amount-row').style.display =
            radio.value === 'partial' ? 'block' : 'none';
    }

    // This stores the pending refund order id while the modal is open
    let pendingRefundOrderId = null;

    // This validates the form and opens the refund confirmation modal
    function openRefundModal(orderId) {
        const type    = document.querySelector('input[name="refund_type"]:checked').value;
        const partial = document.getElementById('partial_amount').value;

        if (type === 'partial' && (!partial || parseFloat(partial) <= 0)) {
            alert('Please enter a valid refund amount.');
            return;
        }

        pendingRefundOrderId = orderId;

        const message = type === 'full'
            ? 'Issue a full refund for this order?'
            : `Issue a partial refund of £${parseFloat(partial).toFixed(2)} for this order?`;

        document.getElementById('refund-modal-message').textContent = message;
        document.getElementById('refund-modal-confirm-btn').disabled    = false;
        document.getElementById('refund-modal-confirm-btn').textContent = 'Yes, Refund';
        document.getElementById('refund-modal').classList.add('open');
    }

    // This closes the refund modal without doing anything
    function closeRefundModal() {
        document.getElementById('refund-modal').classList.remove('open');
        pendingRefundOrderId = null;
    }

    // This closes the modal when clicking the backdrop
    document.getElementById('refund-modal').addEventListener('click', function(e) {
        if (e.target === this) closeRefundModal();
    });

    // This fires after the admin confirms in the modal — calls the refund endpoint
    function executeRefund() {
        const type       = document.querySelector('input[name="refund_type"]:checked').value;
        const partial    = document.getElementById('partial_amount').value;
        const btn        = document.getElementById('refund-submit-btn');
        const spinner    = document.getElementById('refund-spinner');
        const confirmBtn = document.getElementById('refund-modal-confirm-btn');

        confirmBtn.disabled    = true;
        confirmBtn.textContent = 'Processing...';

        const body = new FormData();
        body.append('refund_type', type);
        if (type === 'partial') body.append('partial_amount', partial);

        fetch(`/admin/order/${pendingRefundOrderId}/refund`, { method: 'POST', body })
            .then(r => r.json())
            .then(data => {
                closeRefundModal();
                if (data.success) {
                    // Reload the page to show the confirmed refund banner
                    location.reload();
                } else {
                    alert('Refund failed: ' + data.message);
                    btn.disabled          = false;
                    spinner.style.display = 'none';
                }
            })
            .catch(() => {
                closeRefundModal();
                alert('Network error — please try again.');
                btn.disabled          = false;
                spinner.style.display = 'none';
            });
    }