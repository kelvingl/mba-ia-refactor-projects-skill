const enrollmentModel = require('../models/enrollment.model');

async function financialReport() {
  return enrollmentModel.getReportData();
}

module.exports = { financialReport };
