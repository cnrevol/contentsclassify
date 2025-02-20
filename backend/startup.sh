#!/bin/bash
cd /home/site/wwwroot
source /antenv/bin/activate

# 应用数据库迁移
python backend/manage.py migrate

# 启动 Gunicorn
gunicorn --chdir backend backend.wsgi:application --bind=0.0.0.0:8000 --log-file=- 