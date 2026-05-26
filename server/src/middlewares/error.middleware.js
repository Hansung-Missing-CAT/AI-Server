const { AppError } = require('../utils/errors');
const { error } = require('../utils/response');

function notFoundHandler(req, res, next) {
  next(new AppError('NOT_FOUND', '요청한 엔드포인트를 찾을 수 없습니다.', 404));
}

function errorHandler(err, req, res, next) {
  if (res.headersSent) return next(err);

  if (err instanceof AppError) {
    return error(res, err.code, err.message, err.status, err.fields);
  }

  console.error(err);
  return error(res, 'INTERNAL_SERVER_ERROR', '서버 오류가 발생했습니다.', 500);
}

module.exports = { notFoundHandler, errorHandler };
