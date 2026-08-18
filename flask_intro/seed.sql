-- Seed data for Tango — run this AFTER schema.sql on the hosted database.
-- Fills the rows the app expects to exist so it doesn't crash on first load.

-- 1. Branding — REQUIRED. base.html reads branding.restaurant_name on every page.
--    Without this row the site 500s immediately.
INSERT INTO restaurant_branding (use_logo, logo_path, restaurant_name, restaurant_motto, footer_about, footer_newsletter_text)
VALUES (0, NULL, 'Tango', 'Full-flavour, fast.', 'A demo restaurant built to showcase the Tango platform.', 'Sign up for offers and updates.');

-- 2. Admin login — REQUIRED to access the admin panel at all.
--    Replace REPLACE_WITH_YOUR_HASH below with the output from the Python
--    command you ran locally (generate_password_hash('your_chosen_password')).
INSERT INTO admin_restaurant (admin_username, password_hash, admin_fullname, admin_email, role)
VALUES ('admin', 'scrypt:32768:8:1$QRFiC8nsrHKtq855$c8e83b2ea952c6d5005819fa3a7c27bfc751927017b016104aea6c45a4b0fad28c7032bd6be951a2f44a1fb6ca85557b90d11c04842b6255c8eeb8beb4bb0f07', 'Marsad Choudhury', 'admin@example.com', 'super_admin');

-- 3. System settings — needed for the staff "reset to default password" feature.
INSERT INTO system_settings (id, default_staff_password)
VALUES (1, 'ChangeMe123!');

-- 4. Restaurant hours — optional but the homepage/footer displays these.
INSERT INTO restaurant_info (day_of_week, opening_time, closing_time, is_closed, address)
VALUES
('Monday',    '11:00:00', '22:00:00', 0, '1 Example Street, Manchester, UK'),
('Tuesday',   '11:00:00', '22:00:00', 0, '1 Example Street, Manchester, UK'),
('Wednesday', '11:00:00', '22:00:00', 0, '1 Example Street, Manchester, UK'),
('Thursday',  '11:00:00', '22:00:00', 0, '1 Example Street, Manchester, UK'),
('Friday',    '11:00:00', '23:00:00', 0, '1 Example Street, Manchester, UK'),
('Saturday',  '11:00:00', '23:00:00', 0, '1 Example Street, Manchester, UK'),
('Sunday',    '12:00:00', '21:00:00', 0, '1 Example Street, Manchester, UK');

-- 5. Contact details — optional, shown on the contact page.
INSERT INTO restaurant_contact (email, phonenumber, address)
VALUES ('contact@example.com', '0161 000 0000', '1 Example Street, Manchester, UK');

-- 6. A couple of menu items so the customer-facing site isn't empty.
INSERT INTO menu_categories (category_name) VALUES ('Mains'), ('Starters'), ('Drinks');

INSERT INTO menu_items (item_name, category, description, price, is_available, available_for_takeaway, available_for_delivery, prep_time)
VALUES
('Margherita Pizza', 'Mains', 'Tomato, mozzarella, fresh basil.', 11.50, 1, 1, 1, 12),
('Garlic Bread', 'Starters', 'Toasted sourdough, garlic butter.', 4.50, 1, 1, 1, 6),
('Sparkling Water', 'Drinks', '330ml bottle.', 2.00, 1, 1, 1, 1);
