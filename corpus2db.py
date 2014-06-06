import MySQLdb
from nltk.corpus import brown
from json import dumps

from kw import extract
from setting import MYSQL_CONN_SETTING


def brown2db(table="brown"):
    conn = MySQLdb.connect(**MYSQL_CONN_SETTING)
    x = conn.cursor()
    
    x.execute('TRUNCATE %s' %table)
    conn.commit()
    
    counter = 0
    
    for fid in brown.fileids():
        words = brown.words(fid)
        text = ' '.join(words)

        keywords = extract(text)
        sql = "INSERT INTO %s(url, processed_keywords) values(%%s, %%s)" %(table)
        x.execute(sql, (fid, dumps(keywords)))
        conn.commit()
        counter += 1
        
        print "%.3f %% completed" %(counter / 500. * 100)
    conn.close()

if __name__ == "__main__":
    brown2db()
