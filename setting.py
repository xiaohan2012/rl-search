MYSQL_PWD = "your db password"
MYSQL_DB = "mysql database name"
MYSQL_USER = "mysql db username"
MYSQL_HOST = "mysql db host"
MYSQL_CONN_SETTING = {'host': MYSQL_HOST,
                      'user':MYSQL_USER,
                      'passwd':MYSQL_PWD,
                      'port': 3306,
                      'db':MYSQL_DB,
                      'charset':"utf8", 
                      'use_unicode':True}


TORNDB_CONN_SETTING = {'host': MYSQL_HOST,
                      'user':MYSQL_USER,
                      'password':MYSQL_PWD,
                      'database':MYSQL_DB}
                       


REDIS_HOST = "redis host"
REDIS_DB = "redis db name"
REDIS_PORT = 6379

REDIS_CONN_SETTING = {
    'host': REDIS_HOST,
    'port': REDIS_PORT,
    'db': REDIS_DB
}
