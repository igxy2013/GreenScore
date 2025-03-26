#!/bin/bash

# 确保脚本在项目根目录下运行
cd "$(dirname "$0")"

# 创建日志目录（如果不存在）
mkdir -p logs

# 设置环境变量
export FLASK_APP=app.py
export FLASK_ENV=development

# 如果存在.env文件，加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 如果存在虚拟环境，则激活它
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 启动Gunicorn服务器
echo "正在启动Gunicorn服务器..."
exec gunicorn \
    --bind 0.0.0.0:5010 \
    --workers 3 \
    --worker-class sync \
    --threads 4 \
    --timeout 300 \
    --access-logfile logs/gunicorn_access.log \
    --error-logfile logs/gunicorn_error.log \
    --log-level info \
    --reload \
    app:app