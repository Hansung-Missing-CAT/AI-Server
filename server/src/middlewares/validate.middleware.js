const { validationResult } = require('express-validator');
const { ValidationError } = require('../utils/errors');

function validate(req, res, next) {
  const result = validationResult(req);
  if (result.isEmpty()) return next();

  const fields = result.array().reduce((acc, item) => {
    acc[item.path] = item.msg;
    return acc;
  }, {});

  return next(new ValidationError('입력값이 올바르지 않습니다.', fields));
}

module.exports = { validate };
