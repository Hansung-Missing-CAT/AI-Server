const request = require('supertest');

jest.mock('../src/config/supabase', () => {
  const signInWithPassword = jest.fn(async ({ email, password }) => {
    if (email === 'ok@example.com' && password === 'password123') {
      return {
        data: {
          session: { access_token: 'at', refresh_token: 'rt' },
          user: { id: 'u1', email: 'ok@example.com', user_metadata: { name: 'tester' } },
        },
        error: null,
      };
    }
    return { data: null, error: { message: 'Invalid login credentials' } };
  });

  return {
    supabaseAdmin: {
      from: () => ({
        select: () => ({
          eq: () => ({
            maybeSingle: async () => ({ data: { name: 'tester' }, error: null }),
          }),
        }),
      }),
      auth: { getUser: async () => ({ data: { user: { id: 'u1' } }, error: null }) },
    },
    supabaseAnon: {
      auth: { signInWithPassword },
    },
    createUserClient: () => ({ auth: { signOut: async () => ({ error: null }) } }),
  };
});

const app = require('../src/app');

describe('auth smoke', () => {
  test('POST /api/auth/login success', async () => {
    const res = await request(app).post('/api/auth/login').send({ email: 'ok@example.com', password: 'password123' });
    expect(res.status).toBe(200);
    expect(res.body.accessToken).toBeDefined();
  });

  test('POST /api/auth/login invalid password', async () => {
    const res = await request(app).post('/api/auth/login').send({ email: 'ok@example.com', password: 'bad' });
    expect(res.status).toBe(401);
    expect(res.body.code).toBe('INVALID_CREDENTIALS');
  });
});
