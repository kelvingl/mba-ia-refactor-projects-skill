const { Router } = require('express');
const reportController = require('../controllers/report.controller');

const router = Router();
const asyncHandler = fn => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

router.get('/api/admin/financial-report', asyncHandler(async (req, res) => {
  const report = await reportController.financialReport();
  res.json(report);
}));

module.exports = router;
