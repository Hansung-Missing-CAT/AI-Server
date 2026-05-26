const { Queue } = require('bullmq');
const { createRedisConnection } = require('./redis');

const connection = createRedisConnection();

function createQueue(name) {
  if (!connection) return null;
  return new Queue(name, { connection });
}

const aiAnalysisQueue = createQueue('ai-analysis');
const embeddingIndexQueue = createQueue('embedding-index');
const pushNotificationsQueue = createQueue('push-notifications');

module.exports = {
  connection,
  aiAnalysisQueue,
  embeddingIndexQueue,
  pushNotificationsQueue,
};
