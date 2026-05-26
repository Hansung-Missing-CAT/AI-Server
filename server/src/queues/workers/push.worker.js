'use strict';

const { Worker } = require('bullmq');
const { connection } = require('../../config/bullmq');
const { supabaseAdmin } = require('../../config/supabase');

const FCM_SERVER_KEY = process.env.FCM_SERVER_KEY;
const FCM_PROJECT_ID = process.env.FCM_PROJECT_ID;
const FCM_V1_ACCESS_TOKEN = process.env.FCM_V1_ACCESS_TOKEN;

async function sendFcmV1(token, title, body, data = {}) {
  if (!FCM_PROJECT_ID || !FCM_V1_ACCESS_TOKEN) {
    return { ok: false, skipped: true, reason: 'FCM_V1_NOT_CONFIGURED' };
  }

  const resp = await fetch(`https://fcm.googleapis.com/v1/projects/${FCM_PROJECT_ID}/messages:send`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${FCM_V1_ACCESS_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: {
        token,
        notification: { title, body },
        data: Object.fromEntries(Object.entries(data || {}).map(([k, v]) => [k, String(v)])),
      },
    }),
  });
  const payload = await resp.json().catch(() => ({}));
  return { ok: resp.ok, payload };
}

async function sendFcmLegacy(token, title, body, data = {}) {
  if (!FCM_SERVER_KEY) {
    return { ok: false, skipped: true, reason: 'FCM_LEGACY_NOT_CONFIGURED' };
  }
  const resp = await fetch('https://fcm.googleapis.com/fcm/send', {
    method: 'POST',
    headers: {
      Authorization: `key=${FCM_SERVER_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ to: token, notification: { title, body }, data, priority: 'high' }),
  });
  const payload = await resp.json().catch(() => ({}));
  return { ok: resp.ok, payload };
}

async function sendFcm(token, title, body, data = {}) {
  const v1 = await sendFcmV1(token, title, body, data);
  if (v1.ok) return v1;
  if (!v1.skipped) return v1;
  return sendFcmLegacy(token, title, body, data);
}

async function removeInvalidToken(token) {
  if (!supabaseAdmin) return;
  await supabaseAdmin.from('device_tokens').delete().eq('token', token);
}

function startPushWorker() {
  if (!connection) return null;
  return new Worker(
    'push-notifications',
    async (job) => {
      if (!supabaseAdmin) return { skipped: true, reason: 'SUPABASE_NOT_CONFIGURED' };
      const { userId, title, body, data } = job.data || {};
      if (!userId || !title || !body) return { skipped: true, reason: 'INVALID_PAYLOAD' };

      const { data: rows, error } = await supabaseAdmin.from('device_tokens').select('token').eq('user_id', userId);
      if (error) throw error;
      const tokens = (rows || []).map((x) => x.token).filter(Boolean);

      let sent = 0;
      for (const token of tokens) {
        const result = await sendFcm(token, title, body, data);
        const legacyResults = result.payload?.results || [];
        const firstLegacy = legacyResults[0] || {};
        const v1Error = result.payload?.error?.status;
        if (
          firstLegacy.error === 'InvalidRegistration' ||
          firstLegacy.error === 'NotRegistered' ||
          v1Error === 'UNREGISTERED' ||
          v1Error === 'INVALID_ARGUMENT'
        ) {
          await removeInvalidToken(token);
          continue;
        }
        if (result.ok) sent += 1;
      }
      return { sent, total: tokens.length };
    },
    { connection },
  );
}

module.exports = { startPushWorker };
