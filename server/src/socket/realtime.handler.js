const { createRedisConnection } = require('../config/redis');
const { emitToUser } = require('./socket.handler');

async function registerRealtimeHandlers(io) {
  const redis = createRedisConnection();
  if (!redis) return;

  const subscriber = redis.duplicate();
  await subscriber.subscribe('tip:progress', 'tip:done');

  subscriber.on('message', (channel, message) => {
    try {
      const payload = JSON.parse(message);
      const userId = payload.userId;
      if (!userId) return;
      if (channel === 'tip:progress') {
        emitToUser(io, userId, 'tip.progress', payload);
      } else if (channel === 'tip:done') {
        emitToUser(io, userId, 'tip.done', payload);
      }
    } catch {
      // ignore malformed pub/sub payloads
    }
  });
}

module.exports = { registerRealtimeHandlers };
