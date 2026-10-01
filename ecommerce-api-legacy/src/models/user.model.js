const { getDb } = require('./db');
const { hashPassword } = require('../utils/crypto');

async function findByEmail(email) {
  return getDb().get('SELECT id, name, email FROM users WHERE email = ?', [email]);
}

async function create(name, email, password) {
  const hash = await hashPassword(password);
  const result = await getDb().run(
    'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
    [name, email, hash]
  );
  return result.lastID;
}

async function remove(id) {
  await getDb().run(
    'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)',
    [id]
  );
  await getDb().run('DELETE FROM enrollments WHERE user_id = ?', [id]);
  const result = await getDb().run('DELETE FROM users WHERE id = ?', [id]);
  return result.changes;
}

module.exports = { findByEmail, create, remove };
