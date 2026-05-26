const { supabaseAdmin } = require('../config/supabase');

const userSockets = new Map();

function getBearer(token) {
  if (!token) return null;
  if (token.startsWith('Bearer ')) return token.slice(7);
  return token;
}

async function authenticateSocket(socket, next) {
  try {
    const token = getBearer(socket.handshake.auth?.token);
    if (!token || !supabaseAdmin) return next(new Error('unauthorized'));
    const { data, error } = await supabaseAdmin.auth.getUser(token);
    if (error || !data?.user) return next(new Error('unauthorized'));
    socket.userId = data.user.id;
    return next();
  } catch {
    return next(new Error('unauthorized'));
  }
}

function registerSocketHandlers(io) {
  io.use(authenticateSocket);

  io.on('connection', (socket) => {
    const userId = socket.userId;
    if (!userSockets.has(userId)) userSockets.set(userId, new Set());
    userSockets.get(userId).add(socket.id);

    socket.emit('socket.ready', { socketId: socket.id, userId });
    io.emit('presence.update', { userId, isOnline: true });

    socket.on('disconnect', () => {
      const set = userSockets.get(userId);
      if (set) {
        set.delete(socket.id);
        if (set.size === 0) {
          userSockets.delete(userId);
          io.emit('presence.update', { userId, isOnline: false });
        }
      }
    });
  });
}

function emitToUser(io, userId, event, payload) {
  const socketIds = userSockets.get(userId);
  if (!socketIds) return;
  for (const sid of socketIds) io.to(sid).emit(event, payload);
}

module.exports = { registerSocketHandlers, emitToUser };
