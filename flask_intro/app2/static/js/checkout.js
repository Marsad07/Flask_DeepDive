const stripe = Stripe('{{ stripe_public_key }}');
    let elements  = null;
    let paymentElement = null;
    let clientSecret   = null;

    // This tracks the applied coupon discount
    let appliedDiscount = 0;
    const originalTotal = {{ total }};

    // This validates all contact and address fields before opening the confirmation modal
    function validateAndConfirm() {
        const name  = document.getElementById('full_name').value.trim();
        const email = document.getElementById('email').value.trim();
        const phone = document.getElementById('phone').value.trim();

        // This clears any existing validation errors before re-checking
        clearErrors();

        let valid = true;

        // This checks that the name field is not empty and contains at least two words
        if (!name) {
            showError('full_name', 'Please enter your full name.');
            valid = false;
        } else if (name.split(' ').filter(w => w.length > 0).length < 2) {
            showError('full_name', 'Please enter your first and last name.');
            valid = false;
        }

        // This validates the email address format
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!email) {
            showError('email', 'Please enter your email address.');
            valid = false;
        } else if (!emailRegex.test(email)) {
            showError('email', 'Please enter a valid email address.');
            valid = false;
        }

        // This validates that the phone number contains only digits and is 10-15 characters
        const phoneRegex = /^[0-9]{10,15}$/;
        if (!phone) {
            showError('phone', 'Please enter your phone number.');
            valid = false;
        } else if (!phoneRegex.test(phone)) {
            showError('phone', 'Phone must be 10–15 digits with no spaces or letters.');
            valid = false;
        }

        // This checks the delivery address fields if the customer has selected delivery
        const isDelivery = document.querySelector(
            'input[name="order_type"]:checked').value === 'delivery';
        if (isDelivery) {
            const address1 = document.getElementById('address1').value.trim();
            const city     = document.getElementById('city').value.trim();
            const postcode = document.getElementById('postcode').value.trim();

            if (!address1) {
                showError('address1', 'Please enter your address.');
                valid = false;
            }
            if (!city) {
                showError('city', 'Please enter your city.');
                valid = false;
            }
            if (!postcode) {
                showError('postcode', 'Please enter your postcode.');
                valid = false;
            }
        }

        // This only opens the confirmation modal if all validation passes
        if (valid) openConfirm();
    }

    // This shows a validation error message below the given input field
    function showError(inputId, message) {
        const input = document.getElementById(inputId);
        input.style.borderColor = 'var(--color-primary)';

        const err = document.createElement('p');
        err.className   = 'field-error';
        err.textContent = message;
        err.style.cssText =
            'color: var(--color-primary); font-size: 12px; ' +
            'margin: 4px 0 0; font-family: var(--font-body);';
        input.insertAdjacentElement('afterend', err);
    }

    // This clears all existing validation error messages and resets input border colours
    function clearErrors() {
        document.querySelectorAll('.field-error').forEach(e => e.remove());
        document.querySelectorAll('input').forEach(i => i.style.borderColor = '');
    }

    // This applies the coupon code entered by the customer
    async function applyCoupon() {
        const code      = document.getElementById('coupon-input').value.trim().toUpperCase();
        const successEl = document.getElementById('coupon-success');
        const errorEl   = document.getElementById('coupon-error');
        const applyBtn  = document.querySelector('.btn-apply');

        successEl.style.display = 'none';
        errorEl.style.display   = 'none';

        if (!code) {
            errorEl.textContent  = 'Please enter a coupon code.';
            errorEl.style.display = 'block';
            return;
        }

        // This shows a loading state on the button while the coupon is being validated
        applyBtn.textContent = 'Checking...';
        applyBtn.disabled    = true;

        try {
            const response = await fetch('/checkout/apply-coupon', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ code: code, total: originalTotal })
            });
            const data = await response.json();

            if (data.success) {
                appliedDiscount = data.discount_amount;

                const newTotal = Math.max(0, originalTotal - appliedDiscount).toFixed(2);
                const discountDisplay = data.discount_type === 'percent'
                    ? `${data.discount_value}% off`
                    : `£${parseFloat(data.discount_value).toFixed(2)} off`;

                // This updates the order summary with the discounted price
                document.getElementById('discount-row').style.display  = 'flex';
                document.getElementById('discount-label').textContent  =
                    `${code} (${discountDisplay})`;
                document.getElementById('discount-amount').textContent =
                    `-£${appliedDiscount.toFixed(2)}`;
                document.getElementById('original-price').style.display = 'block';
                document.getElementById('final-price').textContent = `£${newTotal}`;

                // This stores the coupon data in the hidden fields for form submission
                document.getElementById('coupon_code_hidden').value    = code;
                document.getElementById('discount_amount_hidden').value =
                    appliedDiscount.toFixed(2);

                // This locks the input and shows the success message
                successEl.textContent =
                    `✓ Code applied — you save £${appliedDiscount.toFixed(2)}!`;
                successEl.style.display = 'block';
                document.getElementById('coupon-input').disabled = true;
                applyBtn.textContent = '✓ Applied';

            } else {
                // This shows the specific error message returned from the server
                errorEl.textContent  = data.message || 'Invalid or expired coupon code.';
                errorEl.style.display = 'block';
                applyBtn.textContent = 'Apply';
                applyBtn.disabled    = false;
            }

        } catch (err) {
            errorEl.textContent  = 'Something went wrong. Please try again.';
            errorEl.style.display = 'block';
            applyBtn.textContent = 'Apply';
            applyBtn.disabled    = false;
        }
    }

    // This allows the customer to press Enter to apply the coupon
    document.getElementById('coupon-input').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') { e.preventDefault(); applyCoupon(); }
    });

    // This opens the order confirmation modal
    function openConfirm() {
        const finalTotal = Math.max(0, originalTotal - appliedDiscount).toFixed(2);
        const orderType  = document.querySelector(
            'input[name="order_type"]:checked').value;
        const payMethod  = document.querySelector(
            'input[name="payment_method"]:checked').value;
        const name = document.getElementById('full_name').value;

        // This builds the items list for the confirmation modal
        const cart = {{ cart | tojson }};
        let itemsHtml = '';
        for (const [id, item] of Object.entries(cart)) {
            itemsHtml += `
                <div class="confirm-item-row">
                    <span class="confirm-item-label">${item.name} x${item.quantity}</span>
                    <span class="confirm-item-value">
                        £${(item.price * item.quantity).toFixed(2)}
                    </span>
                </div>`;
        }

        // This adds the order details to the confirmation modal
        itemsHtml += `
            <div class="confirm-item-row">
                <span class="confirm-item-label">Name</span>
                <span class="confirm-item-value">${name || '—'}</span>
            </div>
            <div class="confirm-item-row">
                <span class="confirm-item-label">Order Type</span>
                <span class="confirm-item-value"
                      style="text-transform: capitalize;">${orderType}</span>
            </div>
            <div class="confirm-item-row">
                <span class="confirm-item-label">Payment</span>
                <span class="confirm-item-value">
                    ${payMethod === 'cash' ? 'Cash' : 'Card / Online'}
                </span>
            </div>`;

        document.getElementById('confirm-items-list').innerHTML  = itemsHtml;
        document.getElementById('confirm-total-val').textContent = `£${finalTotal}`;

        // This shows the discount row in the modal if a coupon was applied
        const discountRow = document.getElementById('confirm-discount-row');
        if (appliedDiscount > 0) {
            discountRow.style.display = 'flex';
            document.getElementById('confirm-discount-val').textContent =
                `-£${appliedDiscount.toFixed(2)}`;
        } else {
            discountRow.style.display = 'none';
        }

        document.getElementById('confirm-modal').style.display = 'flex';
    }

    // This closes the confirmation modal
    function closeConfirm() {
        document.getElementById('confirm-modal').style.display = 'none';
    }

    // This closes the modal when clicking outside it
    document.getElementById('confirm-modal').addEventListener('click', function(e) {
        if (e.target === this) closeConfirm();
    });

    // This closes the modal when pressing Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') closeConfirm();
    });

    // This handles the final order placement from the confirmation modal
    document.getElementById('confirm-place-btn').addEventListener('click', async function() {
        // This disables the button immediately to prevent double submission
        this.textContent = 'Placing...';
        this.disabled    = true;
        closeConfirm();

        const isOnline = document.getElementById('pay_online').checked;

        if (isOnline) {
            // This shows the loading screen for online payments
            document.getElementById('payment-loading').style.display = 'flex';

            const { error, paymentIntent } = await stripe.confirmPayment({
                elements,
                confirmParams: { return_url: window.location.origin },
                redirect: 'if_required'
            });

            if (error) {
                // This hides the loader and shows the error if payment failed
                document.getElementById('payment-loading').style.display = 'none';
                document.getElementById('payment-errors').textContent    = error.message;
                this.textContent = 'Yes, Place Order';
                this.disabled    = false;
            } else if (paymentIntent && paymentIntent.status === 'succeeded') {
                document.getElementById('payment_status').value      = 'paid';
                document.getElementById('payment_intent_id').value   = paymentIntent.id;
                // This submits the form after successful payment
                document.getElementById('checkout-form').submit();
            }
        } else {
            // This shows the loading screen for cash orders and submits the form
            document.getElementById('payment-loading').style.display = 'flex';
            document.getElementById('checkout-form').submit();
        }
    });

    // This shows or hides the delivery address section based on the selected order type
    function toggleAddress() {
        const deliverySection = document.getElementById('delivery-address');
        const isDelivery      = document.querySelector(
            'input[name="order_type"]:checked').value === 'delivery';
        deliverySection.style.display      = isDelivery ? 'block' : 'none';
        document.getElementById('address1').required  = isDelivery;
        document.getElementById('city').required      = isDelivery;
        document.getElementById('postcode').required  = isDelivery;
    }

    // This shows or hides the Stripe payment element based on the selected payment method
    async function togglePaymentSection() {
        const isOnline      = document.getElementById('pay_online').checked;
        const stripeSection = document.getElementById('stripe-section');
        stripeSection.style.display = isOnline ? 'block' : 'none';

        if (isOnline && !elements) {
            // This creates a payment intent and loads the Stripe payment element
            const response = await fetch('/checkout/create-payment-intent', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data   = await response.json();
            clientSecret = data.clientSecret;
            document.getElementById('payment_intent_id').value = clientSecret;

            elements      = stripe.elements({ clientSecret });
            paymentElement = elements.create('payment');
            paymentElement.mount('#payment-element');
        }
    }

    // This highlights the selected order type option using CSS variables
    document.querySelectorAll('.order-type-option').forEach(option => {
        option.closest('label').addEventListener('click', function() {
            document.querySelectorAll('.order-type-option').forEach(opt => {
                opt.style.background   = '';
                opt.style.borderColor  = '';
            });
            this.querySelector('.order-type-option').style.background  =
                'color-mix(in srgb, var(--color-accent) 10%, var(--color-bg))';
            this.querySelector('.order-type-option').style.borderColor =
                'var(--color-primary)';
        });
    });

    // This highlights the selected payment option using CSS variables
    document.querySelectorAll('.payment-option').forEach(option => {
        option.addEventListener('click', function() {
            document.querySelectorAll('.payment-option').forEach(opt => {
                opt.style.background  = '';
                opt.style.borderColor = '';
            });
            this.style.background  =
                'color-mix(in srgb, var(--color-accent) 10%, var(--color-bg))';
            this.style.borderColor = 'var(--color-primary)';
        });
    });
</script>