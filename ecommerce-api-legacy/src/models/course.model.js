const { getDb } = require('./db');

async function findActiveById(id) {
  return getDb().get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
}

async function findAll({ limit = 50, offset = 0 } = {}) {
  return getDb().all('SELECT * FROM courses LIMIT ? OFFSET ?', [limit, offset]);
}

module.exports = { findActiveById, findAll };
