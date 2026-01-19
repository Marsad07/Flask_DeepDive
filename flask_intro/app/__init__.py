from flask import Flask

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = "ajd82h9d8ahd92h9ahd92h9ahd92h9ahd9"

    from app.views.general import general_bp
    from app.views.auth import auth_bp
    from app.views.tasks import tasks_bp
    from app.views.subjects import subjects_bp
    from app.views.context import inject_subjects
    from app.views.atlas import atlas_bp

    app.register_blueprint(general_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(subjects_bp)
    app.context_processor(inject_subjects)
    app.register_blueprint(atlas_bp)

    return app
