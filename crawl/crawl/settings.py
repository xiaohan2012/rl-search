# Scrapy settings for crawl project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'crawl'

SPIDER_MODULES = ['crawl.spiders']
NEWSPIDER_MODULE = 'crawl.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'crawl (+http://www.yourdomain.com)'
ITEM_PIPELINES = {
    #'crawl.pipelines.ToUnicodePipeline': 299,
    'crawl.pipelines.ToDBPipeline': 300
}

CONCURRENT_REQUESTS = 48
# CLOSESPIDER_ITEMCOUNT=200 #0.4 million urls to collect

EXTENSIONS={
    #'crawl.middlewares.DownloadTimer': 0,
    # 'crawl.stat2email.StatsToEmail': 900
}

#for the emailing stuff
MAILING_ADDRESS=["xiaohan2012@gmail.com"]
#"mohammad.a.hoque@helsinki.fi"
