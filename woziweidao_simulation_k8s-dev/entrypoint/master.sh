celery -A task_celery flower --loglevel=INFO --conf=celeryconfig.py --address=0.0.0.0 --port=5555 &
gunicorn -b 0.0.0.0:5000 --worker-class eventlet -w 1 demo:app