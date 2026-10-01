const crypto = require('crypto');
const config = require('../config');
const { UnauthorizedError } = require('../utils/errors');

function safeEqual(provided, expected) {
  const a = Buffer.from(String(provided));
  const b = Buffer.from(String(expected));
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

function requireAdmin(req, res, next) {
  const provided = req.get('x-admin-token');
  if (!provided || !safeEqual(provided, config.adminToken)) {
    return next(new UnauthorizedError('Unauthorized'));
  }
  next();
}

module.exports = { requireAdmin };
