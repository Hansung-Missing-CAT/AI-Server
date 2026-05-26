const { supabaseAdmin } = require('../config/supabase');
const { AppError } = require('../utils/errors');
const { decodeCursor, pageResult } = require('../utils/pagination');

function assertSupabase() {
  if (!supabaseAdmin) throw new AppError('SUPABASE_NOT_CONFIGURED', 'Supabase 환경 변수가 설정되지 않았습니다.', 500);
}

async function getNotifications(userId, { unreadOnly = false, cursor, limit = 20 }) {
  assertSupabase();
  const cursorValue = decodeCursor(cursor);
  let query = supabaseAdmin
    .from('notifications')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(limit + 1);
  if (unreadOnly) query = query.eq('read', false);
  if (cursorValue) query = query.lt('created_at', cursorValue);

  const { data, error } = await query;
  if (error) throw new AppError('NOTIFICATION_LIST_FAILED', '알림 조회에 실패했습니다.', 400);
  return pageResult(data || [], limit, 'created_at');
}

async function getUnreadCount(userId) {
  assertSupabase();
  const { count, error } = await supabaseAdmin
    .from('notifications')
    .select('*', { count: 'exact', head: true })
    .eq('user_id', userId)
    .eq('read', false);
  if (error) throw new AppError('NOTIFICATION_COUNT_FAILED', '미읽음 알림 수 조회에 실패했습니다.', 400);
  return count || 0;
}

async function markAsRead(userId, id) {
  assertSupabase();
  const { error } = await supabaseAdmin
    .from('notifications')
    .update({ read: true })
    .eq('id', id)
    .eq('user_id', userId);
  if (error) throw new AppError('NOTIFICATION_READ_FAILED', '알림 읽음 처리에 실패했습니다.', 400);
}

async function markAllAsRead(userId) {
  assertSupabase();
  const { error } = await supabaseAdmin.from('notifications').update({ read: true }).eq('user_id', userId).eq('read', false);
  if (error) throw new AppError('NOTIFICATION_READ_ALL_FAILED', '전체 읽음 처리에 실패했습니다.', 400);
}

async function createNotification(userId, type, message, petId = null) {
  assertSupabase();
  const { data, error } = await supabaseAdmin
    .from('notifications')
    .insert({ user_id: userId, type, message, pet_id: petId })
    .select('*')
    .single();
  if (error) throw new AppError('NOTIFICATION_CREATE_FAILED', '알림 생성에 실패했습니다.', 400);
  return data;
}

module.exports = {
  getNotifications,
  getUnreadCount,
  markAsRead,
  markAllAsRead,
  createNotification,
};
