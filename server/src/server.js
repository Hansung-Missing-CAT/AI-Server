require('dotenv').config();

const http = require('http');
const { Server } = require('socket.io');

const app = require('./app');
const { registerSocketHandlers } = require('./socket/socket.handler');
const { registerRealtimeHandlers } = require('./socket/realtime.handler');
const { startPushWorker } = require('./queues/workers/push.worker');
const { startViewFlushJob } = require('./services/views.service');

const port = Number(process.env.PORT || 3000);
const server = http.createServer(app);

const io = new Server(server, {
  cors: {
    origin: process.env.CORS_ORIGIN || '*',
    methods: ['GET', 'POST', 'PATCH', 'DELETE'],
  },
  path: '/ws',
});

app.set('io', io);
registerSocketHandlers(io);
registerRealtimeHandlers(io).catch((err) => {
  console.error('Failed to register realtime handlers:', err.message);
});
startPushWorker();
startViewFlushJob(Number(process.env.VIEW_FLUSH_INTERVAL_MS || 60000));

server.listen(port, () => {
  console.log(`Express server listening on http://localhost:${port}`);
});

module.exports = { server, io };
