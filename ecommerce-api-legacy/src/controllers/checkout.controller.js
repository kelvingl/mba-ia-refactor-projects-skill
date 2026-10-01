const userModel = require('../models/user.model');
const courseModel = require('../models/course.model');
const enrollmentModel = require('../models/enrollment.model');
const paymentModel = require('../models/payment.model');
const { getDb } = require('../models/db');
const { NotFoundError, ValidationError, PaymentRefusedError } = require('../utils/errors');
const logger = require('../utils/logger');

async function checkout({ name, email, password, courseId, cardNumber }) {
  const course = await courseModel.findActiveById(courseId);
  if (!course) throw new NotFoundError('Curso não encontrado');

  let user = await userModel.findByEmail(email);
  let userId;
  if (!user) {
    if (!password) throw new ValidationError('Senha é obrigatória para novo usuário');
    userId = await userModel.create(name, email, password);
  } else {
    userId = user.id;
  }

  const status = cardNumber.startsWith('4') ? 'PAID' : 'DENIED';
  if (status === 'DENIED') throw new PaymentRefusedError();

  const enrollmentId = await enrollmentModel.create(userId, courseId);
  await paymentModel.create(enrollmentId, course.price, status);
  await getDb().run(
    "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
    [`Checkout course ${courseId} by user ${userId}`]
  );

  logger.info('checkout completed', { userId, courseId, enrollmentId });
  return { msg: 'Sucesso', enrollment_id: enrollmentId };
}

module.exports = { checkout };
