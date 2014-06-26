from pyquery import PyQuery as pq

from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from corpus_collection.items import DocumentItem

class JohnSpider(CrawlSpider):
    name = 'john'
    allowed_domains = ['johndcook.com']
    start_urls = ['http://www.johndcook.com/blog']

    rules = (
        Rule(SgmlLinkExtractor(allow=r'/blog/\d{4}/\d{2}/\d{2}/*'), callback='parse_item', follow=True),
    )

    def parse_item(self, response):
        doc = pq(response.body)
        i = DocumentItem()
        i['url'] = response.url
        i['title'] = doc.find('#main .entry-title').text().strip()
        i['keywords'] = map(lambda dom: pq(dom).text().strip().lower(),
                            doc.find('#main .tagcloud a'))
        
        return i
