const router = require('express').Router();
const { authenticate } = require('../middlewares/auth.middleware');
const controller = require('../controllers/notifications.controller');

router.use(authenticate);

router.get('/', controller.listNotifications);
router.get('/unread-count', controller.unreadCount);
router.post('/:id/read', controller.markRead);
router.post('/read-all', controller.readAll);

module.exports = router;
