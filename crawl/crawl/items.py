# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field

class PageItem(Item):
    # define the fields for your item here like:
    id = Field()
    url = Field()
    content = Field()
    keywords = Field()
    description = Field()
    language = Field()
    
    
