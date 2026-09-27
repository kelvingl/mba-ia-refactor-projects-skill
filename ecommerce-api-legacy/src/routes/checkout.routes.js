const { Router } = require('express');
const asyncHandler = require('../middlewares/asyncHandler');
const checkoutController = require('../controllers/checkout.controller');

const router = Router();

router.post('/checkout', asyncHandler(async (req, res) => {
  const { usr: username, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;

  if (!username || !email || !courseId || !cardNumber) {
    return res.status(400).json({ error: 'Bad Request' });
  }

  const result = await checkoutController.checkout({ username, email, password, courseId, cardNumber });
  res.status(200).json(result);
}));

module.exports = router;
