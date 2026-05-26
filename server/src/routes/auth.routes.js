const router = require('express').Router();
const { body } = require('express-validator');
const controller = require('../controllers/auth.controller');
const { validate } = require('../middlewares/validate.middleware');
const { authenticate } = require('../middlewares/auth.middleware');

router.post(
  '/signup',
  [
    body('email').isEmail().withMessage('올바른 이메일 형식이 아닙니다.'),
    body('password').isLength({ min: 8 }).withMessage('비밀번호는 8자 이상이어야 합니다.'),
    body('name').isString().notEmpty().withMessage('이름은 필수입니다.'),
    body('phone').optional().isString(),
    body('agreeTerms').custom((v) => v === true).withMessage('서비스 이용약관 동의가 필요합니다.'),
    body('agreePrivacy').custom((v) => v === true).withMessage('개인정보 처리방침 동의가 필요합니다.'),
    validate,
  ],
  controller.signup,
);

router.post(
  '/login',
  [
    body('email').isEmail().withMessage('올바른 이메일 형식이 아닙니다.'),
    body('password').notEmpty().withMessage('비밀번호는 필수입니다.'),
    validate,
  ],
  controller.login,
);

router.post('/login/google', [body('idToken').notEmpty(), validate], controller.loginWithGoogle);
router.post('/refresh', [body('refreshToken').notEmpty(), validate], controller.refresh);
router.post('/logout', authenticate, controller.logout);
router.post('/password/forgot', [body('email').isEmail(), validate], controller.forgotPassword);
router.post('/password/reset', authenticate, [body('password').isLength({ min: 8 }), validate], controller.resetPassword);

module.exports = router;
