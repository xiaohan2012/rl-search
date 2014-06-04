"""
Utility that moves the webpages in JSON format to MySQL database
"""
import MySQLdb
from util import get_page_json
from json import dumps
from setting import MYSQL_HOST, MYSQL_PWD, MYSQL_DB, MYSQL_USER

conn = MySQLdb.connect(host= MYSQL_HOST,
                       user=MYSQL_USER,
                       passwd=MYSQL_PWD,
                       db=MYSQL_DB,
                       charset="utf8", 
                       use_unicode=True)

x = conn.cursor()
table = 'test_webpage'

print 'truncating table %s' %table

x.execute('TRUNCATE %s;' %table)

import glob
for path in glob.glob("/export/data/mmbrain/filtered.crawled/solrdocs.0-6456635.json.filtered.crawled"):
    print path
    print 'Tranporting to table `%s`' %table
    total = 477444
    counter = 0;
    for page in get_page_json(path):
        sql = """INSERT INTO %s (url, crawled_keywords) VALUES (%%s, %%s)""" %table
        
        x.execute(sql, (page['url'],
                        dumps(page['keywords'])))
        counter += 1
        if counter % 1000 == 0:
            print "%d inserted" %(counter)
            conn.commit()


conn.commit()
conn.close()
