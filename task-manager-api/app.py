import logging
from datetime import datetime, timezone
from flask import Flask
from flask_cors import CORS

from src.config.settings import settings
from src.models.database import db
from src.middlewares.error_handler import register_error_handlers
from src.middlewares.auth import init_auth
from src.views.task_routes import task_bp
from src.views.user_routes import user_bp
from src.views.category_routes import category_bp
from src.views.report_routes import report_bp

logging.basicConfig(level=logging.INFO if settings.DEBUG else logging.WARNING)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = settings.SECRET_KEY

CORS(app)
db.init_app(app)
register_error_handlers(app)
init_auth(app)

app.register_blueprint(task_bp)
app.register_blueprint(user_bp)
app.register_blueprint(category_bp)
app.register_blueprint(report_bp)


@app.route('/')
def index():
    return {'message': 'Task Manager API', 'version': '1.0'}


@app.route('/health')
def health():
    return {'status': 'ok', 'timestamp': str(datetime.now(timezone.utc))}


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=settings.DEBUG, host='0.0.0.0', port=5000)
