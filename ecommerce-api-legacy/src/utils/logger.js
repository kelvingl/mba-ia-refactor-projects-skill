const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };
const current = LEVELS[process.env.LOG_LEVEL || 'info'] ?? LEVELS.info;

function log(level, message, meta = {}) {
  if (LEVELS[level] > current) return;
  const entry = { ts: new Date().toISOString(), level, message, ...meta };
  (level === 'error' ? console.error : console.log)(JSON.stringify(entry));
}

module.exports = {
  info:  (msg, meta) => log('info',  msg, meta),
  warn:  (msg, meta) => log('warn',  msg, meta),
  error: (msg, meta) => log('error', msg, meta),
  debug: (msg, meta) => log('debug', msg, meta),
};
