class AppError extends Error {
  constructor(message, statusCode = 500) {
    super(message);
    this.statusCode = statusCode;
  }
}

class NotFoundError extends AppError {
  constructor(msg = 'Recurso não encontrado') { super(msg, 404); }
}

class ValidationError extends AppError {
  constructor(msg = 'Dados inválidos') { super(msg, 400); }
}

class UnauthorizedError extends AppError {
  constructor(msg = 'Unauthorized') { super(msg, 401); }
}

class PaymentRefusedError extends AppError {
  constructor(msg = 'Pagamento recusado') { super(msg, 400); }
}

module.exports = { AppError, NotFoundError, ValidationError, UnauthorizedError, PaymentRefusedError };
