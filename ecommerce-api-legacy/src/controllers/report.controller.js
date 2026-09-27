const enrollmentModel = require('../models/enrollment.model');

async function getFinancialReport() {
  return enrollmentModel.getFinancialReport();
}

module.exports = { getFinancialReport };
