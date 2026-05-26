const { aiAnalysisQueue } = require('../../config/bullmq');

async function enqueueAiAnalysis(payload) {
  if (!aiAnalysisQueue) throw new Error('ai-analysis queue is not configured');
  return aiAnalysisQueue.add('analyze-tip', payload);
}

module.exports = { enqueueAiAnalysis };
