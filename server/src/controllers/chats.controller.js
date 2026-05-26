const chatService = require('../services/chat.service');
const { success } = require('../utils/response');
const { parseLimit } = require('../utils/pagination');
const { emitToUser } = require('../socket/socket.handler');

async function getChatList(req, res, next) {
  try {
    const result = await chatService.getChatList(req.user.id, {
      q: req.query.q,
      cursor: req.query.cursor,
      limit: parseLimit(req.query.limit),
    });
    return success(res, result);
  } catch (err) {
    next(err);
  }
}

async function getChat(req, res, next) {
  try {
    const data = await chatService.getChatById(req.params.chatId, req.user.id);
    return success(res, data);
  } catch (err) {
    next(err);
  }
}

async function getMessages(req, res, next) {
  try {
    const data = await chatService.getChatMessages(req.params.chatId, req.user.id, {
      cursor: req.query.cursor,
      limit: parseLimit(req.query.limit),
    });
    return success(res, data);
  } catch (err) {
    next(err);
  }
}

async function sendMessage(req, res, next) {
  try {
    const chat = await chatService.getChatById(req.params.chatId, req.user.id);
    const message = await chatService.sendMessage(req.params.chatId, req.user.id, req.body);
    const io = req.app.get('io');
    for (const participantId of chat.participant_ids || []) {
      if (participantId === req.user.id) continue;
      emitToUser(io, participantId, 'message.new', { chatId: chat.id, message });
      emitToUser(io, participantId, 'chat.updated', { chatId: chat.id });
    }
    return success(res, message, 201);
  } catch (err) {
    next(err);
  }
}

async function createChat(req, res, next) {
  try {
    const { petId, otherUserId } = req.body;
    const chat = await chatService.createOrGetChat(petId, req.user.id, otherUserId);
    return success(res, chat, 201);
  } catch (err) {
    next(err);
  }
}

async function markRead(req, res, next) {
  try {
    const chat = await chatService.getChatById(req.params.chatId, req.user.id);
    await chatService.markAsRead(req.params.chatId, req.user.id);
    const io = req.app.get('io');
    for (const participantId of chat.participant_ids || []) {
      if (participantId === req.user.id) continue;
      emitToUser(io, participantId, 'message.read', { chatId: chat.id, userId: req.user.id });
    }
    return success(res, { success: true });
  } catch (err) {
    next(err);
  }
}

async function leaveChat(req, res, next) {
  try {
    await chatService.leaveChat(req.params.chatId, req.user.id);
    return success(res, { success: true });
  } catch (err) {
    next(err);
  }
}

async function reportChat(req, res, next) {
  try {
    const data = await chatService.reportChat(req.params.chatId, req.user.id, req.body.reason);
    return success(res, data, 201);
  } catch (err) {
    next(err);
  }
}

module.exports = {
  getChatList,
  getChat,
  getMessages,
  sendMessage,
  createChat,
  markRead,
  leaveChat,
  reportChat,
};
