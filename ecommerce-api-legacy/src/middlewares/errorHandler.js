const logger = require('../utils/logger');
const { AppError } = require('../utils/errors');

function errorHandler(err, req, res, next) {
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({ error: err.message });
  }
  logger.error('unhandled error', { message: err.message, stack: err.stack });
  res.status(500).json({ error: 'Erro interno do servidor' });
}

module.exports = errorHandler;
