const { supabaseAdmin } = require('../config/supabase');
const { AppError, NotFoundError } = require('../utils/errors');

function assertSupabase() {
  if (!supabaseAdmin) throw new AppError('SUPABASE_NOT_CONFIGURED', 'Supabase 환경 변수가 설정되지 않았습니다.', 500);
}

async function registerDeviceToken(userId, token, platform) {
  assertSupabase();
  const { data, error } = await supabaseAdmin
    .from('device_tokens')
    .upsert({ user_id: userId, token, platform }, { onConflict: 'token' })
    .select('*')
    .single();
  if (error) throw new AppError('DEVICE_REGISTER_FAILED', '디바이스 토큰 등록에 실패했습니다.', 400);
  return data;
}

async function removeDeviceToken(userId, tokenId) {
  assertSupabase();
  const { data, error } = await supabaseAdmin
    .from('device_tokens')
    .delete()
    .eq('id', tokenId)
    .eq('user_id', userId)
    .select('id')
    .maybeSingle();
  if (error) throw new AppError('DEVICE_REMOVE_FAILED', '디바이스 토큰 삭제에 실패했습니다.', 400);
  if (!data) throw new NotFoundError('삭제할 디바이스 토큰을 찾을 수 없습니다.');
}

module.exports = {
  registerDeviceToken,
  removeDeviceToken,
};
