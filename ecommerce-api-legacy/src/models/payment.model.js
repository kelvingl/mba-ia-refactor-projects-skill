const { getDb } = require('./db');

async function create(enrollmentId, amount, status) {
  const result = await getDb().run(
    'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
    [enrollmentId, amount, status]
  );
  return result.lastID;
}

module.exports = { create };
