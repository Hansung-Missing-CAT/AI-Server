const { supabaseAdmin } = require('../config/supabase');
const { AppError, NotFoundError } = require('../utils/errors');
const { enqueueAiAnalysis } = require('../queues/producers/ai.producer');
const chatService = require('./chat.service');
const notificationService = require('./notification.service');

function assertSupabase() {
  if (!supabaseAdmin) throw new AppError('SUPABASE_NOT_CONFIGURED', 'Supabase 환경 변수가 설정되지 않았습니다.', 500);
}

async function createAnalysisRequest(userId, imageUrls = []) {
  assertSupabase();
  const { data, error } = await supabaseAdmin
    .from('tips')
    .insert({ user_id: userId, status: 'processing', image_urls: imageUrls, progress: 0 })
    .select('*')
    .single();
  if (error) throw new AppError('TIP_CREATE_FAILED', '제보 분석 요청 생성에 실패했습니다.', 400);

  enqueueAiAnalysis({ tipId: data.id, userId, imageUrls }).catch(async () => {
    await supabaseAdmin.from('tips').update({ status: 'failed', error_msg: '큐 발행 실패' }).eq('id', data.id);
  });
  return data;
}

async function getTip(tipId, userId) {
  assertSupabase();
  const { data, error } = await supabaseAdmin.from('tips').select('*').eq('id', tipId).eq('user_id', userId).maybeSingle();
  if (error) throw new AppError('TIP_FETCH_FAILED', '제보 조회에 실패했습니다.', 400);
  if (!data) throw new NotFoundError('제보를 찾을 수 없습니다.');
  return data;
}

async function sendTip(tipId, petId, userId) {
  assertSupabase();
  const tip = await getTip(tipId, userId);
  if (tip.status !== 'done') {
    throw new AppError('TIP_NOT_READY', '분석 완료 후 제보를 보낼 수 있습니다.', 409);
  }

  const { data: pet, error: petError } = await supabaseAdmin
    .from('missing_pets')
    .select('id, reporter_id, name')
    .eq('id', petId)
    .maybeSingle();
  if (petError) throw new AppError('PET_FETCH_FAILED', '게시글 조회에 실패했습니다.', 400);
  if (!pet) throw new NotFoundError('게시글을 찾을 수 없습니다.');

  const chat = await chatService.createOrGetChat(pet.id, userId, pet.reporter_id);
  await chatService.sendMessage(chat.id, userId, {
    type: 'tipCard',
    message: `${pet.name || '반려동물'} 관련 제보를 보냈습니다.`,
    payload: { tipId: tip.id, petId: pet.id, results: tip.results, imageUrls: tip.image_urls },
  });

  await notificationService.createNotification(
    pet.reporter_id,
    'tip',
    `${pet.name || '게시글'}에 새 제보가 도착했습니다.`,
    pet.id,
  );

  return { chatId: chat.id };
}

module.exports = {
  createAnalysisRequest,
  getTip,
  sendTip,
};
