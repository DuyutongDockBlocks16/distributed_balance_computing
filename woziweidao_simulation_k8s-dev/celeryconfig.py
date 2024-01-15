import config


# # local-host
# broker_url = 'redis://127.0.0.1:6379'
# result_backend = 'redis://127.0.0.1:6379'

# # 昌平集群
# broker_url = 'redis://192.168.240.19:6379'
# result_backend = 'redis://192.168.240.19:6379'

# # aliyun
# broker_url = 'redis://10.119.113.149:6379'
# result_backend = 'redis://10.119.113.149:6379'

# general
broker_url = config.CONFIG.broker_url
result_backend = config.CONFIG.result_backend
worker_prefetch_multiplier = 3
# redis_max_connections = 5000


accept_content = ['json']
timezone = 'Asia/Shanghai'
enable_utc = False
purge_offline_workers = 10
result_expires = 30
# broker_pool_limit = 3000

# task_soft_time_limit=30
# task_time_limit=10