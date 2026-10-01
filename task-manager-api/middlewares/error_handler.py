from flask import jsonify


class AppError(Exception):
    status_code = 500
    message = "Erro interno"

    def __init__(self, message=None):
        if message:
            self.message = message
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    message = "Recurso não encontrado"


class ValidationError(AppError):
    status_code = 400
    message = "Dados inválidos"


class UnauthorizedError(AppError):
    status_code = 401
    message = "Não autorizado"


class ForbiddenError(AppError):
    status_code = 403
    message = "Acesso negado"


class ConflictError(AppError):
    status_code = 409
    message = "Conflito"


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"error": err.message}), err.status_code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        app.logger.exception("Erro não tratado: %s", err)
        return jsonify({"error": "Erro interno"}), 500
