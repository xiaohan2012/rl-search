from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher
from scrapy.mail import MailSender

class StatsToEmail(object):
    def __init__(self, stats, settings):
        self.stats = stats
        self.settings = settings
        dispatcher.connect(self.on_spider_closed, signal=signals.stats_spider_closed)
        
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.stats, crawler.settings)
        
    def get_email_body(self, spider):
        import pprint
        return """Just finished crawling from %s to %s.
        
Spider statistics are:
        
%s""" %(str(spider.offset),
        ('the end' 
         if not spider.limit 
         else str(spider.offset + spider.limit)),
        pprint.pformat(self.stats.get_stats()),)
        
    def on_spider_closed(self, spider, reason):
        import socket
        hostname = socket.gethostname()
        print "sending email to: %s" %(repr(self.settings["MAILING_ADDRESS"]))
        
        mailer = MailSender()
        mailer.send(to=self.settings["MAILING_ADDRESS"],
                    subject="%s finished crawling" %(hostname), 
                    body= self.get_email_body(spider))               
