#!/bin/bash
cd /home/raju/30_days_challenge/NeoBank
source venv/bin/activate
exec gunicorn -w 4 -b 0.0.0.0:6767 app:app
