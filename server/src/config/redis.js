const IORedis = require('ioredis');

let redis;

function createRedisConnection() {
  if (redis) return redis;

  const url = process.env.UPSTASH_REDIS_URL;
  if (!url) return null;

  redis = new IORedis(url, {
    maxRetriesPerRequest: null,
    tls: url.startsWith('rediss://') ? {} : undefined,
  });

  return redis;
}

module.exports = {
  createRedisConnection,
};
