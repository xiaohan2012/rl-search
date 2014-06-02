# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import MySQLdb
from json import dumps

from spiders import config
from setting import  MYSQL_HOST, MYSQL_PWD, MYSQL_DB, MYSQL_USER

conn = MySQLdb.connect(host= MYSQL_HOST,
                       user = MYSQL_USER,
                       passwd = MYSQL_PWD,
                       db = MYSQL_DB,
                       charset = "utf8", 
                       use_unicode = True)

c = conn.cursor()
class PagePipeline(object):
    def process_item(self, item, spider):
        #save it to database
        c.execute("UPDATE webpage SET crawled_content=%s, crawled_keywords=%s, crawled_language=%s, crawled_description=%s WHERE id=%s", (item['content'], 
                                                                                                                                          dumps(item['keywords']), 
                                                                                                                                          item['language'],
                                                                                                                                          item['description'],
                                                                                                                                          item['id']))
        conn.commit()
        return item
