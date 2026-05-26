const request = require('supertest');

jest.mock('../src/config/supabase', () => ({
  supabaseAdmin: {
    auth: { getUser: async () => ({ data: { user: { id: 'u1' } }, error: null }) },
  },
  supabaseAnon: { auth: {} },
  createUserClient: () => ({ auth: {} }),
}));

const app = require('../src/app');

describe('pets smoke', () => {
  test('POST /api/pets requires auth', async () => {
    const res = await request(app).post('/api/pets').send({ name: 'a', breed: 'b', photoUrls: ['1', '2', '3', '4', '5'] });
    expect(res.status).toBe(401);
  });

  test('PATCH /api/pets/:id requires auth', async () => {
    const res = await request(app).patch('/api/pets/00000000-0000-0000-0000-000000000001').send({ name: 'x' });
    expect(res.status).toBe(401);
  });

  test('DELETE /api/pets/:id requires auth', async () => {
    const res = await request(app).delete('/api/pets/00000000-0000-0000-0000-000000000001');
    expect(res.status).toBe(401);
  });
});
