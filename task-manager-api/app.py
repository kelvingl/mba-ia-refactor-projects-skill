import logging
from datetime import datetime, timezone
from flask import Flask
from flask_cors import CORS
from config.settings import settings
from models.database import db
from models import User, Task, Category  # registers all models with SQLAlchemy
from views.task_routes import task_bp
from views.user_routes import user_bp
from views.report_routes import report_bp
from middlewares.error_handler import register_error_handlers

logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
)


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = settings.SECRET_KEY

    CORS(app)
    db.init_app(app)
    register_error_handlers(app)

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(datetime.now(timezone.utc))}

    @app.route('/')
    def index():
        return {'message': 'Task Manager API', 'version': '1.0'}

    return app


app = create_app()

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=settings.DEBUG, host='0.0.0.0', port=port)
