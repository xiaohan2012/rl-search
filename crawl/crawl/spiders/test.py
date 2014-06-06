from scrapy import log
from scrapy.http import Request
from scrapy.contrib.spiders import CrawlSpider, Rule

from time import time

from crawl.items import PageItem

import re, os, datetime
from chardet import detect 
from pyquery import PyQuery as pq

from config import *
from util import get_links_csv

class FengSpider(CrawlSpider):
    name = 'feng'
    def __init__(self, *args, **kwargs):
        super(FengSpider, self).__init__(*args, **kwargs)
        if kwargs.has_key('path') and len(kwargs['path']):
            self.path = kwargs['path']
            self.start_urls = get_links_csv(kwargs['path'])
        else:
            raise Exception('path should be passed')
        
    def start_requests(self):
        for id, url in self.start_urls:
            yield Request(url=url,
                          meta = {'id': id, '__start_time': time()}, #we need the id attr to do the database update
                          dont_filter = True)

    def parse(self, response):
        i = PageItem()
        print time() - response.meta['__start_time']
        return i
