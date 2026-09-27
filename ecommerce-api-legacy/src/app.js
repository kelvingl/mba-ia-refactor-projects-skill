const express = require('express');
const { initDb } = require('./models/db');
const routes = require('./routes');
const errorHandler = require('./middlewares/errorHandler');
const config = require('./config');

const app = express();
app.use(express.json());
app.use(routes);
app.use(errorHandler);

initDb()
  .then(() => {
    app.listen(config.port, () => {
      console.log(`Frankenstein LMS rodando na porta ${config.port}...`);
    });
  })
  .catch(err => {
    console.error('Failed to initialize DB:', err);
    process.exit(1);
  });
