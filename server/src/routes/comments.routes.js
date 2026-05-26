const router = require('express').Router();
const { authenticate } = require('../middlewares/auth.middleware');
const { removeComment } = require('../controllers/pets.controller');

router.delete('/:commentId', authenticate, removeComment);

module.exports = router;
