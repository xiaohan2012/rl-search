# Scrapy settings for corpus_collection project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'corpus_collection'

SPIDER_MODULES = ['corpus_collection.spiders']
NEWSPIDER_MODULE = 'corpus_collection.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'corpus_collection (+http://www.yourdomain.com)'
CONCURRENT_REQUESTS_PER_DOMAIN = 5
