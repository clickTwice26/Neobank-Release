module.exports = {
  apps: [{
    name: 'neobank',
    script: './start.sh',
    cwd: '/home/raju/30_days_challenge/NeoBank',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      PYTHONUNBUFFERED: '1'
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true
  }]
};
