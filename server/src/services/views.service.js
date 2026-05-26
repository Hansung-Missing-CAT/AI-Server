const { supabaseAdmin } = require('../config/supabase');
const { createRedisConnection } = require('../config/redis');

const VIEW_KEY_PREFIX = 'pet:views:';

function getViewKey(petId) {
  return `${VIEW_KEY_PREFIX}${petId}`;
}

async function incrementView(petId) {
  const redis = createRedisConnection();
  if (!redis) return;
  await redis.incr(getViewKey(petId));
}

async function flushViewBuffer() {
  const redis = createRedisConnection();
  if (!redis || !supabaseAdmin) return { flushed: 0 };

  let cursor = '0';
  const keys = [];
  do {
    const [next, batch] = await redis.scan(cursor, 'MATCH', `${VIEW_KEY_PREFIX}*`, 'COUNT', 200);
    cursor = next;
    keys.push(...batch);
  } while (cursor !== '0');

  let flushed = 0;
  for (const key of keys) {
    const value = await redis.get(key);
    const delta = Number.parseInt(value || '0', 10);
    if (!delta) {
      await redis.del(key);
      continue;
    }

    const petId = key.slice(VIEW_KEY_PREFIX.length);
    await supabaseAdmin.rpc('increment_pet_views', { p_pet_id: petId, p_delta: delta }).catch(() => undefined);
    await redis.del(key);
    flushed += 1;
  }

  return { flushed };
}

function startViewFlushJob(intervalMs = 60_000) {
  const timer = setInterval(() => {
    flushViewBuffer().catch((err) => {
      console.error('View flush failed:', err.message);
    });
  }, intervalMs);
  timer.unref?.();
}

module.exports = {
  incrementView,
  flushViewBuffer,
  startViewFlushJob,
};
