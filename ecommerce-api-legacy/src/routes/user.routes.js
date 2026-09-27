const { Router } = require('express');
const asyncHandler = require('../middlewares/asyncHandler');
const requireAdmin = require('../middlewares/requireAdmin');
const userController = require('../controllers/user.controller');

const router = Router();

router.delete('/users/:id', requireAdmin, asyncHandler(async (req, res) => {
  await userController.deleteUser(req.params.id);
  res.json({ success: true, message: 'Usuário removido com sucesso.' });
}));

module.exports = router;
