from flask import Blueprint
from app2.controllers.admin_controller import (admin_login, dashboard, logout, view_reservations, manage_menu,
                                               add_menu_item, edit_menu_item, delete_menu_item, update_hours,
                                               view_analytics, view_all_orders, view_customer_order,
                                               update_order_status, manage_categories, delete_category, image_manager,
                                               manage_homepage, update_branding_settings, update_review_item,
                                               add_review_item, delete_review_item, update_dish_item, assign_driver,
                                               offer_driver, manage_drivers, toggle_driver_active, manage_contact,
                                               manage_social_links, add_social_link, edit_social_link,
                                               delete_social_link, manage_about, update_about_section,
                                               add_about_section, delete_about_section, manage_tables,
                                               save_table_positions, add_table, delete_table, update_table,
                                               manage_staff, create_staff, edit_staff, disable_staff)
from controllers.staff_controller import reset_staff_email, reset_staff_default

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
admin_bp.route("/login", methods=["GET", "POST"])(admin_login)
admin_bp.route("/dashboard")(dashboard)
admin_bp.route("/logout")(logout)

admin_bp.route("/menu/add", methods=["GET", "POST"])(add_menu_item)
admin_bp.route("/menu/edit/<int:item_id>", methods=["GET", "POST"])(edit_menu_item)
admin_bp.route("/menu/delete/<int:item_id>", methods=["POST"])(delete_menu_item)

admin_bp.route("/reservations")(view_reservations)
admin_bp.route("/menu")(manage_menu)
admin_bp.route("/update_hours", methods=["GET", "POST"])(update_hours)
admin_bp.route("/analytics")(view_analytics)
admin_bp.route("/view_all_orders")(view_all_orders)
admin_bp.route("/customer_order/<int:order_id>")(view_customer_order)
admin_bp.route("/update_order_status/<int:order_id>", methods=["POST"])(update_order_status)
admin_bp.route("/categories", methods=["GET", "POST"])(manage_categories)
admin_bp.route("/categories/delete/<int:category_id>", methods=["POST"])(delete_category)
admin_bp.route("/image_manager", methods=["GET", "POST"])(image_manager)
admin_bp.add_url_rule('/admin/manage-homepage', view_func=manage_homepage, methods=['GET'])
admin_bp.add_url_rule('/admin/update-branding', view_func=update_branding_settings, methods=['POST'])
admin_bp.add_url_rule('/admin/update-review', view_func=update_review_item, methods=['POST'])
admin_bp.add_url_rule('/admin/add-review', view_func=add_review_item, methods=['POST'])
admin_bp.add_url_rule('/admin/delete-review/<int:review_id>', view_func=delete_review_item, methods=['POST'])
admin_bp.add_url_rule('/admin/update-dish', view_func=update_dish_item, methods=['POST'])

admin_bp.route('/drivers')(manage_drivers)
admin_bp.route('/drivers/<int:staff_id>/toggle-active', methods=['POST'])(toggle_driver_active)
admin_bp.route('/orders/<int:order_id>/assign_driver', methods=['POST'])(assign_driver)
admin_bp.route('/orders/<int:order_id>/offer_driver', methods=['POST'])(offer_driver)
admin_bp.route('/manage_contact', methods=['GET', 'POST'])(manage_contact)

admin_bp.route('/social-links', methods=['GET'])(manage_social_links)
admin_bp.route('/social-links/add', methods=['POST'])(add_social_link)
admin_bp.route('/social-links/edit/<int:link_id>', methods=['POST'])(edit_social_link)
admin_bp.route('/social-links/delete/<int:link_id>', methods=['POST'])(delete_social_link)

admin_bp.route('/manage-about', methods=['GET'])(manage_about)
admin_bp.route('/about/update/<int:section_id>', methods=['POST'])(update_about_section)
admin_bp.route('/about/add', methods=['POST'])(add_about_section)
admin_bp.route('/about/delete/<int:section_id>', methods=['POST'])(delete_about_section)

admin_bp.route('/tables', methods=['GET'])(manage_tables)
admin_bp.route('/tables/save-positions', methods=['POST'])(save_table_positions)
admin_bp.route('/tables/add', methods=['POST'])(add_table)
admin_bp.route('/tables/delete/<int:table_id>', methods=['POST'])(delete_table)
admin_bp.route('/tables/update/<int:table_id>', methods=['POST'])(update_table)

admin_bp.route('/staff')(manage_staff)
admin_bp.route('/staff/create', methods=['GET', 'POST'])(create_staff)
admin_bp.route('/staff/<int:staff_id>/edit', methods=['GET', 'POST'])(edit_staff)
admin_bp.route('/staff/<int:staff_id>/disable')(disable_staff)
admin_bp.route('/staff/<int:staff_id>/reset-default')(reset_staff_default)
admin_bp.route('/staff/<int:staff_id>/reset-email')(reset_staff_email)