const router = require('express').Router();
const { body, param } = require('express-validator');
const { authenticate } = require('../middlewares/auth.middleware');
const { validate } = require('../middlewares/validate.middleware');
const controller = require('../controllers/devices.controller');

router.use(authenticate);

router.post(
  '/register',
  [
    body('token').isString().trim().isLength({ min: 10 }),
    body('platform').isIn(['android', 'ios', 'web']),
    validate,
  ],
  controller.registerDevice,
);

router.delete(
  '/:tokenId',
  [param('tokenId').isUUID(), validate],
  controller.removeDevice,
);

module.exports = router;
