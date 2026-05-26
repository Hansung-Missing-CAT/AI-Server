const { supabaseAdmin } = require('../config/supabase');
const { AppError } = require('../utils/errors');
const { success } = require('../utils/response');

function ensureSupabase() {
  if (!supabaseAdmin) {
    throw new AppError('SUPABASE_NOT_CONFIGURED', 'Supabase 환경 변수가 설정되지 않았습니다.', 500);
  }
}

async function getMe(req, res, next) {
  try {
    ensureSupabase();
    const userId = req.user?.id;
    const { data, error } = await supabaseAdmin
      .from('users')
      .select('id, name, phone, avatar_url, is_online, last_seen_at, agree_marketing, created_at')
      .eq('id', userId)
      .single();

    if (error) {
      throw new AppError('USER_NOT_FOUND', '사용자 정보를 찾을 수 없습니다.', 404);
    }
    return success(res, data);
  } catch (err) {
    next(err);
  }
}

async function patchMe(req, res, next) {
  try {
    ensureSupabase();
    const userId = req.user?.id;
    const patch = {};
    for (const key of ['name', 'phone', 'avatar_url']) {
      if (req.body[key] !== undefined) patch[key] = req.body[key];
    }

    const { data, error } = await supabaseAdmin
      .from('users')
      .update(patch)
      .eq('id', userId)
      .select('id, name, phone, avatar_url, is_online, last_seen_at, agree_marketing, created_at')
      .single();

    if (error) {
      throw new AppError('USER_UPDATE_FAILED', '사용자 정보 수정에 실패했습니다.', 400);
    }
    return success(res, data);
  } catch (err) {
    next(err);
  }
}

module.exports = {
  getMe,
  patchMe,
};
