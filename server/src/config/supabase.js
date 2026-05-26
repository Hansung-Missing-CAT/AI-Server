const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = process.env.SUPABASE_URL;
const anonKey = process.env.SUPABASE_ANON_KEY;
const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

function assertSupabaseEnv() {
  if (!supabaseUrl || !anonKey || !serviceRoleKey) {
    throw new Error('SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY must be set');
  }
}

function createServerClient(key, options = {}) {
  if (!supabaseUrl || !key) return null;

  return createClient(supabaseUrl, key, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
    },
    ...options,
  });
}

const supabaseAdmin = createServerClient(serviceRoleKey);
const supabaseAnon = createServerClient(anonKey);

function createUserClient(accessToken) {
  if (!accessToken) throw new Error('accessToken is required');
  assertSupabaseEnv();

  return createClient(supabaseUrl, anonKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
    },
    global: {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
  });
}

module.exports = {
  supabaseAdmin,
  supabaseAnon,
  createUserClient,
  assertSupabaseEnv,
};
