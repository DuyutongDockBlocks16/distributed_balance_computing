import os

class DevelopmentConfig:
    """Development configuration"""

    # mysql
    MYSQL_HOST = "192.168.17.145"
    MYSQL_PORT = 3306
    MYSQL_USER = "root"
    MYSQL_PASSWD = "123456"
    MYSQL_DB = "flaskdb"

    # redis
    redis_host = '127.0.0.1'
    redis_db = 0
    redis_port = 6379

    # broker_url & result_backend
    broker_url = 'redis://127.0.0.1:6379/0'
    result_backend = 'redis://127.0.0.1:6379/0'


class TestingConfig:
    """Testing configuration"""

    # mysql
    MYSQL_HOST = "192.168.17.145"
    MYSQL_PORT = 3306
    MYSQL_USER = "root"
    MYSQL_PASSWD = "123456"
    MYSQL_DB = "flaskdb"

    # redis
    redis_host = '192.168.240.19'
    redis_db = 0
    redis_port = 6379

    # broker_url & result_backend
    broker_url = 'redis://192.168.240.19:6379/0'
    result_backend = 'redis://192.168.240.19:6379/0'


class ProductionConfig:
    """Production configuration"""
    # mysql
    MYSQL_HOST = "10.119.114.2"
    MYSQL_PORT = 3306
    MYSQL_USER = "root"
    MYSQL_PASSWD = "iihi2eo7ahl3eeDei5iezuuleepheimi"
    MYSQL_DB = "flaskdb"

    # redis
    redis_host = '10.119.114.3'
    redis_db = 0
    redis_port = 6379

    # broker_url & result_backend
    broker_url = 'redis://10.119.114.3:6379/0'
    result_backend = 'redis://10.119.114.3:6379/0'

class ProductionConfigDetail:
    """Production detail configuration"""
    # mysql
    MYSQL_HOST = "10.119.114.2"
    MYSQL_PORT = 3306
    MYSQL_USER = "root"
    MYSQL_PASSWD = "iihi2eo7ahl3eeDei5iezuuleepheimi"
    MYSQL_DB = "flaskdb"

    # redis
    redis_host = '127.0.0.1'
    redis_db = 0
    redis_port = 6379

    # broker_url & result_backend
    broker_url = 'redis://127.0.0.1:6379/0'
    result_backend = 'redis://127.0.0.1:6379/0'


CONFIG_DICT = {
    'development': DevelopmentConfig(),
    'testing': TestingConfig(),
    'production': ProductionConfig(),
    'default': DevelopmentConfig(),
    'production_detail':ProductionConfigDetail()
}


ENV = os.getenv("ENV", "development")
CONFIG = CONFIG_DICT.get(ENV)
print(CONFIG.redis_host)
print(CONFIG.redis_port)
print(CONFIG.redis_db)


detail_redis_ip='devwzwd_sim_test-001-redis.service.jjdev.local'
detail_redis_port=7385
detail_redis_pwd='redis_devwzwd_sim_test001_JJMatch'

# detail_redis_ip='127.0.0.1'
# detail_redis_port=7385
# detail_redis_pwd='redis_devwzwd_sim_test001_JJMatch'
