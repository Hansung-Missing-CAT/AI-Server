const router = require('express').Router();
const { body } = require('express-validator');
const { authenticate } = require('../middlewares/auth.middleware');
const { validate } = require('../middlewares/validate.middleware');
const controller = require('../controllers/users.controller');

router.get('/me', authenticate, controller.getMe);
router.patch(
  '/me',
  authenticate,
  [
    body('name').optional().isString().notEmpty(),
    body('phone').optional().isString(),
    body('avatar_url').optional().isString(),
    validate,
  ],
  controller.patchMe,
);

module.exports = router;
