import os
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS


def create_app():
    from config.settings import settings
    from models.database import db
    from middlewares.error_handler import register_error_handlers
    from middlewares.auth import init_auth
    from views.user_routes import user_bp
    from views.task_routes import task_bp
    from views.report_routes import report_bp

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = settings.SECRET_KEY

    CORS(app)
    db.init_app(app)

    register_error_handlers(app)
    init_auth(app)

    app.register_blueprint(user_bp)
    app.register_blueprint(task_bp)
    app.register_blueprint(report_bp)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "timestamp": str(datetime.now())})

    @app.route("/")
    def index():
        return jsonify({"message": "Task Manager API", "version": "1.0"})

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    from config.settings import settings
    port = int(os.environ.get("PORT", "5000"))
    app.run(debug=settings.DEBUG, host="0.0.0.0", port=port)
