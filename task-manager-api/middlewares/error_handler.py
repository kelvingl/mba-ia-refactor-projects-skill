import logging
from flask import jsonify
from marshmallow.exceptions import ValidationError as MarshmallowValidationError

logger = logging.getLogger('app')


class AppError(Exception):
    status_code = 500
    message = 'Erro interno'

    def __init__(self, message=None):
        if message:
            self.message = message
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    message = 'Recurso não encontrado'


class BadRequestError(AppError):
    status_code = 400
    message = 'Dados inválidos'


class ConflictError(AppError):
    status_code = 409
    message = 'Conflito de dados'


class UnauthorizedError(AppError):
    status_code = 401
    message = 'Não autorizado'


class ForbiddenError(AppError):
    status_code = 403
    message = 'Acesso proibido'


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({'error': err.message}), err.status_code

    @app.errorhandler(MarshmallowValidationError)
    def handle_validation_error(err):
        return jsonify({'error': 'Dados inválidos', 'details': err.messages}), 400

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception('Erro não tratado')
        return jsonify({'error': 'Erro interno'}), 500
