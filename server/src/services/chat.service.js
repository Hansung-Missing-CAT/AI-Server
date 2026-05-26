const { supabaseAdmin } = require('../config/supabase');
const { AppError, ForbiddenError, NotFoundError } = require('../utils/errors');
const { decodeCursor, pageResult } = require('../utils/pagination');

function assertSupabase() {
  if (!supabaseAdmin) throw new AppError('SUPABASE_NOT_CONFIGURED', 'Supabase 환경 변수가 설정되지 않았습니다.', 500);
}

async function ensureParticipant(chatId, userId) {
  const chat = await getChatById(chatId, userId);
  return chat;
}

async function getChatList(userId, { q, cursor, limit = 20 }) {
  assertSupabase();
  const cursorValue = decodeCursor(cursor);
  let query = supabaseAdmin
    .from('chats')
    .select('*')
    .contains('participant_ids', [userId])
    .order('last_message_at', { ascending: false, nullsFirst: false })
    .order('created_at', { ascending: false })
    .limit(limit + 1);
  if (q) query = query.ilike('last_message', `%${q}%`);
  if (cursorValue) query = query.lt('last_message_at', cursorValue);
  const { data: rawRows, error } = await query;
  if (error) throw new AppError('CHAT_LIST_FAILED', '채팅 목록 조회에 실패했습니다.', 400);
  const paged = pageResult(rawRows || [], limit, 'last_message_at');
  const rows = paged.data || [];
  if (!rows.length) return paged;

  const otherUserIds = [];
  const petIds = [];
  for (const chat of rows) {
    const participants = chat.participant_ids || [];
    const otherUserId = participants.find((id) => id !== userId);
    if (otherUserId) otherUserIds.push(otherUserId);
    if (chat.pet_id) petIds.push(chat.pet_id);
  }

  const [{ data: userRows }, { data: petRows }, { data: messageRows }] = await Promise.all([
    otherUserIds.length
      ? supabaseAdmin.from('users').select('id,name,avatar_url,is_online').in('id', otherUserIds)
      : Promise.resolve({ data: [] }),
    petIds.length ? supabaseAdmin.from('missing_pets').select('id,name').in('id', petIds) : Promise.resolve({ data: [] }),
    supabaseAdmin.from('chat_messages').select('chat_id,read_by').in(
      'chat_id',
      rows.map((r) => r.id),
    ),
  ]);

  const userMap = new Map((userRows || []).map((u) => [u.id, u]));
  const petMap = new Map((petRows || []).map((p) => [p.id, p]));

  const unreadByChat = new Map();
  for (const msg of messageRows || []) {
    const readBy = Array.isArray(msg.read_by) ? msg.read_by : [];
    if (!readBy.includes(userId)) {
      unreadByChat.set(msg.chat_id, (unreadByChat.get(msg.chat_id) || 0) + 1);
    }
  }

  paged.data = rows
    .map((chat) => {
      const otherUserId = (chat.participant_ids || []).find((id) => id !== userId);
      const other = otherUserId ? userMap.get(otherUserId) : null;
      const pet = chat.pet_id ? petMap.get(chat.pet_id) : null;
      return {
        ...chat,
        petName: pet?.name || null,
        otherUserName: other?.name || null,
        otherUserAvatar: other?.avatar_url || null,
        isOnline: other?.is_online || false,
        unreadCount: unreadByChat.get(chat.id) || 0,
      };
    })
    .filter((chat) => {
      if (!q) return true;
      return [chat.petName, chat.otherUserName, chat.last_message].some((v) =>
        typeof v === 'string' ? v.toLowerCase().includes(q.toLowerCase()) : false,
      );
    });

  return paged;
}

async function getChatById(chatId, userId) {
  assertSupabase();
  const { data, error } = await supabaseAdmin.from('chats').select('*').eq('id', chatId).maybeSingle();
  if (error) throw new AppError('CHAT_FETCH_FAILED', '채팅방 조회에 실패했습니다.', 400);
  if (!data) throw new NotFoundError('채팅방을 찾을 수 없습니다.');
  if (!Array.isArray(data.participant_ids) || !data.participant_ids.includes(userId)) {
    throw new ForbiddenError('채팅 참여자만 접근할 수 있습니다.');
  }
  return data;
}

async function getChatMessages(chatId, userId, { cursor, limit = 20 }) {
  assertSupabase();
  await ensureParticipant(chatId, userId);
  const cursorValue = decodeCursor(cursor);
  let query = supabaseAdmin
    .from('chat_messages')
    .select('*')
    .eq('chat_id', chatId)
    .order('created_at', { ascending: false })
    .limit(limit + 1);
  if (cursorValue) query = query.lt('created_at', cursorValue);
  const { data, error } = await query;
  if (error) throw new AppError('CHAT_MESSAGES_FAILED', '메시지 조회에 실패했습니다.', 400);
  return pageResult(data || [], limit, 'created_at');
}

async function createOrGetChat(petId, userId, otherUserId) {
  assertSupabase();
  const { data: existing, error: findError } = await supabaseAdmin
    .from('chats')
    .select('*')
    .eq('pet_id', petId)
    .contains('participant_ids', [userId, otherUserId])
    .limit(1)
    .maybeSingle();
  if (findError) throw new AppError('CHAT_FIND_FAILED', '채팅방 조회에 실패했습니다.', 400);
  if (existing) return existing;

  const { data, error } = await supabaseAdmin
    .from('chats')
    .insert({ pet_id: petId, participant_ids: [userId, otherUserId] })
    .select('*')
    .single();
  if (error) throw new AppError('CHAT_CREATE_FAILED', '채팅방 생성에 실패했습니다.', 400);
  return data;
}

async function sendMessage(chatId, senderId, payload) {
  assertSupabase();
  await ensureParticipant(chatId, senderId);

  const messagePayload = {
    chat_id: chatId,
    sender_id: senderId,
    type: payload.type || 'text',
    message: payload.message || null,
    image_url: payload.imageUrl || null,
    latitude: payload.latitude || null,
    longitude: payload.longitude || null,
    payload: payload.payload || null,
    read_by: [senderId],
  };

  const { data: msg, error: msgError } = await supabaseAdmin
    .from('chat_messages')
    .insert(messagePayload)
    .select('*')
    .single();
  if (msgError) throw new AppError('MESSAGE_SEND_FAILED', '메시지 전송에 실패했습니다.', 400);

  await supabaseAdmin
    .from('chats')
    .update({ last_message: payload.message || payload.type || 'message', last_message_at: new Date().toISOString() })
    .eq('id', chatId);

  return msg;
}

async function markAsRead(chatId, userId) {
  assertSupabase();
  await ensureParticipant(chatId, userId);
  const { data: messages, error } = await supabaseAdmin
    .from('chat_messages')
    .select('id, read_by')
    .eq('chat_id', chatId);
  if (error) throw new AppError('CHAT_READ_FAILED', '읽음 처리 조회에 실패했습니다.', 400);

  for (const msg of messages || []) {
    const readBy = Array.isArray(msg.read_by) ? msg.read_by : [];
    if (!readBy.includes(userId)) {
      await supabaseAdmin.from('chat_messages').update({ read_by: [...readBy, userId] }).eq('id', msg.id);
    }
  }
}

async function leaveChat(chatId, userId) {
  assertSupabase();
  const chat = await ensureParticipant(chatId, userId);
  const nextParticipants = (chat.participant_ids || []).filter((id) => id !== userId);
  const { error } = await supabaseAdmin.from('chats').update({ participant_ids: nextParticipants }).eq('id', chatId);
  if (error) throw new AppError('CHAT_LEAVE_FAILED', '채팅방 나가기에 실패했습니다.', 400);
}

async function reportChat(chatId, userId, reason) {
  assertSupabase();
  await ensureParticipant(chatId, userId);
  const { data, error } = await supabaseAdmin
    .from('chat_reports')
    .insert({ chat_id: chatId, reporter_id: userId, reason })
    .select('*')
    .single();
  if (error) throw new AppError('CHAT_REPORT_FAILED', '채팅 신고에 실패했습니다.', 400);
  return data;
}

module.exports = {
  getChatList,
  getChatById,
  getChatMessages,
  createOrGetChat,
  sendMessage,
  markAsRead,
  leaveChat,
  reportChat,
};
