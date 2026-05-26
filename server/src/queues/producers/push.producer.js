const { pushNotificationsQueue } = require('../../config/bullmq');

async function enqueuePushNotification(payload) {
  if (!pushNotificationsQueue) throw new Error('push-notifications queue is not configured');
  return pushNotificationsQueue.add('send-push', payload);
}

module.exports = { enqueuePushNotification };
