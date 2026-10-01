const { Router } = require('express');
const userController = require('../controllers/user.controller');

const router = Router();
const asyncHandler = fn => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

router.delete('/api/users/:id', asyncHandler(async (req, res) => {
  const result = await userController.deleteUser(Number(req.params.id));
  res.json(result);
}));

module.exports = router;
