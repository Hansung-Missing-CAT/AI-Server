const { embeddingIndexQueue } = require('../../config/bullmq');

async function enqueueEmbeddingIndex(payload) {
  if (!embeddingIndexQueue) throw new Error('embedding-index queue is not configured');
  return embeddingIndexQueue.add('index-pet', payload);
}

module.exports = { enqueueEmbeddingIndex };
