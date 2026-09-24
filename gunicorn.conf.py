# Gunicorn config for Render free tier (512 MB RAM)

workers = 1
timeout = 120
preload_app = True
bind = "0.0.0.0:10000"
accesslog = "-"
errorlog = "-"
loglevel = "info"