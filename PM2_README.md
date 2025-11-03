# NeoBank PM2 Deployment

## Quick Start

### Start the application
```bash
pm2 start ecosystem.config.js
```

### Stop the application
```bash
pm2 stop neobank
```

### Restart the application
```bash
pm2 restart neobank
```

### Reload without downtime
```bash
pm2 reload neobank
```

### Delete the application from PM2
```bash
pm2 delete neobank
```

### View logs
```bash
# Real-time logs
pm2 logs neobank

# Error logs only
pm2 logs neobank --err

# Output logs only
pm2 logs neobank --out

# Last 100 lines
pm2 logs neobank --lines 100
```

### Monitor
```bash
pm2 monit
```

### Status
```bash
pm2 status
```

### Save PM2 process list (auto-start on reboot)
```bash
pm2 save
pm2 startup
```

## Configuration

- **Workers**: 4 Gunicorn workers
- **Port**: 6767
- **Bind**: 0.0.0.0 (all interfaces)
- **Max Memory**: 1GB (auto-restart if exceeded)
- **Auto-restart**: Enabled
- **Logs**: `./logs/` directory
  - `err.log` - Error logs
  - `out.log` - Output logs
  - `combined.log` - All logs

## Application Details

- **Name**: neobank
- **Type**: Python Flask application with Gunicorn WSGI server
- **Start Script**: `start.sh`
- **Environment**: Production

## Testing

Test if the application is running:
```bash
curl -I http://localhost:6767
```

Access the application:
```
http://localhost:6767
http://your-server-ip:6767
http://neobank.shagato.me
```

## Useful Commands

```bash
# Show application info
pm2 show neobank

# Flush all logs
pm2 flush

# Update PM2
pm2 update

# Restart all PM2 processes
pm2 restart all

# Stop all processes
pm2 stop all
```

## Files

- `ecosystem.config.js` - PM2 configuration file
- `start.sh` - Bash script that activates venv and starts Gunicorn
- `logs/` - Directory for application logs
