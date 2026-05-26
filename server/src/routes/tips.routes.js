const router = require('express').Router();
const { body } = require('express-validator');
const { authenticate } = require('../middlewares/auth.middleware');
const { validate } = require('../middlewares/validate.middleware');
const controller = require('../controllers/tips.controller');

router.use(authenticate);

router.post(
  '/analyze',
  [body('imageUrls').isArray({ min: 3, max: 5 }).withMessage('imageUrls는 3~5장이어야 합니다.'), validate],
  controller.analyze,
);
router.get('/:tipId', controller.getTip);
router.post('/:tipId/send', [body('petId').isUUID(), validate], controller.sendTip);

module.exports = router;
