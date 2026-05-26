const path = require('path');
const { supabaseAdmin } = require('../config/supabase');
const { AppError } = require('../utils/errors');

function assertSupabase() {
  if (!supabaseAdmin) {
    throw new AppError('SUPABASE_NOT_CONFIGURED', 'Supabase 환경 변수가 설정되지 않았습니다.', 500);
  }
}

function sanitizeFileName(fileName) {
  return path.basename(fileName).replace(/\s+/g, '_');
}

async function createPresignedUpload({ userId, bucket, fileName, contentType }) {
  assertSupabase();
  const safeName = sanitizeFileName(fileName);
  const objectPath = `${userId}/${Date.now()}-${safeName}`;

  const { data, error } = await supabaseAdmin.storage.from(bucket).createSignedUploadUrl(objectPath);
  if (error || !data) {
    throw new AppError('UPLOAD_PRESIGN_FAILED', '업로드 URL 생성에 실패했습니다.', 400);
  }

  const { data: publicData } = supabaseAdmin.storage.from(bucket).getPublicUrl(objectPath);
  return {
    bucket,
    path: objectPath,
    contentType,
    token: data.token,
    uploadUrl: data.signedUrl,
    fileUrl: publicData?.publicUrl || null,
    expiresIn: 7200,
  };
}

module.exports = { createPresignedUpload };
