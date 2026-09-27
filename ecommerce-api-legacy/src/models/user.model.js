const { db } = require('./db');

async function findByEmail(email) {
  return db.get('SELECT id, name, email FROM users WHERE email = ?', [email]);
}

async function create(name, email, passHash) {
  return db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passHash]);
}

async function deleteById(id) {
  await db.run(
    'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)',
    [id]
  );
  await db.run('DELETE FROM enrollments WHERE user_id = ?', [id]);
  return db.run('DELETE FROM users WHERE id = ?', [id]);
}

module.exports = { findByEmail, create, deleteById };
