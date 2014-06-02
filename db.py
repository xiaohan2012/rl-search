import MySQLdb
import MySQLdb.cursors

def get_conn():
    conn = MySQLdb.connect(host= "localhost",
                           user="root",
                           passwd="uGluk!@#",
                           db="scinet3",
                           charset="utf8", 
                           use_unicode=True,
                           cursorclass = MySQLdb.cursors.SSCursor)
    return conn
