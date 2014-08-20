MYSQL_PWD = "xh24206688"
MYSQL_DB = "archive"
MYSQL_USER = "hxiao"
MYSQL_HOST = "ugluk"
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
                       


REDIS_HOST = 'ugluk'
REDIS_DB = "scinet3"
REDIS_PORT = 6379

REDIS_CONN_SETTING = {
    'host': REDIS_HOST,
    'port': REDIS_PORT,
    'db': REDIS_DB
}
