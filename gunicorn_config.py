import multiprocessing

# ワーカープロセスの数
workers = multiprocessing.cpu_count() * 2 + 1

# ワーカークラスの指定
worker_class = 'sync'

# タイムアウト設定
timeout = 120

# バインドするアドレスとポート
bind = "0.0.0.0:$PORT"

# アクセスログの設定
accesslog = '-'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# エラーログの設定
errorlog = '-'
loglevel = 'info' 