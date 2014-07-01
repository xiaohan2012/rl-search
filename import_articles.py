from pyquery import PyQuery as pq

import MySQLdb

from setting import MYSQL_CONN_SETTING

def get_data(xml_path):
    d = pq(open(xml_path).read())

    counter = 0
    for a in d.children():
        data = {}
        fields = ['title', 'venue', 'abstract', 'author', 'url']
        for f in fields:
            data[f] = a.find(f).text
        counter += 1
        if counter % 1000 == 0:
            print "%d finished" %counter
        yield data

def insert_data(data, table = "archive"):
    conn = MySQLdb.connect(**MYSQL_CONN_SETTING)
    x = conn.cursor()
    x.execute('delete from %s;' %table)
    x.execute('alter table %s auto_increment=1;' %table)
    for row in data:
        x.execute('INSERT INTO %s(title, venue, abstract, author, url) VALUES(%%s, %%s, %%s, %%s, %%s)' %(table), (row['title'], row['venue'], row['abstract'], row['author'], row['url']))
        conn.commit()


if __name__ == "__main__":
    data = get_data('corpus_collection/articles_70k.xml')
    insert_data(data)
