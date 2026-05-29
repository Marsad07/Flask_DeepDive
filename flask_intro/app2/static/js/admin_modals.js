// ADD ITEM js
    function selectCategory(name, btn) {
        document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        document.getElementById('selected-category').value = name;
    }

    function showConfirm() {
        const name     = document.getElementById('item_name').value.trim();
        const category = document.getElementById('selected-category').value;
        const desc     = document.getElementById('description').value.trim();
        const price    = document.getElementById('price').value;

        if (!name) {
            alert('Please enter an item name.');
            return;
        }
        if (!category) {
            alert('Please select a category.');
            return;
        }
        if (!desc) {
            alert('Please enter a description.');
            return;
        }
        if (!price || parseFloat(price) < 0) {
            alert('Please enter a valid price.');
            return;
        }

        document.getElementById('confirm-modal').classList.add('open');
    }

    function closeConfirm() {
        document.getElementById('confirm-modal').classList.remove('open');
    }

    function submitForm() {
        document.getElementById('add-form').submit();
    }

    document.getElementById('confirm-modal').addEventListener('click', function (e) {
        if (e.target === this) closeConfirm();
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeConfirm();
    });

// COUPONS js
// Close modal helper
    function closeModal(id) {
        document.getElementById(id).classList.remove('open');
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

    // Update discount value label when type changes
    document.getElementById('discount-type-select').addEventListener('change', function() {
        const label = document.getElementById('discount-value-label');
        const input = document.getElementById('discount-value-input');
        if (this.value === 'percent') {
            label.textContent = 'Discount Value (%)';
            input.max = 100;
            input.placeholder = 'e.g. 10';
        } else {
            label.textContent = 'Discount Value (£)';
            input.removeAttribute('max');
            input.placeholder = 'e.g. 5.00';
        }
    });

    // Toggle specific email select visibility
    function toggleEmailSelect() {
        const sendTo = document.getElementById('send-to-select').value;
        const specificGroup = document.getElementById('specific-email-group');
        const bulkInfo = document.getElementById('bulk-send-info');
        const usesInput = document.getElementById('uses-limit-input');
        const preview = document.getElementById('recipient-preview');

        const isBulk = ['all_subscribers', 'all_customers', 'all_everyone'].includes(sendTo);
        const isSpecific = sendTo === 'one';

        specificGroup.style.display = isSpecific ? 'block' : 'none';
        bulkInfo.style.display = isBulk ? 'block' : 'none';

        if (isBulk) {
            usesInput.value = 1;
            usesInput.disabled = true;

            const labels = {
                all_subscribers: 'Will send to all newsletter subscribers',
                all_customers: 'Will send to all registered customers',
                all_everyone: 'Will send to all subscribers and customers'
            };
            preview.textContent = labels[sendTo] || '';
        } else {
            usesInput.disabled = false;
            preview.textContent = '';
        }
    }

    // Show create confirmation modal
    function showCreateConfirm() {
        const sendTo = document.getElementById('send-to-select').value;
        const discountType = document.getElementById('discount-type-select').value;
        const discountValue = document.getElementById('discount-value-input').value;
        const codeInput = document.querySelector('input[name="code"]').value;

        const discountText = discountType === 'percent'
            ? `${discountValue}% off`
            : `£${parseFloat(discountValue).toFixed(2)} off`;

        const sendLabels = {
            none: 'no email will be sent',
            all_subscribers: 'sent to all newsletter subscribers',
            all_customers: 'sent to all registered customers',
            all_everyone: 'sent to everyone (subscribers + customers)',
            one: 'sent to the selected recipient'
        };

        const codeText = codeInput
            ? `code <strong>${codeInput.toUpperCase()}</strong>`
            : 'an auto-generated code';

        document.getElementById('create-confirm-message').innerHTML =
            `Create ${codeText} for <strong>${discountText}</strong>? ` +
            `This coupon will be ${sendLabels[sendTo] || 'created'}.`;

        document.getElementById('create-confirm-modal').classList.add('open');
    }

    // Show delete confirmation modal
    function showDeleteConfirm(id, code) {
        document.getElementById('delete-confirm-message').textContent =
            `Are you sure you want to delete coupon ${code}? This cannot be undone.`;
        document.getElementById('delete-confirm-btn').onclick = function() {
            document.getElementById('delete-form-' + id).submit();
        };
        document.getElementById('delete-confirm-modal').classList.add('open');
    }

    // Filter coupons by status
    function filterCoupons(status, btn) {
        document.querySelectorAll('.coupon-filter-btn').forEach(function(b) {
            b.classList.remove('active');
        });
        btn.classList.add('active');

        document.querySelectorAll('.coupon-row').forEach(function(row) {
            if (status === 'all' || row.dataset.status === status) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    // Copy coupon code to clipboard
    function copyCode(code) {
        navigator.clipboard.writeText(code).then(function() {
            const toast = document.getElementById('copy-toast');
            toast.classList.add('show');
            setTimeout(function() { toast.classList.remove('show'); }, 2000);
        });
    }

// CREATE STAFF js
function showModal(title, message, onConfirm) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-message').textContent = message;
    document.getElementById('modal-confirm-btn').onclick = function() {
        closeModal();
        onConfirm();
    };
    document.getElementById('confirm-modal').style.display = 'flex';
}
function closeModal() {
    document.getElementById('confirm-modal').style.display = 'none';
}
document.getElementById('confirm-modal').addEventListener('click', function(e) {
    if (e.target === this) closeModal();
});

// EDIT CONTACT DETAILS js
  // This opens the confirmation modal
  function openConfirm() {
    document.getElementById("confirm-modal").style.display = "flex";
  }

  // This closes the modal
  function closeConfirm() {
    document.getElementById("confirm-modal").style.display = "none";
  }

  // This submits the form after confirmation
  function submitContactForm() {
    document.getElementById("contact-form").submit();
  }

  // This closes modal when clicking outside the box
  document.getElementById("confirm-modal").addEventListener("click", function(e) {
    if (e.target === this) closeConfirm();
  });

// EDIT MENU ITEM JS
    function selectCategory(name, btn) {
        document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        document.getElementById('selected-category').value = name;
    }

    function showConfirm() {
        document.getElementById('confirm-modal').classList.add('open');
    }

    function closeConfirm() {
        document.getElementById('confirm-modal').classList.remove('open');
    }

    function submitForm() {
        document.getElementById('edit-form').submit();
    }

    document.getElementById('confirm-modal').addEventListener('click', function (e) {
        if (e.target === this) closeConfirm();
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeConfirm();
    });

// MANAGE ABOUT JS
function showConfirm(type, sectionId) {
    document.getElementById('confirm-title').textContent = 'Save Changes';
    document.getElementById('confirm-message').textContent =
        'Are you sure you want to update this section?';
    document.getElementById('confirm-modal').classList.add('open');
    document.getElementById('confirm-yes').onclick = function() {
        closeConfirm();
        document.getElementById('edit-form-' + sectionId).submit();
    };
}

function closeConfirm() {
    document.getElementById('confirm-modal').classList.remove('open');
}

document.getElementById('confirm-modal').addEventListener('click', function(e) {
    if (e.target === this) closeConfirm();
});

function showDeleteConfirm(id, heading) {
    document.getElementById('delete-message').textContent =
        'Are you sure you want to delete the "' + heading + '" section? This cannot be undone.';
    document.getElementById('delete-confirm-btn').onclick = function() {
        document.getElementById('delete-form-' + id).submit();
    };
    document.getElementById('delete-modal').classList.add('open');
}

function closeDeleteConfirm() {
    document.getElementById('delete-modal').classList.remove('open');
}

document.getElementById('delete-modal').addEventListener('click', function(e) {
    if (e.target === this) closeDeleteConfirm();
});

// MANAGE CATEGORIES js
  // This opens the confirmation modal for deleting a category
  function confirmDeleteCategory(catId, catName) {
    document.getElementById("modal-title").innerText = "Delete Category";
    document.getElementById("modal-message").innerText =
      `Are you sure you want to delete "${catName}"? This cannot be undone.`;

    const confirmBtn = document.getElementById("modal-confirm-btn");
    confirmBtn.onclick = function () {
      document.getElementById(`delete-cat-${catId}`).submit();
    };

    document.getElementById("confirm-modal").style.display = "flex";
  }

  // This closes the modal
  function closeModal() {
    document.getElementById("confirm-modal").style.display = "none";
  }

// MANAGE HOMEPAGE js
// This toggles between text name and logo upload sections
    function toggleLogoSection() {
        const select      = document.getElementById("use_logo_select");
        const logoSection = document.getElementById("logo-section");
        const textSection = document.getElementById("text-section");

        if (select.value === "true") {
            logoSection.style.display = "block";
            textSection.style.display = "none";
        } else {
            logoSection.style.display = "none";
            textSection.style.display = "block";
        }
    }

    // Opens the modal with custom title + message + confirm action
    function openModal(title, message, onConfirm) {
        document.getElementById("modal-title").innerText   = title;
        document.getElementById("modal-message").innerText = message;

        const confirmBtn   = document.getElementById("modal-confirm-btn");
        confirmBtn.onclick = onConfirm;

        document.getElementById("confirm-modal").classList.add("open");
    }

    // Close modal
    function closeModal() {
        document.getElementById("confirm-modal").classList.remove("open");
    }

    // Branding
    function confirmBranding() {
        openModal(
            "Save Branding",
            "Are you sure you want to update the homepage branding?",
            () => document.getElementById("branding-form").submit()
        );
    }

    // Footer about
    function confirmFooterAbout() {
        openModal(
            "Update Footer About",
            "Are you sure you want to update the footer about text?",
            () => document.getElementById("footer-about-form").submit()
        );
    }

    // Dish update
    function confirmDish(dishKey) {
        openModal(
            "Update Dish",
            "Are you sure you want to update this dish?",
            () => document.getElementById(`dish-form-${dishKey}`).submit()
        );
    }

    // Adding review
    function confirmAddReview() {
        openModal(
            "Add Review",
            "Are you sure you want to add this new review?",
            () => document.getElementById("add-review-form").submit()
        );
    }

    // Updating review
    function confirmUpdateReview(reviewId) {
        openModal(
            "Update Review",
            "Are you sure you want to update this review?",
            () => document.getElementById(`review-form-${reviewId}`).submit()
        );
    }

    // Deleting review
    function confirmDeleteReview(reviewId, reviewerName) {
        openModal(
            "Delete Review",
            `Are you sure you want to delete the review by "${reviewerName}"? This cannot be undone.`,
            () => document.getElementById(`delete-review-form-${reviewId}`).submit()
        );
    }

    // Close modal when clicking outside the box
    document.getElementById("confirm-modal").addEventListener("click", function(e) {
        if (e.target === this) closeModal();
    });

// MANAGE MENU JS

    function showDeleteConfirm(itemId, itemName) {
        document.getElementById('delete-item-name').textContent = itemName;
        document.getElementById('confirm-delete-btn').onclick = function () {
            document.getElementById('delete-form-' + itemId).submit();
        };
        document.getElementById('delete-modal').classList.add('open');
    }

    function closeDeleteConfirm() {
        document.getElementById('delete-modal').classList.remove('open');
    }

    // Close modal when clicking the backdrop
    document.getElementById('delete-modal').addEventListener('click', function (e) {
        if (e.target === this) closeDeleteConfirm();
    });

    // Close modal with Escape key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeDeleteConfirm();
    });

    // Scroll-reveal animation
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.08 });

    document.querySelectorAll('.category-card, .category-heading').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(16px)';
        el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        observer.observe(el);
    });

// MANAGE NEWSLETTER SUBS
// Send modal
  function confirmSend() {
    document.getElementById('send-modal').classList.add('open');
  }
  function closeSendModal() {
    document.getElementById('send-modal').classList.remove('open');
  }

  // Delete subscriber modal
  function confirmDeleteSub(index, email) {
    document.getElementById('del-sub-email').textContent = email;
    document.getElementById('del-sub-confirm-btn').onclick = function () {
      document.getElementById('del-sub-' + index).submit();
    };
    document.getElementById('del-sub-modal').classList.add('open');
  }
  function closeDelSubModal() {
    document.getElementById('del-sub-modal').classList.remove('open');
  }

  // Close on outside click
  document.querySelectorAll('.modal-overlay').forEach(function(modal) {
    modal.addEventListener('click', function(e) {
      if (e.target === this) this.classList.remove('open');
    });
  });

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('open'));
    }
  });

// MANAGE STAFF JS
// This opens the confirmation modal for disabling staff
    function confirmDisableStaff(staffId, staffName) {
        document.getElementById("modal-title").innerText = "Disable Staff Member";
        document.getElementById("modal-message").innerText =
            `Are you sure you want to disable "${staffName}"? They will no longer be able to log in.`;

        const confirmBtn = document.getElementById("modal-confirm-btn");
        confirmBtn.onclick = function () {
            window.location = `/admin/staff/disable/${staffId}`;
        };

        document.getElementById("confirm-modal").style.display = "flex";
    }

    // This closes the modal
    function closeModal() {
        document.getElementById("confirm-modal").style.display = "none";
    }

    // Close modal when clicking outside the box
    document.getElementById("confirm-modal").addEventListener("click", function(e) {
        if (e.target === this) closeModal();
    });

// SOCIAL LINKS JS
// This is for the edit modal
    function openEdit(id, platform, url, iconClass, order, isActive) {
        document.getElementById('edit-platform').value = platform;
        document.getElementById('edit-url').value      = url;
        document.getElementById('edit-icon').value     = iconClass;
        document.getElementById('edit-order').value    = order;
        document.getElementById('edit-active').value   = isActive;
        document.getElementById('edit-form').action    = '/admin/social-links/edit/' + id;
        document.getElementById('edit-modal').classList.add('open');
    }

    function closeEdit() {
        document.getElementById('edit-modal').classList.remove('open');
    }

    document.getElementById('edit-modal').addEventListener('click', function(e) {
        if (e.target === this) closeEdit();
    });

    // This is for the delete confirmation modal
    function showDeleteConfirm(id, platform) {
        document.getElementById('delete-message').textContent =
            'Are you sure you want to remove the ' + platform + ' link?';
        document.getElementById('delete-confirm-btn').onclick = function() {
            document.getElementById('delete-form-' + id).submit();
        };
        document.getElementById('delete-modal').classList.add('open');
    }

    function closeDeleteConfirm() {
        document.getElementById('delete-modal').classList.remove('open');
    }

    document.getElementById('delete-modal').addEventListener('click', function(e) {
        if (e.target === this) closeDeleteConfirm();
    });

// UPDATE HOURS JS
function showModal(title, message, onConfirm) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-message').textContent = message;
    document.getElementById('modal-confirm-btn').onclick = function () {
      closeModal();
      onConfirm();
    };
    document.getElementById('confirm-modal').style.display = 'flex';
  }

  function closeModal() {
    document.getElementById('confirm-modal').style.display = 'none';
  }

  document.getElementById('confirm-modal').addEventListener('click', function (e) {
    if (e.target === this) closeModal();
  });

  function confirmHours() {
    showModal(
      'Confirm Hours Update',
      'Are you sure you want to update the opening hours?',
      () => document.getElementById('update-hours-form').submit()
    );
  }

// VIEW ALL ORDERS js
// This converts every .rel-time element's data-datetime into a human-readable relative string
    function timeAgo(datetimeStr) {
        const then  = new Date(datetimeStr);
        const now   = new Date();
        const diff  = Math.floor((now - then) / 1000); // seconds

        if (diff < 60)                        return 'Just now';
        if (diff < 3600)  {
            const m = Math.floor(diff / 60);
            return m + ' min ago';
        }
        if (diff < 86400) {
            const h = Math.floor(diff / 3600);
            return h + ' hr' + (h !== 1 ? 's' : '') + ' ago';
        }
        if (diff < 604800) {
            const d = Math.floor(diff / 86400);
            return d + ' day' + (d !== 1 ? 's' : '') + ' ago';
        }
        // Older than a week — show the actual date from the title attribute
        return then.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
    }

    // This is the raw orders data from Flask — passed into Vue as the initial dataset
    const ordersData = [
        {% for order in orders %}
        {
            order_id:        {{ order.order_id }},
            customer_name:   "{{ (order.customer_fullname or order.guest_fullname or '') | e }}",
            customer_email:  "{{ (order.customer_email or order.guest_email or '') | e }}",
            order_type:      "{{ order.order_type }}",
            order_type_display: "{{ order.order_type | capitalize }}",
            total_price:     "{{ '%.2f' | format(order.total_price) }}",
            order_status:    "{{ order.order_status }}",
            status_display:  "{{ order.order_status | capitalize }}",
            datetime:        "{{ order.order_date.strftime('%Y-%m-%d') }}T{{ order.order_time }}",
            datetime_title:  "{{ order.order_date.strftime('%d %b %Y') }} at {{ order.order_time }}",
            view_url:        "{{ url_for('admin.view_customer_order', order_id=order.order_id) }}"
        },
        {% endfor %}
    ];

    // This is the Vue 3 app that handles live search and filtering
    const { createApp, ref, computed, nextTick } = Vue;

    createApp({
        setup() {
            // This holds the current search query and active filter pill
            const search       = ref('{{ search }}');
            const activeFilter = ref('{{ filter_type }}');

            // These are the filter pill options
            const filters = [
                { val: '',           label: 'All' },
                { val: 'today',      label: 'Today' },
                { val: 'delivery',   label: '🚗 Delivery' },
                { val: 'collection', label: '🏪 Collection' },
                { val: 'pending',    label: 'Pending' },
                { val: 'confirmed',  label: 'Confirmed' },
                { val: 'preparing',  label: 'Preparing' },
                { val: 'ready',      label: 'Ready' },
                { val: 'completed',  label: 'Completed' },
                { val: 'cancelled',  label: 'Cancelled' },
            ];

            // This computes the filtered orders list reactively whenever search or filter changes
            const filteredOrders = computed(() => {
                let results = ordersData;
                const q = search.value.toLowerCase().trim();

                // This applies the text search across name, email and order ID
                if (q) {
                    results = results.filter(o =>
                        o.customer_name.toLowerCase().includes(q)  ||
                        o.customer_email.toLowerCase().includes(q) ||
                        String(o.order_id).includes(q)
                    );
                }

                // This applies the active filter pill
                if (activeFilter.value) {
                    const f = activeFilter.value;

                    if (f === 'today') {
                        // This filters to orders placed today using the datetime field
                        const todayStr = new Date().toISOString().slice(0, 10);
                        results = results.filter(o => o.datetime.startsWith(todayStr));
                    } else if (f === 'delivery' || f === 'collection') {
                        results = results.filter(o => o.order_type === f);
                    } else {
                        // This filters by order status
                        results = results.filter(o => o.order_status === f);
                    }
                }

                return results;
            });

            // This updates the rel-time spans after Vue re-renders the DOM
            const updateTimestamps = () => {
                nextTick(() => {
                    document.querySelectorAll('.rel-time').forEach(function(el) {
                        if (el.dataset.datetime) {
                            el.textContent = timeAgo(el.dataset.datetime);
                        }
                    });
                });
            };

            return { search, activeFilter, filters, filteredOrders, updateTimestamps };
        },

        // This runs the timestamp update after every render
        updated() { this.updateTimestamps(); },
        mounted()  { this.updateTimestamps(); }

    }).mount('#orders-app');

// VIEW ANALYTICS JS
// Reads CSS variables so chart colours follows the theme
    const rootStyle    = getComputedStyle(document.documentElement);
    const colorPrimary = rootStyle.getPropertyValue('--color-primary').trim()    || '#8B0000';
    const colorAccent  = rootStyle.getPropertyValue('--color-accent').trim()     || '#D4AF37';
    const colorSidebar = rootStyle.getPropertyValue('--color-sidebar-bg').trim() || '#2C2416';
    const colorMuted   = rootStyle.getPropertyValue('--color-text-muted').trim() || '#9E8C78';
    const colorText    = rootStyle.getPropertyValue('--color-text').trim()       || '#2C2416';

    // Shared axis style used by all charts
    const axisStyle = {
        titleTextStyle: { color: colorMuted },
        textStyle:      { color: colorText  }
    };

    // Load Google Charts
    google.charts.load('current', { packages: ['corechart'] });
    google.charts.setOnLoadCallback(drawCharts);

    function drawCharts() {
        drawDayChart();
        drawTimeChart();
        drawMonthlyChart();
        drawTopItemsQtyChart();
        drawTopItemsRevenueChart();
        drawRevenueTrendChart();
        drawOrderTypeChart();
    }

    // Chart 1: Bookings by Day
    function drawDayChart() {
        var data = google.visualization.arrayToDataTable([
            ['Day', 'Bookings'],
            {% for item in bookings_by_day %}
            ['{{ item.day }}', {{ item.count }}],
            {% endfor %}
        ]);

        var options = {
            colors: [colorPrimary],
            backgroundColor: 'transparent',
            legend: { position: 'none' },
            hAxis: Object.assign({ title: 'Day of Week' },   axisStyle),
            vAxis: Object.assign({ title: 'Number of Bookings', minValue: 0 }, axisStyle),
            chartArea: { width: '80%', height: '75%' }
        };

        var chart = new google.visualization.ColumnChart(
            document.getElementById('bookings_by_day_chart')
        );
        chart.draw(data, options);
    }

    // Chart 2: Bookings by Time
    function drawTimeChart() {
        var data = google.visualization.arrayToDataTable([
            ['Time', 'Bookings'],
            {% for item in bookings_by_time %}
            ['{{ item.hour }}:00', {{ item.count }}],
            {% endfor %}
        ]);

        var options = {
            colors: [colorAccent],
            backgroundColor: 'transparent',
            legend: { position: 'none' },
            hAxis: Object.assign({ title: 'Time Slot' },         axisStyle),
            vAxis: Object.assign({ title: 'Number of Bookings', minValue: 0 }, axisStyle),
            chartArea: { width: '80%', height: '75%' }
        };

        var chart = new google.visualization.ColumnChart(
            document.getElementById('bookings_by_time_chart')
        );
        chart.draw(data, options);
    }

    // Chart 3: Monthly Trend
    function drawMonthlyChart() {
        var data = google.visualization.arrayToDataTable([
            ['Month', 'Bookings'],
            {% for item in monthly_trend %}
            ['{{ item.month }}', {{ item.count }}],
            {% endfor %}
        ]);

        var options = {
            colors: [colorSidebar],
            backgroundColor: 'transparent',
            legend: { position: 'none' },
            hAxis: Object.assign({ title: 'Month' },              axisStyle),
            vAxis: Object.assign({ title: 'Number of Bookings', minValue: 0 }, axisStyle),
            curveType: 'function',
            chartArea: { width: '88%', height: '75%' }
        };

        var chart = new google.visualization.LineChart(
            document.getElementById('monthly_trend_chart')
        );
        chart.draw(data, options);
    }

    // Chart 4: Top items by quantity ordered
    function drawTopItemsQtyChart() {
        var data = google.visualization.arrayToDataTable([
            ['Item', 'Times Ordered'],
            {% for item in top_items_qty %}
            ['{{ item.item_name | replace("'", "\\'") }}', {{ item.total_qty }}],
            {% endfor %}
        ]);

        var options = {
            colors: [colorPrimary],
            backgroundColor: 'transparent',
            legend: { position: 'none' },
            hAxis: Object.assign({ title: 'Times Ordered', minValue: 0 }, axisStyle),
            vAxis: Object.assign({ textStyle: { color: colorText, fontSize: 12 } }, axisStyle),
            chartArea: { width: '65%', height: '80%' }
        };

        var chart = new google.visualization.BarChart(
            document.getElementById('top_items_qty_chart')
        );
        chart.draw(data, options);
    }

    // Chart 5: Top items by revenue generated
    function drawTopItemsRevenueChart() {
        var data = google.visualization.arrayToDataTable([
            ['Item', 'Revenue (£)'],
            {% for item in top_items_revenue %}
            ['{{ item.item_name | replace("'", "\\'") }}', {{ item.total_revenue }}],
            {% endfor %}
        ]);

        var options = {
            colors: [colorAccent],
            backgroundColor: 'transparent',
            legend: { position: 'none' },
            hAxis: Object.assign({ title: 'Revenue (£)', minValue: 0 }, axisStyle),
            vAxis: Object.assign({ textStyle: { color: colorText, fontSize: 12 } }, axisStyle),
            chartArea: { width: '65%', height: '80%' }
        };

        var chart = new google.visualization.BarChart(
            document.getElementById('top_items_revenue_chart')
        );
        chart.draw(data, options);
    }

    // Chart 6: Revenue trend over last 6 months
    function drawRevenueTrendChart() {
        var data = google.visualization.arrayToDataTable([
            ['Month', 'Revenue (£)'],
            {% for item in revenue_trend %}
            ['{{ item.month }}', {{ item.revenue }}],
            {% endfor %}
        ]);

        var options = {
            colors: [colorPrimary],
            backgroundColor: 'transparent',
            legend: { position: 'none' },
            hAxis: Object.assign({ title: 'Month' }, axisStyle),
            vAxis: Object.assign({ title: 'Revenue (£)', minValue: 0 }, axisStyle),
            curveType: 'function',
            chartArea: { width: '80%', height: '75%' }
        };

        var chart = new google.visualization.LineChart(
            document.getElementById('revenue_trend_chart')
        );
        chart.draw(data, options);
    }

    // Chart 7: Collection vs Delivery pie chart
    function drawOrderTypeChart() {
        var data = google.visualization.arrayToDataTable([
            ['Order Type', 'Count'],
            {% for item in orders_by_type %}
            ['{{ item.order_type | capitalize }}', {{ item.count }}],
            {% endfor %}
        ]);

        var options = {
            colors: [colorPrimary, colorAccent, colorSidebar],
            backgroundColor: 'transparent',
            legend: { textStyle: { color: colorText } },
            chartArea: { width: '80%', height: '80%' },
            pieHole: 0.4
        };

        var chart = new google.visualization.PieChart(
            document.getElementById('order_type_chart')
        );
        chart.draw(data, options);
    }

// VIEW RESERVATION JS
function showCancelConfirm(customerId, name) {
        document.getElementById('cancel-name').textContent = name;
        document.getElementById('cancel-confirm-btn').onclick = function () {
            document.getElementById('cancel-form-' + customerId).submit();
        };
        document.getElementById('cancel-modal').classList.add('open');
    }

    function closeCancelConfirm() {
        document.getElementById('cancel-modal').classList.remove('open');
    }

    // Close on backdrop click
    document.getElementById('cancel-modal').addEventListener('click', function (e) {
        if (e.target === this) closeCancelConfirm();
    });

    // Close on Escape
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeCancelConfirm();
    });

    // Scroll-reveal animation
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) entry.target.classList.add('visible');
        });
    }, { threshold: 0.05 });

    document.querySelectorAll('.dash-card, .dash-header').forEach(el => observer.observe(el));