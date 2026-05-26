const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');

const { notFoundHandler, errorHandler } = require('./middlewares/error.middleware');
const { success } = require('./utils/response');
const { mountSwagger } = require('./config/swagger');

const app = express();

app.use(helmet());
app.use(cors({ origin: process.env.CORS_ORIGIN || '*' }));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

if (process.env.NODE_ENV !== 'test') {
  app.use(morgan('dev'));
}

app.get('/health', (req, res) => {
  success(res, {
    status: 'ok',
    timestamp: new Date().toISOString(),
  });
});

mountSwagger(app);

app.use('/api/auth', require('./routes/auth.routes'));
app.use('/api/users', require('./routes/users.routes'));
app.use('/api/pets', require('./routes/pets.routes'));
app.use('/api/tips', require('./routes/tips.routes'));
app.use('/api/chats', require('./routes/chats.routes'));
app.use('/api/notifications', require('./routes/notifications.routes'));
app.use('/api/uploads', require('./routes/uploads.routes'));
app.use('/api/comments', require('./routes/comments.routes'));
app.use('/api/devices', require('./routes/devices.routes'));

app.use(notFoundHandler);
app.use(errorHandler);

module.exports = app;
