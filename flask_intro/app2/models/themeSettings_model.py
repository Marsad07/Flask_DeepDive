from app2.database import get_db

def get_theme():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM theme_settings WHERE id = 1")
    theme = cursor.fetchone()
    cursor.close()

    # Return defaults if no row exists yet
    if not theme:
        return {
            'id': 1,
            'color_primary':     '#8B0000',
            'color_accent':      '#D4AF37',
            'color_background':  '#F7F4EE',
            'color_surface':     '#FFFFFF',
            'color_text':        '#2C2416',
            'color_text_muted':  '#9E8C78',
            'color_sidebar_bg':  '#2C2416',
            'color_sidebar_text':'#FFFEF2',
            'font_body':         'Lato',
            'font_heading':      'Playfair Display',
            'border_radius':     '2px',
            'dark_mode':         False,
        }
    return theme


def save_theme(data):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO theme_settings (
            id, color_primary, color_accent, color_background,
            color_surface, color_text, color_text_muted,
            color_sidebar_bg, color_sidebar_text,
            font_body, font_heading, border_radius, dark_mode
        ) VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            color_primary     = VALUES(color_primary),
            color_accent      = VALUES(color_accent),
            color_background  = VALUES(color_background),
            color_surface     = VALUES(color_surface),
            color_text        = VALUES(color_text),
            color_text_muted  = VALUES(color_text_muted),
            color_sidebar_bg  = VALUES(color_sidebar_bg),
            color_sidebar_text= VALUES(color_sidebar_text),
            font_body         = VALUES(font_body),
            font_heading      = VALUES(font_heading),
            border_radius     = VALUES(border_radius),
            dark_mode         = VALUES(dark_mode)
    """, (
        data['color_primary'],
        data['color_accent'],
        data['color_background'],
        data['color_surface'],
        data['color_text'],
        data['color_text_muted'],
        data['color_sidebar_bg'],
        data['color_sidebar_text'],
        data['font_body'],
        data['font_heading'],
        data['border_radius'],
        data['dark_mode'],
    ))
    db.commit()
    cursor.close()