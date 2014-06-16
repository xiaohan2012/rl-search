import MySQLdb, MySQLdb.cursors
from boilerpipe.extract import Extractor
from time import time

from setting import MYSQL_CONN_SETTING

def main(offset, limit, extractor_name = 'ArticleExtractor'): 
    upd_conn = MySQLdb.connect(**MYSQL_CONN_SETTING)
    
    MYSQL_CONN_SETTING['cursorclass'] = MySQLdb.cursors.SSCursor
    sel_conn = MySQLdb.connect(**MYSQL_CONN_SETTING)

    sel_c = sel_conn.cursor()
    print 'SELECT ING...'
    print 'SELECT id, uncompress(crawled_html) from webpage where !isnull(crawled_html) and length(crawled_html) > 0 and isnull(processed_content) and id >= %d and id < %d ' %(offset, offset + limit)
    sel_c.execute('SELECT id, uncompress(crawled_html) from webpage where !isnull(crawled_html) and length(crawled_html) > 0 and isnull(processed_content) and id >= %s and id < %s ', (offset, offset + limit))
        
    upd_c = upd_conn.cursor()
    
    counter = 0
    frequency = 10
    start = time()
    
    while True:
        row = sel_c.fetchone()
        if row is None:
            break
            
        if row[1] is None: #corrupted html
            continue
        
        id, html = row
        try:
            print id
            extractor = Extractor(extractor=extractor_name, html=html)
            content = extractor.getText()
        except:
            print 'Some error occurred..'
            
        upd_c.execute('UPDATE webpage set processed_content = %s where id=%s', (content, id))
        counter += 1
        
        if counter % frequency == 0:
            print 'procssed %d items, used %f seconds' %(frequency, time() - start)
            start = time()
            upd_conn.commit()
            counter = 0

if __name__ == "__main__":
    import sys
    offset = sys.argv[1]
    limit = sys.argv[2]
    main(int(offset), int(limit))

