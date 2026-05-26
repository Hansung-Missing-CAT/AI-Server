const swaggerJSDoc = require('swagger-jsdoc');
const swaggerUi = require('swagger-ui-express');

const options = {
  definition: {
    openapi: '3.0.3',
    info: {
      title: 'Missing Pet Finder Server API',
      version: '0.1.0',
    },
    servers: [{ url: 'http://localhost:3000' }],
    components: {
      securitySchemes: {
        bearerAuth: {
          type: 'http',
          scheme: 'bearer',
          bearerFormat: 'JWT',
        },
      },
      schemas: {
        ApiError: {
          type: 'object',
          properties: {
            code: { type: 'string' },
            message: { type: 'string' },
          },
        },
      },
    },
    paths: {
      '/health': {
        get: {
          summary: 'Server health check',
          responses: { '200': { description: 'OK' } },
        },
      },
      '/api/auth/signup': {
        post: { summary: 'Sign up', responses: { '201': { description: 'Created' }, '409': { description: 'Conflict' } } },
      },
      '/api/auth/login': {
        post: {
          summary: 'Login',
          requestBody: {
            required: true,
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  required: ['email', 'password'],
                  properties: {
                    email: { type: 'string', format: 'email' },
                    password: { type: 'string' },
                  },
                },
              },
            },
          },
          responses: { '200': { description: 'Logged in' }, '401': { description: 'Unauthorized' } },
        },
      },
      '/api/auth/login/google': {
        post: { summary: 'Google login', responses: { '200': { description: 'Logged in' }, '401': { description: 'Unauthorized' } } },
      },
      '/api/auth/refresh': {
        post: { summary: 'Refresh token', responses: { '200': { description: 'Refreshed' }, '401': { description: 'Unauthorized' } } },
      },
      '/api/auth/logout': {
        post: { summary: 'Logout', security: [{ bearerAuth: [] }], responses: { '200': { description: 'Logged out' } } },
      },
      '/api/auth/password/forgot': {
        post: { summary: 'Request password reset', responses: { '200': { description: 'Requested' } } },
      },
      '/api/auth/password/reset': {
        post: { summary: 'Reset password', security: [{ bearerAuth: [] }], responses: { '200': { description: 'Updated' } } },
      },
      '/api/users/me': {
        get: {
          summary: 'Get my profile',
          security: [{ bearerAuth: [] }],
          responses: { '200': { description: 'Profile' }, '401': { description: 'Unauthorized' } },
        },
        patch: {
          summary: 'Update my profile',
          security: [{ bearerAuth: [] }],
          responses: { '200': { description: 'Updated' }, '401': { description: 'Unauthorized' } },
        },
      },
      '/api/pets': {
        get: { summary: 'List pets', responses: { '200': { description: 'List response' } } },
        post: {
          summary: 'Create pet post',
          security: [{ bearerAuth: [] }],
          responses: { '201': { description: 'Created' }, '401': { description: 'Unauthorized' } },
        },
      },
      '/api/pets/{id}': {
        get: { summary: 'Get pet detail', parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string' } }], responses: { '200': { description: 'Detail' }, '404': { description: 'Not found' } } },
        patch: { summary: 'Update pet', security: [{ bearerAuth: [] }], parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string' } }], responses: { '200': { description: 'Updated' }, '403': { description: 'Forbidden' } } },
        delete: { summary: 'Delete pet', security: [{ bearerAuth: [] }], parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string' } }], responses: { '200': { description: 'Deleted' }, '403': { description: 'Forbidden' } } },
      },
      '/api/pets/{id}/like': {
        post: { summary: 'Like pet', security: [{ bearerAuth: [] }], parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string' } }], responses: { '201': { description: 'Liked' } } },
        delete: { summary: 'Unlike pet', security: [{ bearerAuth: [] }], parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string' } }], responses: { '200': { description: 'Unliked' } } },
      },
      '/api/pets/{id}/comments': {
        get: { summary: 'List comments', parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string' } }], responses: { '200': { description: 'Comment list' } } },
        post: { summary: 'Create comment', security: [{ bearerAuth: [] }], parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string' } }], responses: { '201': { description: 'Created' } } },
      },
      '/api/comments/{commentId}': {
        delete: { summary: 'Delete comment', security: [{ bearerAuth: [] }], parameters: [{ name: 'commentId', in: 'path', required: true, schema: { type: 'string' } }], responses: { '200': { description: 'Deleted' }, '403': { description: 'Forbidden' } } },
      },
      '/api/chats': {
        get: {
          summary: 'Get chat list',
          security: [{ bearerAuth: [] }],
          responses: { '200': { description: 'Chat list' } },
        },
        post: {
          summary: 'Create or get chat',
          security: [{ bearerAuth: [] }],
          responses: { '201': { description: 'Chat created' } },
        },
      },
      '/api/chats/{chatId}': {
        get: { summary: 'Get chat meta', security: [{ bearerAuth: [] }], parameters: [{ name: 'chatId', in: 'path', required: true, schema: { type: 'string' } }], responses: { '200': { description: 'Chat meta' }, '403': { description: 'Forbidden' } } },
      },
      '/api/chats/{chatId}/messages': {
        get: { summary: 'Get chat messages', security: [{ bearerAuth: [] }], parameters: [{ name: 'chatId', in: 'path', required: true, schema: { type: 'string' } }], responses: { '200': { description: 'Message list' } } },
        post: { summary: 'Send chat message', security: [{ bearerAuth: [] }], parameters: [{ name: 'chatId', in: 'path', required: true, schema: { type: 'string' } }], responses: { '201': { description: 'Message sent' } } },
      },
      '/api/chats/{chatId}/read': {
        post: { summary: 'Mark messages as read', security: [{ bearerAuth: [] }], parameters: [{ name: 'chatId', in: 'path', required: true, schema: { type: 'string' } }], responses: { '200': { description: 'Read updated' } } },
      },
      '/api/chats/{chatId}/leave': {
        post: { summary: 'Leave chat', security: [{ bearerAuth: [] }], parameters: [{ name: 'chatId', in: 'path', required: true, schema: { type: 'string' } }], responses: { '200': { description: 'Left' } } },
      },
      '/api/chats/{chatId}/report': {
        post: { summary: 'Report chat', security: [{ bearerAuth: [] }], parameters: [{ name: 'chatId', in: 'path', required: true, schema: { type: 'string' } }], responses: { '201': { description: 'Reported' } } },
      },
      '/api/tips/analyze': {
        post: {
          summary: 'Analyze tip images',
          security: [{ bearerAuth: [] }],
          responses: { '201': { description: 'Queued' } },
        },
      },
      '/api/tips/{tipId}': {
        get: { summary: 'Get tip analysis status', security: [{ bearerAuth: [] }], parameters: [{ name: 'tipId', in: 'path', required: true, schema: { type: 'string' } }], responses: { '200': { description: 'Tip status' } } },
      },
      '/api/tips/{tipId}/send': {
        post: { summary: 'Send tip to chat', security: [{ bearerAuth: [] }], parameters: [{ name: 'tipId', in: 'path', required: true, schema: { type: 'string' } }], responses: { '201': { description: 'Sent' } } },
      },
      '/api/notifications': {
        get: { summary: 'List notifications', security: [{ bearerAuth: [] }], responses: { '200': { description: 'Notification list' } } },
      },
      '/api/notifications/unread-count': {
        get: { summary: 'Unread notification count', security: [{ bearerAuth: [] }], responses: { '200': { description: 'Unread count' } } },
      },
      '/api/notifications/{id}/read': {
        post: { summary: 'Mark notification as read', security: [{ bearerAuth: [] }], parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string' } }], responses: { '200': { description: 'Read' } } },
      },
      '/api/notifications/read-all': {
        post: { summary: 'Mark all notifications as read', security: [{ bearerAuth: [] }], responses: { '200': { description: 'All read' } } },
      },
      '/api/uploads/presign': {
        post: { summary: 'Create signed upload URL', security: [{ bearerAuth: [] }], responses: { '201': { description: 'Presigned URL created' } } },
      },
      '/api/devices/register': {
        post: { summary: 'Register device token', security: [{ bearerAuth: [] }], responses: { '201': { description: 'Registered' } } },
      },
      '/api/devices/{tokenId}': {
        delete: { summary: 'Delete device token', security: [{ bearerAuth: [] }], parameters: [{ name: 'tokenId', in: 'path', required: true, schema: { type: 'string' } }], responses: { '200': { description: 'Deleted' } } },
      },
    },
  },
  apis: [],
};

const openapiSpec = swaggerJSDoc(options);

function mountSwagger(app) {
  app.get('/docs/openapi.json', (req, res) => res.json(openapiSpec));
  app.use('/docs', swaggerUi.serve, swaggerUi.setup(openapiSpec));
}

module.exports = {
  mountSwagger,
  openapiSpec,
};
