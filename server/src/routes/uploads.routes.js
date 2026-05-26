const router = require('express').Router();
const { body } = require('express-validator');
const { authenticate } = require('../middlewares/auth.middleware');
const { validate } = require('../middlewares/validate.middleware');
const controller = require('../controllers/uploads.controller');

router.post(
  '/presign',
  authenticate,
  [
    body('bucket').isString().notEmpty(),
    body('fileName').isString().notEmpty(),
    body('contentType').isString().notEmpty(),
    validate,
  ],
  controller.presign,
);

module.exports = router;
