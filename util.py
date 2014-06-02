"""""                                                                                                                                                                                                          
utility functions                                                                                                                                                                                            
"""
import MySQLdb, MySQLdb.cursors
from json import loads
from setting import MYSQL_HOST, MYSQL_PWD, MYSQL_DB, MYSQL_USER

def get_links_db(offset, limit = None):
    conn = MySQLdb.connect(host= MYSQL_HOST,
                           user=MYSQL_USER,
                           passwd=MYSQL_PWD,
                           db=MYSQL_DB,
                           charset="utf8", 
                           use_unicode=True,
                           cursorclass = MySQLdb.cursors.SSCursor)
    x = conn.cursor()
    sql = "SELECT id, url FROM webpage "
    sql += ("WHERE  id >= %d" %offset)
    
    if limit:
        sql += (" LIMIT %d" %(limit))
        
    sql += ';'
    print "SQL:",sql

    x.execute(sql)
    
    while True:
        row = x.fetchone()
        if row:
            yield row
        else:
            break
    conn.close()
    
def get_links(filename, lang = "en", category="editorial"):
    """                                                                                                                                                                                                         Given the filename, extract the urls of given language                                                                                                                                                   
    Return:                                                                                                                                                                                                  
    generator of the filtered URL list                                                                                                                                                                       
    """
    with open(filename) as f:
        for line in f:
            page_json = loads(line)
            if page_json.has_key("contentLanguage") and page_json["contentLanguage"] == lang and \
               page_json.has_key("category") and page_json["category"] == category:
                yield page_json['url']

def get_page_json(filepath, withkeywords = True):
    from codecs import open
    with open(filepath, 'r', 'utf8') as f:
        for line in f:
            page_json = loads(line)
            if withkeywords and page_json['keywords']:
                yield page_json
            
def mbrain_data2db(filename, category = "editorial", lang = "en"):
    conn = MySQLdb.connect(host= MYSQL_HOST,
                           user=MYSQL_USER,
                           passwd=MYSQL_PWD,
                           db=MYSQL_DB,
                           charset="utf8", 
                           use_unicode=True)
    x = conn.cursor()
    fields = ["url","title","category","contentLanguage","publishDate","authorName","region","plainTextContent"]

    field_sql_string = ','.join(fields)
    value_sql_tmpl = '%s,%s,%s,%s,"%s",%s,%s,%s'
    sql_tmpl = "INSERT INTO webpage(%s) values(%s)" %(field_sql_string, value_sql_tmpl)
    counter = 0
    
    with open(filename) as f:
        for line in f:
            page_json = loads(line)
            if page_json.has_key("contentLanguage") and page_json["contentLanguage"] == lang and \
               page_json.has_key("category") and page_json["category"] == category:
                
                x.execute(sql_tmpl, 
                             (page_json.get(field) for field in fields))
                counter += 1
                if counter % 1000 == 0:
                    print "%d inserted" %(counter)
                    conn.commit()
    conn.commit()
    conn.close()

def truncate_table(table="webpage"):
    conn = MySQLdb.connect(host= MYSQL_HOST,
                           user=MYSQL_USER,
                           passwd=MYSQL_PWD,
                           db=MYSQL_DB,
                           charset="utf8", 
                           use_unicode=True)
    x = conn.cursor()
    x.execute('truncate table %s' %table)
    conn.commit()
    
if __name__ == "__main__":
    mbrain_data2db("/export/data/mmbrain/filtered/solrdocs.0-6456635.json.filtered")
