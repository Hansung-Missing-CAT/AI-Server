const { supabaseAdmin } = require('../config/supabase');
const { AppError } = require('../utils/errors');

function extractBearerToken(req) {
  const header = req.headers.authorization;
  if (!header) return null;

  const [scheme, token] = header.split(' ');
  if (scheme !== 'Bearer' || !token) return null;
  return token;
}

async function resolveUser(req, required) {
  const token = extractBearerToken(req);

  if (!token) {
    if (required) throw new AppError('INVALID_TOKEN', '인증 토큰이 필요합니다.', 401);
    return null;
  }

  if (!supabaseAdmin) {
    throw new AppError('SUPABASE_NOT_CONFIGURED', 'Supabase 환경 변수가 설정되지 않았습니다.', 500);
  }

  const { data, error } = await supabaseAdmin.auth.getUser(token);
  if (error || !data?.user) {
    throw new AppError('INVALID_TOKEN', '유효하지 않은 인증 토큰입니다.', 401);
  }

  return data.user;
}

async function authenticate(req, res, next) {
  try {
    req.user = await resolveUser(req, true);
    next();
  } catch (err) {
    next(err);
  }
}

async function optionalAuth(req, res, next) {
  try {
    req.user = await resolveUser(req, false);
    next();
  } catch (err) {
    next(err);
  }
}

module.exports = { authenticate, optionalAuth };
