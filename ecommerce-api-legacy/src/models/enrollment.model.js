const { db } = require('./db');

async function createEnrollment(userId, courseId) {
  return db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
}

async function createPayment(enrollmentId, amount, status) {
  return db.run(
    'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
    [enrollmentId, amount, status]
  );
}

async function logAudit(action) {
  return db.run(
    "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
    [action]
  );
}

async function getFinancialReport() {
  const rows = await db.all(`
    SELECT
      c.id    AS courseId,
      c.title,
      u.name  AS studentName,
      p.amount,
      p.status
    FROM courses c
    LEFT JOIN enrollments e ON e.course_id = c.id
    LEFT JOIN users       u ON u.id = e.user_id
    LEFT JOIN payments    p ON p.enrollment_id = e.id
    ORDER BY c.id
  `);

  const map = new Map();
  for (const r of rows) {
    if (!map.has(r.courseId)) {
      map.set(r.courseId, { course: r.title, revenue: 0, students: [] });
    }
    const entry = map.get(r.courseId);
    if (r.studentName) {
      if (r.status === 'PAID') entry.revenue += r.amount;
      entry.students.push({ student: r.studentName, paid: r.amount || 0 });
    }
  }
  return Array.from(map.values());
}

module.exports = { createEnrollment, createPayment, logAudit, getFinancialReport };
