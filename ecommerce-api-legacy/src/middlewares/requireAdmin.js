const config = require('../config');

function requireAdmin(req, res, next) {
  if (!config.adminToken) return next();
  if (req.headers['x-admin-token'] !== config.adminToken) {
    const err = new Error('Unauthorized');
    err.statusCode = 401;
    return next(err);
  }
  next();
}

module.exports = requireAdmin;
