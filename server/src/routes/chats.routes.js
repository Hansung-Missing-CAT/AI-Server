const router = require('express').Router();
const { body, query } = require('express-validator');
const { authenticate } = require('../middlewares/auth.middleware');
const { validate } = require('../middlewares/validate.middleware');
const controller = require('../controllers/chats.controller');

router.use(authenticate);

router.get('/', [query('q').optional().isString(), query('limit').optional().isInt({ min: 1, max: 100 }), validate], controller.getChatList);
router.get('/:chatId', controller.getChat);
router.get('/:chatId/messages', controller.getMessages);
router.post(
  '/:chatId/messages',
  [body('type').optional().isIn(['text', 'image', 'location', 'tipCard']), validate],
  controller.sendMessage,
);
router.post('/',
  [body('petId').isUUID(), body('otherUserId').isUUID(), validate],
  controller.createChat,
);
router.post('/:chatId/read', controller.markRead);
router.post('/:chatId/leave', controller.leaveChat);
router.post('/:chatId/report', [body('reason').isString().trim().isLength({ min: 1, max: 1000 }), validate], controller.reportChat);

module.exports = router;
