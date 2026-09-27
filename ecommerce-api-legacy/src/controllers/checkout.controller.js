const courseModel = require('../models/course.model');
const userModel = require('../models/user.model');
const enrollmentModel = require('../models/enrollment.model');
const { hashPassword } = require('../utils/crypto');
const logger = require('../utils/logger');

async function checkout({ username, email, password, courseId, cardNumber }) {
  const course = await courseModel.findActiveById(courseId);
  if (!course) {
    const err = new Error('Curso não encontrado');
    err.statusCode = 404;
    throw err;
  }

  let user = await userModel.findByEmail(email);
  if (!user) {
    const hash = await hashPassword(password || '123456');
    const result = await userModel.create(username, email, hash);
    user = { id: result.lastID };
  }

  const status = String(cardNumber).startsWith('4') ? 'PAID' : 'DENIED';
  if (status === 'DENIED') {
    const err = new Error('Pagamento recusado');
    err.statusCode = 400;
    throw err;
  }

  logger.info(`Payment processed for course ${courseId}`);
  const enr = await enrollmentModel.createEnrollment(user.id, courseId);
  await enrollmentModel.createPayment(enr.lastID, course.price, status);
  await enrollmentModel.logAudit(`Checkout curso ${courseId} por ${user.id}`);

  return { msg: 'Sucesso', enrollment_id: enr.lastID };
}

module.exports = { checkout };
