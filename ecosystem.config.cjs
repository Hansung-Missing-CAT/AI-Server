module.exports = {
  apps: [
    {
      name: 'missing-pet-image-server',
      cwd: './CAT_00',
      script: 'python3',
      args: '-m http.server 18080 --bind 127.0.0.1',
      watch: false,
      autorestart: true,
    },
    {
      name: 'missing-pet-server',
      cwd: './server',
      script: 'src/server.js',
      interpreter: 'node',
      watch: false,
      autorestart: true,
      env_file: './.env',
      env: {
        NODE_ENV: 'development',
        PORT: 3000,
      },
    },
    {
      name: 'missing-pet-ai-server',
      cwd: './ai_server',
      script: '.venv/bin/uvicorn',
      args: 'main:app --host 127.0.0.1 --port 8000',
      interpreter: 'none',
      watch: false,
      autorestart: true,
      env_file: './.env',
      env: {
        PYTHONUNBUFFERED: '1',
      },
    },
    {
      name: 'missing-pet-ai-worker',
      cwd: './ai_server',
      script: '.venv/bin/python',
      args: 'workers/ai_worker.py',
      autorestart: true,
      watch: false,
      env_file: './.env',
      env: {
        PYTHONUNBUFFERED: '1',
      },
    },
  ],
};
