const router = require('express').Router();
const { body, query } = require('express-validator');
const controller = require('../controllers/pets.controller');
const { authenticate, optionalAuth } = require('../middlewares/auth.middleware');
const { validate } = require('../middlewares/validate.middleware');

router.get(
  '/',
  [
    query('sort').optional().isIn(['latest', 'likes', 'comments']),
    query('status').optional().isIn(['실종', '찾음']),
    query('limit').optional().isInt({ min: 1, max: 100 }),
    validate,
  ],
  optionalAuth,
  controller.listPets,
);

router.get('/:id', optionalAuth, controller.getPet);

router.post(
  '/',
  authenticate,
  [
    body('name').isString().notEmpty(),
    body('breed').isString().notEmpty(),
    body('photoUrls').isArray({ min: 5 }).withMessage('photoUrls는 최소 5장 이상이어야 합니다.'),
    body('lostDate')
      .optional()
      .isISO8601()
      .custom((v) => new Date(v).getTime() <= Date.now())
      .withMessage('lostDate는 미래 날짜일 수 없습니다.'),
    validate,
  ],
  controller.createPet,
);

router.patch('/:id', authenticate, controller.patchPet);
router.delete('/:id', authenticate, controller.removePet);

router.post('/:id/like', authenticate, controller.likePet);
router.delete('/:id/like', authenticate, controller.unlikePet);

router.get('/:id/comments', optionalAuth, controller.listComments);
router.post(
  '/:id/comments',
  authenticate,
  [body('content').isString().trim().isLength({ min: 1, max: 1000 }), validate],
  controller.createComment,
);

module.exports = router;
