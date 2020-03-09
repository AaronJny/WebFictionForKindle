# 端口
bind = '0.0.0.0:7777'
# 并发数
workers = 2
# 异步模式
worker_class = 'gevent'
# app.py的路径
chdir = '.'
proc_name = 'gunicorn.proc'
