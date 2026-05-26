const { supabaseAdmin } = require('../config/supabase');
const { AppError, ForbiddenError, NotFoundError } = require('../utils/errors');
const { decodeCursor, pageResult } = require('../utils/pagination');
const { incrementView } = require('./views.service');

function assertSupabase() {
  if (!supabaseAdmin) {
    throw new AppError('SUPABASE_NOT_CONFIGURED', 'Supabase 환경 변수가 설정되지 않았습니다.', 500);
  }
}

function applyTextSearch(query, q) {
  if (!q) return query;
  return query.or(`name.ilike.%${q}%,breed.ilike.%${q}%,location.ilike.%${q}%`);
}

async function listPets({ district, q, sort = 'latest', status, cursor, limit = 20 }) {
  assertSupabase();
  const cursorValue = decodeCursor(cursor);
  let query = supabaseAdmin
    .from('missing_pets')
    .select('*')
    .order(sort === 'likes' ? 'likes_count' : sort === 'comments' ? 'comments_count' : 'created_at', {
      ascending: false,
    })
    .order('id', { ascending: false })
    .limit(limit + 1);

  if (district && district !== '전체') query = query.eq('district', district);
  if (status && ['실종', '찾음'].includes(status)) query = query.eq('status', status);
  query = applyTextSearch(query, q);
  if (cursorValue && sort === 'latest') query = query.lt('created_at', cursorValue);

  const { data, error } = await query;
  if (error) throw new AppError('PET_LIST_FAILED', '게시글 목록 조회에 실패했습니다.', 400);

  return pageResult(data || [], limit, 'created_at');
}

async function getPetById(id) {
  assertSupabase();
  const { data, error } = await supabaseAdmin.from('missing_pets').select('*').eq('id', id).maybeSingle();
  if (error) throw new AppError('PET_FETCH_FAILED', '게시글 조회에 실패했습니다.', 400);
  if (!data) throw new NotFoundError('게시글을 찾을 수 없습니다.');
  return data;
}

async function createPet(input, userId) {
  assertSupabase();
  const payload = {
    name: input.name,
    breed: input.breed,
    age: input.age ?? null,
    gender: input.gender ?? null,
    color: input.color ?? null,
    location: input.location ?? null,
    district: input.district ?? null,
    detail_address: input.detailAddress ?? null,
    last_seen: input.lostDate,
    lost_time: input.lostTime ?? null,
    reward: input.reward ?? null,
    photo: input.photoUrls?.[0] ?? null,
    photos: input.photoUrls ?? [],
    description: input.description ?? null,
    status: input.status ?? '실종',
    reporter_id: userId,
    latitude: input.latitude ?? null,
    longitude: input.longitude ?? null,
    embedding_status: 'pending',
  };

  const { data, error } = await supabaseAdmin.from('missing_pets').insert(payload).select('*').single();
  if (error) throw new AppError('PET_CREATE_FAILED', '게시글 생성에 실패했습니다.', 400);
  return data;
}

async function updatePet(id, input, userId) {
  assertSupabase();
  const pet = await getPetById(id);
  if (pet.reporter_id !== userId) throw new ForbiddenError('게시글 작성자만 수정할 수 있습니다.');

  const patch = {};
  const map = {
    name: 'name',
    breed: 'breed',
    age: 'age',
    gender: 'gender',
    color: 'color',
    location: 'location',
    district: 'district',
    detailAddress: 'detail_address',
    lostDate: 'last_seen',
    lostTime: 'lost_time',
    reward: 'reward',
    description: 'description',
    status: 'status',
    latitude: 'latitude',
    longitude: 'longitude',
  };
  Object.entries(map).forEach(([from, to]) => {
    if (input[from] !== undefined) patch[to] = input[from];
  });
  if (Array.isArray(input.photoUrls)) {
    patch.photos = input.photoUrls;
    patch.photo = input.photoUrls[0] || null;
  }

  const { data, error } = await supabaseAdmin.from('missing_pets').update(patch).eq('id', id).select('*').single();
  if (error) throw new AppError('PET_UPDATE_FAILED', '게시글 수정에 실패했습니다.', 400);
  return data;
}

async function deletePet(id, userId) {
  assertSupabase();
  const pet = await getPetById(id);
  if (pet.reporter_id !== userId) throw new ForbiddenError('게시글 작성자만 삭제할 수 있습니다.');
  const { error } = await supabaseAdmin.from('missing_pets').delete().eq('id', id);
  if (error) throw new AppError('PET_DELETE_FAILED', '게시글 삭제에 실패했습니다.', 400);
}

async function incrementViews(petId) {
  await incrementView(petId);
}

async function isPetLikedByUser(petId, userId) {
  assertSupabase();
  const { data, error } = await supabaseAdmin
    .from('pet_likes')
    .select('id')
    .eq('pet_id', petId)
    .eq('user_id', userId)
    .limit(1)
    .maybeSingle();
  if (error) return false;
  return !!data;
}

async function likePet(petId, userId) {
  assertSupabase();
  const { error } = await supabaseAdmin.from('pet_likes').insert({ pet_id: petId, user_id: userId });
  if (error) {
    if (error.code === '23505') throw new AppError('ALREADY_LIKED', '이미 좋아요한 게시글입니다.', 409);
    throw new AppError('LIKE_FAILED', '좋아요 처리에 실패했습니다.', 400);
  }
}

async function unlikePet(petId, userId) {
  assertSupabase();
  const { error } = await supabaseAdmin.from('pet_likes').delete().eq('pet_id', petId).eq('user_id', userId);
  if (error) throw new AppError('UNLIKE_FAILED', '좋아요 취소에 실패했습니다.', 400);
}

async function listComments(petId, { cursor, limit = 20 }) {
  assertSupabase();
  const cursorValue = decodeCursor(cursor);
  let query = supabaseAdmin
    .from('pet_comments')
    .select('*')
    .eq('pet_id', petId)
    .order('created_at', { ascending: false })
    .limit(limit + 1);

  if (cursorValue) query = query.lt('created_at', cursorValue);
  const { data, error } = await query;
  if (error) throw new AppError('COMMENT_LIST_FAILED', '댓글 조회에 실패했습니다.', 400);
  return pageResult(data || [], limit, 'created_at');
}

async function createComment(petId, userId, content) {
  assertSupabase();
  const { data, error } = await supabaseAdmin
    .from('pet_comments')
    .insert({ pet_id: petId, user_id: userId, content })
    .select('*')
    .single();
  if (error) throw new AppError('COMMENT_CREATE_FAILED', '댓글 작성에 실패했습니다.', 400);
  return data;
}

async function deleteComment(commentId, userId) {
  assertSupabase();
  const { data: comment, error: fetchError } = await supabaseAdmin
    .from('pet_comments')
    .select('*')
    .eq('id', commentId)
    .maybeSingle();
  if (fetchError) throw new AppError('COMMENT_FETCH_FAILED', '댓글 조회에 실패했습니다.', 400);
  if (!comment) throw new NotFoundError('댓글을 찾을 수 없습니다.');
  if (comment.user_id !== userId) throw new ForbiddenError('댓글 작성자만 삭제할 수 있습니다.');

  const { error } = await supabaseAdmin.from('pet_comments').delete().eq('id', commentId);
  if (error) throw new AppError('COMMENT_DELETE_FAILED', '댓글 삭제에 실패했습니다.', 400);
}

module.exports = {
  listPets,
  getPetById,
  createPet,
  updatePet,
  deletePet,
  incrementViews,
  isPetLikedByUser,
  likePet,
  unlikePet,
  listComments,
  createComment,
  deleteComment,
};
