class AppError extends Error {
  constructor(code, message, status = 500, fields = undefined) {
    super(message);
    this.name = this.constructor.name;
    this.code = code;
    this.status = status;
    this.fields = fields;
  }
}

class NotFoundError extends AppError {
  constructor(message = '요청한 리소스를 찾을 수 없습니다.') {
    super('NOT_FOUND', message, 404);
  }
}

class ForbiddenError extends AppError {
  constructor(message = '접근 권한이 없습니다.') {
    super('FORBIDDEN', message, 403);
  }
}

class ValidationError extends AppError {
  constructor(message = '입력값이 올바르지 않습니다.', fields = undefined) {
    super('VALIDATION_ERROR', message, 400, fields);
  }
}

module.exports = {
  AppError,
  NotFoundError,
  ForbiddenError,
  ValidationError,
};
