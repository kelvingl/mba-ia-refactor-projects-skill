const { Router } = require('express');
const { requireAdmin } = require('../middlewares/auth');
const checkoutRoutes = require('./checkout.routes');
const reportRoutes = require('./report.routes');
const userRoutes = require('./user.routes');

const router = Router();

// Public routes — allowlist explicit (everything after requireAdmin is protected)
router.use(checkoutRoutes);

// Admin-protected routes — mounted after the guard; order is the access policy
router.use(requireAdmin);
router.use(reportRoutes);
router.use(userRoutes);

module.exports = router;
