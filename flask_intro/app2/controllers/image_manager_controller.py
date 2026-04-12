import os
from flask import request, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from app2.models.image_model import get_image, set_image

def image_manager_controller():
    if request.method == "POST":
        image_key = request.form["image_key"]
        file = request.files["image_file"]

        if file:
            filename = secure_filename(file.filename)
            # This builds the correct path regardless of OS
            upload_folder = os.path.join(current_app.root_path, 'static', 'imgs')
            save_path = os.path.join(upload_folder, filename)
            file.save(save_path)
            set_image(image_key, f"/static/imgs/{filename}")

        return redirect(url_for("image.image_manager"))

    return {
        "hero": get_image("hero"),
        "dish1": get_image("dish1"),
        "dish2": get_image("dish2"),
        "dish3": get_image("dish3"),
    }