const { Router } = require('express');
const checkoutRoutes = require('./checkout.routes');
const reportRoutes = require('./report.routes');
const userRoutes = require('./user.routes');

const router = Router();

router.use('/api', checkoutRoutes);
router.use('/api', reportRoutes);
router.use('/api', userRoutes);

module.exports = router;
