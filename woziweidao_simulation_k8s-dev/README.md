# start flower
celery -A task_celery flower --loglevel=INFO --conf=celeryconfig.py --address=0.0.0.0 --port=5555

# start master
python3 demo.py

# start worker
celery -A task_celery worker --loglevel=INFO --pool=threads --concurrency=2

# lupa库安装
sudo cp libtolua.so /usr/lib/

sudo ldconfig

pip install lupa-1.10-cp38-cp38-linux_x86_64.whl

# 测试
python test.py 1 1 1
