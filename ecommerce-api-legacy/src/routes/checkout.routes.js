const { Router } = require('express');
const checkoutController = require('../controllers/checkout.controller');
const { ValidationError } = require('../utils/errors');

const router = Router();
const asyncHandler = fn => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

router.post('/api/checkout', asyncHandler(async (req, res) => {
  const { usr: name, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;
  if (!name || !email || !courseId || !cardNumber) {
    throw new ValidationError('Campos obrigatórios: usr, eml, c_id, card');
  }
  const result = await checkoutController.checkout({ name, email, password, courseId, cardNumber });
  res.status(200).json(result);
}));

module.exports = router;
