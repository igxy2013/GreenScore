# Nginx 配置指南

本文档提供了在 GreenScore 项目中使用 Nginx 的详细说明，包括安装、配置、启动和停止服务以及常见问题的解决方案。

## 目录

- [安装 Nginx](#安装-nginx)
- [配置文件说明](#配置文件说明)
- [启动和停止 Nginx](#启动和停止-nginx)
- [与 Gunicorn 集成](#与-gunicorn-集成)
- [常见问题解决](#常见问题解决)

## 安装 Nginx

### Windows 环境

1. 访问 [Nginx 官方网站](http://nginx.org/en/download.html) 下载最新的稳定版本
2. 解压下载的 zip 文件到一个合适的目录，例如 `C:\nginx`
3. 将 Nginx 目录添加到系统环境变量 PATH 中（可选，但推荐）

### Linux 环境

#### Debian/Ubuntu

```bash
sudo apt update
sudo apt install nginx
```

#### CentOS/RHEL

```bash
sudo yum install epel-release
sudo yum install nginx
```

## 配置文件说明

GreenScore 项目包含一个预配置的 `nginx.conf` 文件，该文件已经针对项目进行了优化。以下是主要配置部分的说明：

### 基本设置

```nginx
worker_processes auto;  # 自动设置工作进程数量为CPU核心数
pid logs/nginx.pid;     # PID文件位置

events {
    worker_connections 1024;  # 每个工作进程的最大连接数
    multi_accept on;          # 一次接受所有新连接
}
```

### HTTP 服务器设置

```nginx
http {
    # 基本设置
    sendfile on;                    # 启用sendfile
    tcp_nopush on;                  # 优化数据包传输
    tcp_nodelay on;                 # 禁用Nagle算法
    keepalive_timeout 65;           # 保持连接超时时间
    types_hash_max_size 2048;       # 类型哈希表的最大大小
    server_tokens off;              # 隐藏Nginx版本信息
    
    # MIME类型设置
    include mime.types;
    default_type application/octet-stream;
    
    # 日志设置
    access_log logs/access.log;
    error_log logs/error.log;
    
    # Gzip压缩设置
    gzip on;
    # ... 其他gzip设置 ...
}
```

### 反向代理设置

```nginx
location / {
    proxy_pass http://127.0.0.1:5010;  # 转发到Gunicorn/Waitress
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # WebSocket支持
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    
    # 超时设置
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
}
```

## 启动和停止 Nginx

### Windows 环境

在项目根目录下，我们提供了两个批处理脚本来管理 Nginx 服务：

- `start_nginx.bat` - 启动 Nginx 服务
- `stop_nginx.bat` - 停止 Nginx 服务

#### 手动启动和停止

如果您没有使用提供的脚本，可以手动执行以下命令：

```batch
# 启动 Nginx
start nginx -c "D:\PY\GreenScore\nginx.conf"

# 停止 Nginx
nginx -s stop

# 重新加载配置
nginx -s reload
```

### Linux 环境

```bash
# 启动 Nginx
sudo systemctl start nginx

# 停止 Nginx
sudo systemctl stop nginx

# 重启 Nginx
sudo systemctl restart nginx

# 重新加载配置
sudo systemctl reload nginx

# 检查 Nginx 状态
sudo systemctl status nginx
```

## 与 Gunicorn 集成

GreenScore 项目使用 Gunicorn 作为 WSGI 服务器，Nginx 作为反向代理。这种架构提供了更好的性能和安全性。

### 启动顺序

1. 首先启动 Gunicorn：
   - Windows: 执行 `run.bat`
   - Linux: 执行 `./start.sh`

2. 然后启动 Nginx：
   - Windows: 执行 `start_nginx.bat`
   - Linux: `sudo systemctl start nginx`

### 配置检查

确保 Nginx 配置中的 `proxy_pass` 指向正确的 Gunicorn 地址和端口（默认为 `http://127.0.0.1:5010`）。

## 常见问题解决

### 端口冲突

如果 Nginx 无法启动，可能是因为端口 80 已被占用。您可以：

1. 修改 `nginx.conf` 中的 `listen` 指令，使用其他端口（如 8080）
2. 找出并关闭占用端口 80 的程序

### 权限问题

#### Windows

在 Windows 上，如果遇到权限问题，请尝试以管理员身份运行命令提示符或 PowerShell。

#### Linux

在 Linux 上，确保 Nginx 有权访问项目目录：

```bash
sudo chown -R www-data:www-data /path/to/GreenScore
sudo chmod -R 755 /path/to/GreenScore
```

### 日志检查

如果遇到问题，请检查以下日志文件：

- Nginx 错误日志：`logs/greenscore_error.log`
- Nginx 访问日志：`logs/greenscore_access.log`
- Gunicorn 错误日志：`logs/gunicorn_error.log`
- Gunicorn 访问日志：`logs/gunicorn_access.log`

### 配置测试

在应用任何配置更改之前，建议先测试配置文件的语法：

```bash
nginx -t -c /path/to/nginx.conf
```

如果配置文件有语法错误，此命令将显示详细信息。