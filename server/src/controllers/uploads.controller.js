const { AppError } = require('../utils/errors');
const { success } = require('../utils/response');
const storageService = require('../services/storage.service');

const allowedBuckets = new Set(['pet-photos', 'chat-attachments', 'avatars']);
const allowedContentTypes = new Set(['image/jpeg', 'image/png', 'image/webp']);

async function presign(req, res, next) {
  try {
    const { bucket, fileName, contentType } = req.body;
    if (!allowedBuckets.has(bucket)) throw new AppError('INVALID_BUCKET', '허용되지 않은 버킷입니다.', 400);
    if (!allowedContentTypes.has(contentType)) {
      throw new AppError('INVALID_CONTENT_TYPE', '허용되지 않은 파일 형식입니다.', 400);
    }
    if (!fileName) throw new AppError('INVALID_FILE_NAME', 'fileName은 필수입니다.', 400);

    const data = await storageService.createPresignedUpload({
      userId: req.user.id,
      bucket,
      fileName,
      contentType,
    });
    return success(res, data, 201);
  } catch (err) {
    next(err);
  }
}

module.exports = { presign };
