"""
Utility that moves the webpages in JSON format to MySQL database
"""
from util import get_page_json
from json import dumps
import db

conn = db.get_conn()

x = conn.cursor()
print 'runcating table `webpage`'

x.execute('TRUNCATE webpage;')

import glob
for path in glob.glob("/export/data/mmbrain/filtered.crawled/*"):
    print path
    print 'Tranporting to table `webpage`'
    total = 477444
    counter = 0;
    for page in get_page_json(path):
        try:
            x.execute("""INSERT INTO webpage (url, keywords) VALUES (%s, %s)""",
                      (page['url'],
                       dumps(page['keywords'])))
            counter += 1
            if counter % 1000 == 0:
                print "%d inserted" %(counter)
                conn.commit()

        except:
            print 'error occurred'
            conn.rollback()

conn.commit()
conn.close()
