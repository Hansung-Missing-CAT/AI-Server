const notificationService = require('../services/notification.service');
const { success } = require('../utils/response');
const { parseLimit } = require('../utils/pagination');

async function listNotifications(req, res, next) {
  try {
    const data = await notificationService.getNotifications(req.user.id, {
      unreadOnly: req.query.unreadOnly === 'true',
      cursor: req.query.cursor,
      limit: parseLimit(req.query.limit),
    });
    return success(res, data);
  } catch (err) {
    next(err);
  }
}

async function unreadCount(req, res, next) {
  try {
    const count = await notificationService.getUnreadCount(req.user.id);
    return success(res, { count });
  } catch (err) {
    next(err);
  }
}

async function markRead(req, res, next) {
  try {
    await notificationService.markAsRead(req.user.id, req.params.id);
    return success(res, { success: true });
  } catch (err) {
    next(err);
  }
}

async function readAll(req, res, next) {
  try {
    await notificationService.markAllAsRead(req.user.id);
    return success(res, { success: true });
  } catch (err) {
    next(err);
  }
}

module.exports = {
  listNotifications,
  unreadCount,
  markRead,
  readAll,
};
