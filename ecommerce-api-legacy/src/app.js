const express = require('express');
const config = require('./config');
const { getDb, initDb } = require('./models/db');
const routes = require('./routes');
const errorHandler = require('./middlewares/errorHandler');
const logger = require('./utils/logger');

const app = express();
app.use(express.json());
app.use(routes);
app.use(errorHandler);

async function start() {
  await initDb(getDb());
  app.listen(config.port, () => {
    logger.info('Ecommerce API running', { port: config.port });
  });
}

start().catch(err => {
  console.error('Boot failed:', err.message);
  process.exit(1);
});
