import logging

from flask import Flask
from flask_cors import CORS

from src.config.settings import settings
from src.middlewares.error_handler import register_error_handlers
from src.middlewares.auth import init_auth
from src.models.database import init_app as init_db
from src.views.health_routes import health_bp
from src.views.produto_routes import produto_bp
from src.views.usuario_routes import usuario_bp
from src.views.pedido_routes import pedido_bp
from src.views.relatorio_routes import relatorio_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    app.config["DATABASE_PATH"] = settings.DATABASE_PATH

    logging.basicConfig(level=logging.DEBUG if settings.DEBUG else logging.WARNING)

    CORS(app)
    register_error_handlers(app)
    init_auth(app)
    init_db(app)

    app.register_blueprint(health_bp)
    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(pedido_bp)
    app.register_blueprint(relatorio_bp)

    return app
