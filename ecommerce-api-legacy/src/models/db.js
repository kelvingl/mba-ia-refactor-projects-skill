const sqlite3 = require('sqlite3').verbose();
const { promisify } = require('util');
const bcrypt = require('bcryptjs');

function createDb() {
  const raw = new sqlite3.Database(':memory:');
  return {
    all: promisify(raw.all.bind(raw)),
    get:  promisify(raw.get.bind(raw)),
    run: (sql, params = []) => new Promise((resolve, reject) => {
      raw.run(sql, params, function (err) {
        err ? reject(err) : resolve({ lastID: this.lastID, changes: this.changes });
      });
    }),
  };
}

const db = createDb();

async function initDb() {
  await db.run('PRAGMA foreign_keys = ON');

  await db.run(`CREATE TABLE users (
    id    INTEGER PRIMARY KEY,
    name  TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    pass  TEXT NOT NULL
  )`);
  await db.run(`CREATE TABLE courses (
    id     INTEGER PRIMARY KEY,
    title  TEXT NOT NULL,
    price  REAL NOT NULL,
    active INTEGER DEFAULT 1
  )`);
  await db.run(`CREATE TABLE enrollments (
    id        INTEGER PRIMARY KEY,
    user_id   INTEGER NOT NULL REFERENCES users(id),
    course_id INTEGER NOT NULL
  )`);
  await db.run(`CREATE TABLE payments (
    id            INTEGER PRIMARY KEY,
    enrollment_id INTEGER NOT NULL REFERENCES enrollments(id),
    amount        REAL NOT NULL,
    status        TEXT NOT NULL
  )`);
  await db.run(`CREATE TABLE audit_logs (
    id         INTEGER PRIMARY KEY,
    action     TEXT NOT NULL,
    created_at DATETIME NOT NULL
  )`);

  const seedHash = bcrypt.hashSync('123', 10);
  await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
    ['Leonan', 'leonan@fullcycle.com.br', seedHash]);
  await db.run("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1)");
  await db.run("INSERT INTO courses (title, price, active) VALUES ('Docker', 497.00, 1)");
  await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
  await db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')");
}

module.exports = { db, initDb };
