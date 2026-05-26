const { supabaseAdmin, supabaseAnon, createUserClient } = require('../config/supabase');
const { AppError } = require('../utils/errors');
const { success } = require('../utils/response');

function ensureSupabase(client) {
  if (!client) {
    throw new AppError('SUPABASE_NOT_CONFIGURED', 'Supabase 환경 변수가 설정되지 않았습니다.', 500);
  }
}

async function signup(req, res, next) {
  try {
    ensureSupabase(supabaseAdmin);
    const { email, password, name, phone, agreeTerms, agreePrivacy, agreeMarketing = false } = req.body;

    if (!agreeTerms || !agreePrivacy) {
      throw new AppError('TERMS_REQUIRED', '필수 약관 동의가 필요합니다.', 400);
    }

    const { data: userData, error: createError } = await supabaseAdmin.auth.admin.createUser({
      email,
      password,
      email_confirm: true,
      user_metadata: { name, phone, agreeTerms, agreePrivacy, agreeMarketing },
    });

    if (createError) {
      const msg = createError.message || '';
      if (msg.includes('already') || msg.includes('exists')) {
        throw new AppError('EMAIL_ALREADY_EXISTS', '이미 사용 중인 이메일입니다.', 409);
      }
      throw new AppError('SIGNUP_FAILED', '회원가입에 실패했습니다.', 400);
    }

    const user = userData?.user;
    if (!user?.id) {
      throw new AppError('SIGNUP_FAILED', '회원가입 처리 중 오류가 발생했습니다.', 500);
    }

    const { data: profile, error: profileError } = await supabaseAdmin
      .from('users')
      .upsert(
        {
          id: user.id,
          name,
          phone: phone || null,
          agree_marketing: !!agreeMarketing,
        },
        { onConflict: 'id' },
      )
      .select('id, name, phone, avatar_url, agree_marketing, created_at')
      .single();

    if (profileError) {
      throw new AppError('PROFILE_CREATE_FAILED', '프로필 생성에 실패했습니다.', 500);
    }

    return success(
      res,
      {
        user: {
          id: user.id,
          email: user.email,
          ...profile,
        },
      },
      201,
    );
  } catch (err) {
    next(err);
  }
}

async function login(req, res, next) {
  try {
    ensureSupabase(supabaseAnon);
    const { email, password } = req.body;
    const { data, error } = await supabaseAnon.auth.signInWithPassword({ email, password });

    if (error || !data?.session || !data?.user) {
      throw new AppError('INVALID_CREDENTIALS', '이메일 또는 비밀번호가 올바르지 않습니다.', 401);
    }

    const { data: profile } = await supabaseAdmin
      .from('users')
      .select('id, name, phone, avatar_url')
      .eq('id', data.user.id)
      .maybeSingle();

    return success(res, {
      accessToken: data.session.access_token,
      refreshToken: data.session.refresh_token,
      user: {
        id: data.user.id,
        email: data.user.email,
        name: profile?.name || data.user.user_metadata?.name || null,
        phone: profile?.phone || null,
        avatar_url: profile?.avatar_url || null,
      },
    });
  } catch (err) {
    next(err);
  }
}

async function refresh(req, res, next) {
  try {
    ensureSupabase(supabaseAnon);
    const { refreshToken } = req.body;
    const { data, error } = await supabaseAnon.auth.refreshSession({ refresh_token: refreshToken });

    if (error || !data?.session) {
      throw new AppError('INVALID_REFRESH_TOKEN', '리프레시 토큰이 유효하지 않습니다.', 401);
    }

    return success(res, {
      accessToken: data.session.access_token,
      refreshToken: data.session.refresh_token,
    });
  } catch (err) {
    next(err);
  }
}

async function logout(req, res, next) {
  try {
    const token = req.headers.authorization?.split(' ')?.[1];
    if (!token) throw new AppError('INVALID_TOKEN', '인증 토큰이 필요합니다.', 401);

    const client = createUserClient(token);
    await client.auth.signOut();
    return success(res, { success: true });
  } catch (err) {
    next(err);
  }
}

async function forgotPassword(req, res, next) {
  try {
    ensureSupabase(supabaseAnon);
    const { email } = req.body;
    const redirectTo = req.body.redirectTo || undefined;
    const { error } = await supabaseAnon.auth.resetPasswordForEmail(email, { redirectTo });
    if (error) throw new AppError('PASSWORD_RESET_FAILED', '비밀번호 재설정 메일 발송에 실패했습니다.', 400);
    return success(res, { success: true });
  } catch (err) {
    next(err);
  }
}

async function resetPassword(req, res, next) {
  try {
    const token = req.headers.authorization?.split(' ')?.[1];
    if (!token) throw new AppError('INVALID_TOKEN', '인증 토큰이 필요합니다.', 401);
    const { password } = req.body;
    const client = createUserClient(token);
    const { error } = await client.auth.updateUser({ password });
    if (error) throw new AppError('PASSWORD_RESET_FAILED', '비밀번호 변경에 실패했습니다.', 400);
    return success(res, { success: true });
  } catch (err) {
    next(err);
  }
}

async function loginWithGoogle(req, res, next) {
  try {
    ensureSupabase(supabaseAnon);
    const { idToken } = req.body;
    const { data, error } = await supabaseAnon.auth.signInWithIdToken({
      provider: 'google',
      token: idToken,
    });
    if (error || !data?.session || !data?.user) {
      throw new AppError('GOOGLE_LOGIN_FAILED', 'Google 로그인에 실패했습니다.', 401);
    }

    return success(res, {
      accessToken: data.session.access_token,
      refreshToken: data.session.refresh_token,
      user: {
        id: data.user.id,
        email: data.user.email,
        name: data.user.user_metadata?.name || null,
      },
    });
  } catch (err) {
    next(err);
  }
}

module.exports = {
  signup,
  login,
  loginWithGoogle,
  refresh,
  logout,
  forgotPassword,
  resetPassword,
};
