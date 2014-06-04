from scrapy import log
from scrapy.http import Request
from scrapy.contrib.spiders import CrawlSpider, Rule

from time import time

from crawl.items import PageItem

import re, os, datetime
from pyquery import PyQuery as pq

from config import *
from util import get_links_csv

class BasicSpider(CrawlSpider):
    name = 'basic'
    
    def __init__(self, *args, **kwargs):
        super(BasicSpider, self).__init__(*args, **kwargs)
        if kwargs.has_key('path') and len(kwargs['path']):
            self.path = kwargs['path']
            self.start_urls = get_links_csv(kwargs['path'])
        else:
            raise Exception('path should be passed')
        #self.start_urls = [(110882, 'http://www.limburger.nl/article/20130911/ANPNIEUWS01/130919470')]

    def start_requests(self):
        for id, url in self.start_urls:
            yield Request(url=url,
                          meta = {'id': id}, #we need the id attr to do the database update
                          dont_filter = True)
            
    def parse(self, response):
        i = PageItem()
        i["id"] = response.meta["id"]
        #save the raw html, so that we don't need to crawl again..
        
        i['html'] = response.body

        doc = pq(response.body)

        #preprocessing, remove script and link elements
        doc.find("body script").remove()
        doc.find("body link").remove()
        
        #get the keywords information
        kw_metas = doc.find('meta[name="keywords"]') #also dc tags

        if len(kw_metas) == 1:            
            i['keywords'] = [kw.strip() 
                             for kw in re.split("[,;]", kw_metas.attr("content") or "")]
        elif len(kw_metas) >= 2:
            #multiple keyword elements encountered, choose the one with the maximum number of keywords
            candidate_kws = [[kw.strip()  
                              for kw in re.split("[,;]", pq(kw_meta).attr("content") or "")]
                              for kw_meta in kw_metas]
            i['keywords'] = max(candidate_kws, key = lambda kws: len(kws))
        else:
            i['keywords'] = []
            
        i['keywords'] = [kw.strip() for kw in i['keywords'] if len(kw.strip()) > 0] #filter out those empty ones
        
        #the description tagm, that might be useful is keyword tag is not available
        desc_meta = (doc.find('meta[name="description"]') or
                     doc.find('meta[name="og:description"]') or#fb
                     doc.find('meta[name="twitter:description"]') or#twitter
                     doc.find('meta[itemprop="description"]')  or#g+
                     doc.find('meta[property="og:description"]')
        )
        if len(desc_meta) >= 1:
            i['description'] = desc_meta.attr("content")
        else:
            i['description'] = ""
            
        #get the language information
        lang_meta = doc.find('meta[name="language"]')
        if len(lang_meta) > 0:
            i['language'] = lang_meta.attr("content").strip()
        else:
            i['language'] = ""
            
        i['url'] = response.url
        
        return i

