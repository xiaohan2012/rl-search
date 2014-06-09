# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import MySQLdb
from json import dumps

from spiders import config
from chardet import detect 
from setting import  MYSQL_HOST, MYSQL_PWD, MYSQL_DB, MYSQL_USER

conn = MySQLdb.connect(host= MYSQL_HOST,
                       user = MYSQL_USER,
                       passwd = MYSQL_PWD,
                       db = MYSQL_DB,
                       charset = "utf8")

c = conn.cursor()

class ToUnicodePipeline(object):
    def process_item(self, item, spider):
        #too slow
        item['html'] = item['html'].decode(detect(item['html'])['encoding'], 'ignore')
        return item
        
class ToDBPipeline(object):
    def process_item(self, item, spider):
        #save it to database
        c.execute("UPDATE webpage SET crawled_keywords=%s, crawled_description=%s, crawled_html=compress(%s) WHERE id=%s", (dumps(item.get('keywords', [])), 
                                                                                                                            item.get('description', ''),
                                                                                                                            item['html'],
                                                                                                                            item['id']
                                                                                                                        ))
        conn.commit()
        return item
