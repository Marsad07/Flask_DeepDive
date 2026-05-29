const socket = io();
    socket.emit("join_driver", { driver_id: {{ driver_id }} });

    let currentOfferOrderId = null;

    const titles = {
        pickup: 'Mark as Out for Delivery',
        delivered: 'Mark as Delivered',
        accept: 'Accept Delivery'
    };

    const messages = {
        pickup: 'Confirm you have picked up this order and are heading to the customer?',
        delivered: 'Confirm this order has been successfully delivered?',
        accept: 'Accept this delivery request?'
    };

    function showConfirm(type, orderId) {
        document.getElementById('confirm-title').textContent = titles[type];
        document.getElementById('confirm-message').textContent = messages[type];
        document.getElementById('confirm-modal').classList.add('open');

        document.getElementById('confirm-yes').onclick = function() {
            closeConfirm();
            if (type === 'pickup') {
                document.getElementById('pickup-form-' + orderId).submit();
            } else if (type === 'delivered') {
                document.getElementById('delivered-form-' + orderId).submit();
            } else if (type === 'accept') {
                socket.emit("driver_response", { order_id: orderId, accepted: true });
            }
        };
    }

    function closeConfirm() {
        document.getElementById('confirm-modal').classList.remove('open');
    }

    document.getElementById('confirm-modal').addEventListener('click', function(e) {
        if (e.target === this) closeConfirm();
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') closeConfirm();
    });

    socket.on("driver_offer", function(data) {
        const sound = document.getElementById("offer-sound");
        if (sound) {
            sound.muted = false;
            sound.volume = 1;
            sound.currentTime = 0;
            sound.play().catch(err => console.log("Autoplay blocked:", err));
        }

        currentOfferOrderId = data.order_id;
        document.getElementById("toast-customer").textContent = "Customer: " + data.customer_name;
        document.getElementById("toast-address").textContent = "Address: " + data.address;
        document.getElementById("toast-total").textContent = "Total: £" + data.total_price;

        const toast = document.getElementById("offer-toast");
        toast.style.display = "block";
        setTimeout(() => { toast.style.display = "none"; }, 10000);
    });

    {% for order in orders %}
        socket.emit('join_order', { order_id: {{ order.order_id }} });
    {% endfor %}

    document.getElementById("toast-accept").onclick = function() {
        if (!currentOfferOrderId) return;
        document.getElementById("offer-toast").style.display = "none";
        showConfirm('accept', currentOfferOrderId);
    };

    document.getElementById("toast-decline").onclick = function() {
        if (!currentOfferOrderId) return;
        socket.emit("driver_response", { order_id: currentOfferOrderId, accepted: false });
        document.getElementById("offer-toast").style.display = "none";
    };

    // This sends the driver's live GPS location every 10 seconds
    function startLocationTracking() {
        if (!navigator.geolocation) return;

        navigator.geolocation.watchPosition(function(position) {
            socket.emit('driver_location_update', {
                order_id: currentOrderId,
                lat: position.coords.latitude,
                lng: position.coords.longitude
            });
        }, function(err) {
            console.log('GPS error:', err);
        }, {
            enableHighAccuracy: true,
            maximumAge: 5000,
            timeout: 10000
        });
    }

    // Start tracking when an order is out for delivery
    {% for order in orders %}
    {% if order.status == 'out_for_delivery' %}
    const currentOrderId = {{ order.order_id }};
    startLocationTracking();
    {% endif %}
    {% endfor %}