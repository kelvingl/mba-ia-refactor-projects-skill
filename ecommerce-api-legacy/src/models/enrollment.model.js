const { getDb } = require('./db');

async function create(userId, courseId) {
  const result = await getDb().run(
    'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
    [userId, courseId]
  );
  return result.lastID;
}

async function getReportData() {
  const courses = await getDb().all('SELECT * FROM courses');
  return Promise.all(courses.map(async (course) => {
    const rows = await getDb().all(
      `SELECT u.name, p.amount, p.status
       FROM enrollments e
       LEFT JOIN users u    ON u.id = e.user_id
       LEFT JOIN payments p ON p.enrollment_id = e.id
       WHERE e.course_id = ?`,
      [course.id]
    );
    const revenue = rows
      .filter(r => r.status === 'PAID')
      .reduce((acc, r) => acc + (r.amount || 0), 0);
    return {
      course: course.title,
      revenue,
      students: rows.map(r => ({ student: r.name || 'Unknown', paid: r.amount || 0 })),
    };
  }));
}

module.exports = { create, getReportData };
