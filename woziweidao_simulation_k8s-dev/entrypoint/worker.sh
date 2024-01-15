#celery -A task_celery worker --loglevel=INFO --pool=threads --concurrency=4 --time-limit=240
python3 task_celery.py