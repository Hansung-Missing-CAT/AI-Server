const request = require('supertest');

jest.mock('../src/config/supabase', () => ({
  supabaseAdmin: {
    auth: { getUser: async () => ({ data: { user: { id: 'u1' } }, error: null }) },
  },
  supabaseAnon: { auth: {} },
  createUserClient: () => ({ auth: {} }),
}));

const app = require('../src/app');

describe('chats smoke', () => {
  test('POST /api/chats/:chatId/messages requires auth', async () => {
    const res = await request(app).post('/api/chats/00000000-0000-0000-0000-000000000001/messages').send({ type: 'text', message: 'hi' });
    expect(res.status).toBe(401);
  });

  test('POST /api/chats/:chatId/read requires auth', async () => {
    const res = await request(app).post('/api/chats/00000000-0000-0000-0000-000000000001/read');
    expect(res.status).toBe(401);
  });
});
