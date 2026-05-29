from marshmallow import Schema, fields, validate, ValidationError

# This standalone function is used by both CheckoutSchema and RegisterSchema
# to validate that a full name contains at least a first and last name
def validate_full_name(value):
    if len(value.strip().split()) < 2:
        raise ValidationError("Please enter your full name (first and last).")

class CheckoutSchema(Schema):
    """Validates the checkout form data submitted by the customer."""
    full_name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=2, max=255, error="Full name must be between 2 and 255 characters."),
            validate_full_name
        ]
    )
    email = fields.Email(
        required=True,
        error_messages={"required": "Email is required.", "invalid": "Please enter a valid email address."}
    )
    phone = fields.Str(
        required=True,
        validate=validate.Regexp(r'^\+?[\d\s\-]{7,20}$', error="Please enter a valid phone number.")
    )
    order_type = fields.Str(
        required=True,
        validate=validate.OneOf(['delivery', 'collection'], error="Order type must be delivery or collection.")
    )
    payment_method = fields.Str(
        required=True,
        validate=validate.OneOf(
            ['card_online', 'cash', 'card_on_delivery'],
            error="Invalid payment method."
        )
    )
    # Delivery address fields as its only required when order_type is delivery
    address_line1 = fields.Str(load_default=None)
    address_line2 = fields.Str(load_default=None)
    city          = fields.Str(load_default=None)
    postcode      = fields.Str(load_default=None)
    special_instructions = fields.Str(load_default=None)
    coupon_code   = fields.Str(load_default=None)
    discount_amount = fields.Float(load_default=0)

class RegisterSchema(Schema):
    """Validates the customer registration form."""

    customer_fullname = fields.Str(
        required=True,
        validate=[
            validate.Length(min=2, max=255, error="Full name must be between 2 and 255 characters."),
            validate_full_name
        ]
    )
    customer_email = fields.Email(
        required=True,
        error_messages={"required": "Email is required.", "invalid": "Please enter a valid email address."}
    )
    customer_phonenum = fields.Str(
        required=True,
        validate=validate.Regexp(r'^\+?[\d\s\-]{7,20}$', error="Please enter a valid phone number.")
    )
    customer_password = fields.Str(
        required=True,
        validate=validate.Length(min=6, error="Password must be at least 6 characters.")
    )

class CouponCreateSchema(Schema):
    """Validates the create coupon form in the admin panel."""

    code = fields.Str(
        load_default=None,
        validate=validate.Length(max=50, error="Coupon code cannot exceed 50 characters.")
    )
    discount_type = fields.Str(
        required=True,
        validate=validate.OneOf(['percent', 'fixed'], error="Discount type must be percent or fixed.")
    )
    discount_value = fields.Float(
        required=True,
        validate=validate.Range(min=0.01, max=100000, error="Discount value must be between 0.01 and 100000.")
    )
    assigned_email = fields.Email(
        load_default=None,
        allow_none=True,
        error_messages={"invalid": "Please enter a valid email address for the assigned user."}
    )
    uses_limit = fields.Int(
        load_default=1,
        validate=validate.Range(min=1, error="Usage limit must be at least 1.")
    )
    expires_at = fields.Date(
        load_default=None,
        allow_none=True,
        error_messages={"invalid": "Please enter a valid expiry date."}
    )

class UpdateProfileSchema(Schema):
    """Validates the customer profile update form."""

    customer_fullname = fields.Str(
        required=True,
        validate=[
            validate.Length(min=2, max=255, error="Full name must be between 2 and 255 characters."),
            validate_full_name
        ]
    )
    customer_email = fields.Email(
        required=True,
        error_messages={"required": "Email is required.", "invalid": "Please enter a valid email address."}
    )
    customer_phonenum = fields.Str(
        required=True,
        validate=validate.Regexp(r'^\+?[\d\s\-]{7,20}$', error="Please enter a valid phone number.")
    )
    new_password = fields.Str(
        load_default=None,
        validate=validate.Length(min=6, error="Password must be at least 6 characters.")
    )
    confirm_password = fields.Str(load_default=None)