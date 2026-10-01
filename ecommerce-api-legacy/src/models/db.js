const sqlite3 = require('sqlite3');
const { hashPassword } = require('../utils/crypto');

function createDb(path = ':memory:') {
  const raw = new sqlite3.Database(path);
  return {
    all: (sql, params = []) => new Promise((resolve, reject) => {
      raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    }),
    get: (sql, params = []) => new Promise((resolve, reject) => {
      raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    }),
    run: (sql, params = []) => new Promise((resolve, reject) => {
      raw.run(sql, params, function(err) {
        err ? reject(err) : resolve({ lastID: this.lastID, changes: this.changes });
      });
    }),
  };
}

async function initDb(db) {
  await db.run('PRAGMA foreign_keys = ON');
  await db.run(`CREATE TABLE IF NOT EXISTS users (
    id    INTEGER PRIMARY KEY,
    name  TEXT    NOT NULL,
    email TEXT    NOT NULL UNIQUE,
    pass  TEXT    NOT NULL
  )`);
  await db.run(`CREATE TABLE IF NOT EXISTS courses (
    id     INTEGER PRIMARY KEY,
    title  TEXT    NOT NULL,
    price  REAL    NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
  )`);
  await db.run(`CREATE TABLE IF NOT EXISTS enrollments (
    id        INTEGER PRIMARY KEY,
    user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id INTEGER NOT NULL REFERENCES courses(id)
  )`);
  await db.run(`CREATE TABLE IF NOT EXISTS payments (
    id            INTEGER PRIMARY KEY,
    enrollment_id INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
    amount        REAL    NOT NULL,
    status        TEXT    NOT NULL
  )`);
  await db.run(`CREATE TABLE IF NOT EXISTS audit_logs (
    id         INTEGER PRIMARY KEY,
    action     TEXT    NOT NULL,
    created_at DATETIME NOT NULL DEFAULT (datetime('now'))
  )`);

  const seedHash = await hashPassword('123');
  await db.run(
    'INSERT OR IGNORE INTO users (name, email, pass) VALUES (?, ?, ?)',
    ['Leonan', 'leonan@fullcycle.com.br', seedHash]
  );
  await db.run('INSERT OR IGNORE INTO courses (title, price, active) VALUES (?, ?, 1)', ['Clean Architecture', 997.00]);
  await db.run('INSERT OR IGNORE INTO courses (title, price, active) VALUES (?, ?, 1)', ['Docker', 497.00]);

  const user = await db.get('SELECT id FROM users WHERE email = ?', ['leonan@fullcycle.com.br']);
  const course = await db.get('SELECT id FROM courses WHERE title = ?', ['Clean Architecture']);
  if (user && course) {
    const existing = await db.get(
      'SELECT id FROM enrollments WHERE user_id = ? AND course_id = ?',
      [user.id, course.id]
    );
    if (!existing) {
      const enr = await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [user.id, course.id]);
      await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [enr.lastID, 997.00, 'PAID']);
    }
  }
}

let instance;
function getDb() {
  if (!instance) instance = createDb(':memory:');
  return instance;
}

module.exports = { getDb, initDb };
