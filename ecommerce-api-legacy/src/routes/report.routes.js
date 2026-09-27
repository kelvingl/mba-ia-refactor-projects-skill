const { Router } = require('express');
const asyncHandler = require('../middlewares/asyncHandler');
const requireAdmin = require('../middlewares/requireAdmin');
const reportController = require('../controllers/report.controller');

const router = Router();

router.get('/admin/financial-report', requireAdmin, asyncHandler(async (req, res) => {
  const report = await reportController.getFinancialReport();
  res.json(report);
}));

module.exports = router;
