import multiprocessing

# 绑定的IP和端口
bind = '0.0.0.0:5000'

# 工作进程数
workers = multiprocessing.cpu_count() * 2 + 1

# 工作模式
worker_class = 'sync'

# 每个工作进程的线程数
threads = 4

# 超时时间
timeout = 300

# 最大客户端并发数量
worker_connections = 1000

# 进程名称前缀
proc_name = 'greenscore'

# 访问日志文件
accesslog = 'logs/gunicorn_access.log'

# 错误日志文件
errorlog = 'logs/gunicorn_error.log'

# 日志级别
loglevel = 'info'

# 是否后台运行
daemon = False

# 优雅重启
graceful_timeout = 120

# 重启间隔
max_requests = 2000
max_requests_jitter = 400