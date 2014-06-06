"""""                                                                                                                                                                                                          
utility functions                                                                                                                                                                                            
"""
import MySQLdb, MySQLdb.cursors
from json import loads
from setting import MYSQL_CONN_SETTING

conn = MySQLdb.connect(**MYSQL_CONN_SETTING)

def is_url_crawled(id):
    c = conn.cursor()
    c.execute('SELECT id from webpage where id = %s and !isnull(crawled_html) and length(crawled_html) != 0', (id,))
    return (c.fetchone() is not None)

#deprecated
def get_links_db(offset, limit = None):
    START_ID = 110863
    conn = MySQLdb.connect(host= MYSQL_HOST,
                           user=MYSQL_USER,
                           passwd=MYSQL_PWD,
                           db=MYSQL_DB,
                           charset="utf8", 
                           use_unicode=True)
    x = conn.cursor()
    sql = "SELECT id, url FROM webpage "
    sql += ("WHERE  id >= %d" %START_ID + offset)
    
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

def get_links_csv(path):
    """
    get the (id, url) tuples from csv file at `path`
    """
    with open(path, 'r') as f:
        for line in f:
            id, url = line.split()
            yield int(id), url
            
def get_links(filename, lang = "en", category="editorial"):
    """                                                                                                                                                                                                         Given the filename, extract the urls of given language                                                                                                                                                   
    Return:                                                                                                                                                                                                  
    generator of the filtered URL list                                                                                                                                                                       
    """
    print 'getting links'
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
            try:
                page_json = loads(line)
            except:#skip bad json
                continue
            if withkeywords and page_json['keywords']:
                yield page_json
            
def mbrain_data2db(filename, category = "editorial", lang = "en", table="webpage"):
    conn = MySQLdb.connect(**MYSQL_CONN_SETTING)
    x = conn.cursor()
    fields = ["url","title","category","contentLanguage","publishDate","authorName","region","plainTextContent"]

    field_sql_string = ','.join(fields)
    value_sql_tmpl = '%s,%s,%s,%s,"%s",%s,%s,%s'
    sql_tmpl = "INSERT INTO %s(%s) values(%s)" %(table, field_sql_string, value_sql_tmpl)
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

def count_by_condition(path, condition):
    counter = 0
    for page in get_page_json(path):
        if condition(page):
            counter += 1
        if counter % 1000 == 0:
            print "processed %d" %counter
    return counter

def truncate_table(table="webpage"):
    conn = MySQLdb.connect(**MYSQL_CONN_SETTING)
    x = conn.cursor()
    x.execute('truncate table %s' %table)
    conn.commit()
    
if __name__ == "__main__":
    import glob
    total = 0
    for path in glob.glob("/export/data/mmbrain/filtered.crawled/solrdocs*"):
        print "Dealing with %s" %path
        total += count_by_condition(path, lambda d: len(d['keywords']) > 0)
        print total
    print total

