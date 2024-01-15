import config

# # =================aliyun=================
# MYSQL_HOST = "10.119.113.148"
# MYSQL_PORT = 3306
# MYSQL_USER = "root"
# MYSQL_PASSWD = "zaibai3eirooc9aekaeX1Eirie3bie3f"
# MYSQL_DB = "flaskdb"

# # =================local-test=================
# MYSQL_HOST = "192.168.17.145"
# MYSQL_PORT = 3306
# MYSQL_USER = "root"
# MYSQL_PASSWD = "123456"
# MYSQL_DB = "flaskdb"

# =================general=================

MYSQL_HOST = config.CONFIG.MYSQL_HOST
MYSQL_PORT = config.CONFIG.MYSQL_PORT
MYSQL_USER = config.CONFIG.MYSQL_USER
MYSQL_PASSWD = config.CONFIG.MYSQL_PASSWD
MYSQL_DB = config.CONFIG.MYSQL_DB