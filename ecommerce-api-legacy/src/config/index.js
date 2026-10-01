require('dotenv').config();

function requiredEnv(name) {
  const value = (process.env[name] || '').trim();
  if (!value) throw new Error(`${name} não definida — copie .env.example para .env e preencha`);
  return value;
}

module.exports = {
  port: parseInt(process.env.PORT || '3000', 10),
  adminToken: requiredEnv('ADMIN_TOKEN'),
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
};
