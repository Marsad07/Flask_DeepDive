    const socket  = io();
    const orderId = "{{ order.order_id }}";

    socket.emit('join_order', { order_id: orderId });

    socket.on('order_status_update', function(data) {
        if (data.order_id == orderId) {
            updateProgressBar(data.new_status);
            if (data.estimated_minutes) {
                startCountdown(parseInt(data.estimated_minutes));
            }
            {% if order.order_type == 'collection' %}
            updateCollectionHero(data.new_status);
            {% endif %}
        }
    });

    function updateProgressBar(newStatus) {
        const stages = ['pending', 'confirmed', 'preparing', 'ready', 'completed'];
        const currentIndex = stages.indexOf(newStatus);
        const circles = document.querySelectorAll('.status-circle');
        const lines   = document.querySelectorAll('.status-line');
        const labels  = document.querySelectorAll('.status-label');

        circles.forEach((circle, i) => {
            circle.classList.toggle('active',  i <= currentIndex);
            circle.classList.toggle('current', i === currentIndex);
            labels[i].classList.toggle('active', i <= currentIndex);
        });

        lines.forEach((line, i) => {
            line.classList.toggle('active', i < currentIndex);
        });

        const statusText = document.getElementById('order-status-text');
        if (statusText) {
            statusText.textContent =
                newStatus.charAt(0).toUpperCase() + newStatus.slice(1);
        }

        showNotification(newStatus);
    }

    // This updates the collection hero block when a status change arrives via SocketIO
    function updateCollectionHero(newStatus) {
        const heroMessages = {
            'pending':   { icon: '📋', text: "We've received your order" },
            'confirmed': { icon: '✅', text: 'Order confirmed!' },
            'preparing': { icon: '👨‍🍳', text: 'Being prepared in the kitchen' },
            'ready':     { icon: '🍽️', text: 'Ready for collection!' },
            'completed': { icon: '🎉', text: 'Order complete — enjoy!' }
        };
        const hero = heroMessages[newStatus];
        if (!hero) return;

        const heroEl   = document.querySelector('.track-collection-hero');
        const iconEl   = document.querySelector('.track-collection-hero-icon');
        const statusEl = document.getElementById('collection-status-text');

        if (heroEl) {
            // Remove all status-hero-* classes then apply the new one
            heroEl.className = heroEl.className.replace(/status-hero-\S+/, '');
            heroEl.classList.add(`status-hero-${newStatus}`);
        }
        if (iconEl)   iconEl.textContent   = hero.icon;
        if (statusEl) statusEl.textContent = hero.text;
    }

    function showNotification(status) {
        const messages = {
            'confirmed': '✅ Your order has been confirmed!',
            'preparing': '👨‍🍳 Your order is being prepared!',
            'ready':     '🍽️ Your order is ready for collection!',
            'completed': '🎉 Order completed. Enjoy your meal!'
        };
        const msg = messages[status];
        if (!msg) return;

        const toast = document.createElement('div');
        toast.textContent = msg;
        toast.className   = 'track-toast';
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }

    let countdownInterval = null;
    function startCountdown(minutes) {
        if (countdownInterval) clearInterval(countdownInterval);
        let totalSeconds = minutes * 60;
        const display    = document.getElementById('countdown-display');
        if (!display) return;

        countdownInterval = setInterval(function() {
            if (totalSeconds <= 0) {
                clearInterval(countdownInterval);
                display.textContent = 'Any moment now!';
                return;
            }
            const mins = Math.floor(totalSeconds / 60);
            const secs = totalSeconds % 60;
            display.textContent =
                mins + 'm ' + (secs < 10 ? '0' : '') + secs + 's remaining';
            totalSeconds--;
        }, 1000);
    }

    {% if order.order_type == 'delivery' %}
    // This is the live driver marker updated via SocketIO
    let driverMarker = null;

    socket.on('driver_moved', function(data) {
        const latlng = [data.lat, data.lng];
        if (driverMarker) {
            animateMarker(driverMarker, latlng);
        } else {
            driverMarker = L.marker(latlng, {
                icon: L.divIcon({
                    className: '',
                    html:      '<div style="font-size:28px;">🚗</div>',
                    iconSize:  [32, 32],
                    iconAnchor:[16, 16]
                })
            }).addTo(map).bindPopup('🚗 Your Driver');
        }
    });

    // This smoothly animates the driver marker between GPS updates
    function animateMarker(marker, newLatLng) {
        const startLatLng = marker.getLatLng();
        const startLat    = startLatLng.lat;
        const startLng    = startLatLng.lng;
        const endLat      = newLatLng[0];
        const endLng      = newLatLng[1];
        const duration    = 1000;
        const startTime   = performance.now();

        function step(currentTime) {
            const elapsed  = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const lat = startLat + (endLat - startLat) * progress;
            const lng = startLng + (endLng - startLng) * progress;
            marker.setLatLng([lat, lng]);
            if (progress < 1) requestAnimationFrame(step);
        }

        requestAnimationFrame(step);
    }

    document.addEventListener('DOMContentLoaded', function () {
        const mapEl = document.getElementById('order-map');
        if (!mapEl) return;

        {% if restaurant and restaurant.latitude and restaurant.longitude %}
            mapEl.innerHTML = '';
            mapEl.style.display = 'block';

            const map = L.map('order-map').setView(
                [{{ restaurant.latitude }}, {{ restaurant.longitude }}], 14
            );

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);

            L.marker([{{ restaurant.latitude }}, {{ restaurant.longitude }}])
                .addTo(map)
                .bindPopup('📍 Restaurant')
                .openPopup();

            {% if order.order_type == 'delivery' and route_coords %}
                const routeCoords = {{ route_coords | tojson }};
                L.polyline(routeCoords, {
                    color: '#8B0000', weight: 4, opacity: 0.8
                }).addTo(map);

                L.marker([{{ customer_lat }}, {{ customer_lng }}])
                    .addTo(map)
                    .bindPopup('🏠 Delivery Address');

                map.fitBounds(
                    L.latLngBounds(routeCoords), { padding: [30, 30] }
                );
            {% endif %}

        {% else %}
            mapEl.innerHTML =
                '<p style="padding:20px; color:var(--color-primary);' +
                'font-family:var(--font-body);">' +
                '⚠ Map unavailable — restaurant location not configured.</p>';
            mapEl.style.background = 'var(--color-bg)';
            mapEl.style.display    = 'flex';
        {% endif %}
    });
    {% endif %}

    // This builds and downloads the receipt as an HTML file
    function downloadReceipt() {
        const restaurantName       = "{{ branding.restaurant_name }}";
        const orderNumber          = "{{ order_number }}";
        const orderType            = "{{ order.order_type | capitalize }}";
        const orderStatus          = "{{ order.order_status | capitalize }}";
        const paymentMethod        =
            "{{ order.payment_method | replace('_', ' ') | capitalize }}";
        const paymentStatus        = "{{ order.payment_status | capitalize }}";
        const orderDate            =
            "{{ order.created_at.strftime('%d %B %Y at %H:%M') if order.created_at else '' }}";
        const deliveryAddress      = "{{ order.guest_delivery_address or '' }}";
        const specialInstructions  = "{{ order.special_instructions or '' }}";
        const couponCode           = "{{ order.coupon_code or '' }}";
        const discountAmount       =
            parseFloat("{{ order.discount_amount or 0 }}");
        const total                = parseFloat("{{ order.total_price }}");

        const items = [
            {% for item in items %}
            {
                name:     "{{ item.item_name | replace('"', '\\"') }}",
                qty:      {{ item.quantity }},
                subtotal: {{ "%.2f" % (item.item_price|float * item.quantity|int) }}
            },
            {% endfor %}
        ];

        const now       = new Date();
        const printDate = now.toLocaleDateString('en-GB', {
            day: '2-digit', month: 'long', year: 'numeric'
        }) + ' ' + now.toLocaleTimeString('en-GB', {
            hour: '2-digit', minute: '2-digit'
        });

        // This builds the items rows for the receipt
        let itemsHtml = '';
        items.forEach(item => {
            itemsHtml += `
                <tr>
                    <td style="padding:8px 0;border-bottom:1px dashed #ddd;
                               font-size:13px;color:#333;">
                        ${item.name}
                    </td>
                    <td style="padding:8px 0;border-bottom:1px dashed #ddd;
                               font-size:13px;color:#333;text-align:center;">
                        x${item.qty}
                    </td>
                    <td style="padding:8px 0;border-bottom:1px dashed #ddd;
                               font-size:13px;color:#333;text-align:right;">
                        £${item.subtotal}
                    </td>
                </tr>`;
        });

        // This builds the discount row if a coupon was applied
        let discountHtml = '';
        if (discountAmount > 0) {
            discountHtml = `
                <tr>
                    <td colspan="2" style="padding:6px 0;font-size:13px;color:#28a745;">
                        Discount${couponCode ? ' (' + couponCode + ')' : ''}
                    </td>
                    <td style="padding:6px 0;font-size:13px;
                               color:#28a745;text-align:right;">
                        -£${discountAmount.toFixed(2)}
                    </td>
                </tr>`;
        }

        // This builds the delivery address row if applicable
        let deliveryHtml = '';
        if (orderType.toLowerCase() === 'delivery' && deliveryAddress) {
            deliveryHtml = `
                <tr>
                    <td style="padding:4px 0;font-size:12px;color:#666;">
                        Delivering to:
                    </td>
                    <td colspan="2" style="padding:4px 0;font-size:12px;
                                          color:#333;text-align:right;">
                        ${deliveryAddress}
                    </td>
                </tr>`;
        }

        // This builds the special instructions row if any were provided
        let notesHtml = '';
        if (specialInstructions) {
            notesHtml = `
                <p style="margin:8px 0 0;font-size:12px;color:#666;
                          font-style:italic;border-top:1px dashed #ddd;
                          padding-top:8px;">
                    Notes: ${specialInstructions}
                </p>`;
        }

        // This is the full receipt HTML that gets downloaded
        const receiptHtml = `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Receipt - ${orderNumber}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Courier New', Courier, monospace;
            background: #f5f5f5;
            display: flex;
            justify-content: center;
            padding: 40px 20px;
        }
        .receipt {
            background: white;
            width: 340px;
            padding: 32px 28px;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
        }
        .receipt-logo {
            text-align: center;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 2px dashed #ccc;
        }
        .receipt-logo h1 {
            font-family: Georgia, serif;
            font-size: 22px;
            font-weight: 700;
            color: #1C1008;
            letter-spacing: 3px;
            margin-bottom: 4px;
        }
        .receipt-logo p { font-size: 11px; color: #999; letter-spacing: 1px; }
        .receipt-ref {
            text-align: center;
            background: #1C1008;
            color: #D4AF37;
            padding: 10px;
            margin-bottom: 20px;
            letter-spacing: 2px;
            font-size: 14px;
            font-weight: 700;
        }
        .receipt-meta {
            margin-bottom: 16px;
            padding-bottom: 16px;
            border-bottom: 1px dashed #ddd;
        }
        .receipt-meta table { width: 100%; font-size: 12px; }
        .receipt-meta td { padding: 3px 0; color: #666; }
        .receipt-meta td:last-child {
            text-align: right; color: #333; font-weight: 600;
        }
        .receipt-items { margin-bottom: 16px; }
        .receipt-items h3 {
            font-size: 11px;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: #999;
            margin-bottom: 10px;
        }
        .receipt-total {
            border-top: 2px dashed #ccc;
            padding-top: 12px;
            margin-top: 8px;
        }
        .receipt-total table { width: 100%; }
        .grand-total td {
            font-size: 16px;
            font-weight: 700;
            color: #8B0000;
            padding-top: 8px;
        }
        .receipt-footer {
            text-align: center;
            margin-top: 24px;
            padding-top: 16px;
            border-top: 2px dashed #ccc;
            font-size: 11px;
            color: #999;
            line-height: 1.8;
        }
        .receipt-footer strong {
            display: block;
            font-size: 13px;
            color: #333;
            margin-bottom: 4px;
        }
        @media print {
            body { background: white; padding: 0; }
            .receipt { box-shadow: none; }
        }
    </style>
</head>
<body>
<div class="receipt">
    <div class="receipt-logo">
        <h1>${restaurantName}</h1>
        <p>ORDER RECEIPT</p>
        <p style="margin-top:4px;font-size:10px;">Printed: ${printDate}</p>
    </div>
    <div class="receipt-ref">${orderNumber}</div>
    <div class="receipt-meta">
        <table>
            <tr><td>Order Date</td><td>${orderDate}</td></tr>
            <tr><td>Order Type</td><td>${orderType}</td></tr>
            <tr><td>Status</td><td>${orderStatus}</td></tr>
            <tr><td>Payment</td><td>${paymentMethod}</td></tr>
            <tr><td>Payment Status</td><td>${paymentStatus}</td></tr>
            ${deliveryHtml}
        </table>
        ${notesHtml}
    </div>
    <div class="receipt-items">
        <h3>Items Ordered</h3>
        <table style="width:100%;">
            <thead>
                <tr>
                    <th style="font-size:11px;color:#999;font-weight:400;
                               text-align:left;padding-bottom:6px;">Item</th>
                    <th style="font-size:11px;color:#999;font-weight:400;
                               text-align:center;padding-bottom:6px;">Qty</th>
                    <th style="font-size:11px;color:#999;font-weight:400;
                               text-align:right;padding-bottom:6px;">Price</th>
                </tr>
            </thead>
            <tbody>${itemsHtml}</tbody>
        </table>
    </div>
    <div class="receipt-total">
        <table>
            ${discountHtml}
            <tr class="grand-total">
                <td colspan="2">TOTAL</td>
                <td style="text-align:right;">£${total.toFixed(2)}</td>
            </tr>
        </table>
    </div>
    <div class="receipt-footer">
        <strong>Thank you for your order!</strong>
        We hope you enjoy your meal.
        <br>Please keep this receipt for your records.
    </div>
</div>
</body>
</html>`;

        // This downloads the receipt as a file rather than opening a new tab
        const blob = new Blob([receiptHtml], { type: 'text/html' });
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = `receipt-${orderNumber}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }