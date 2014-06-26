# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field

class DocumentItem(Item):
    # define the fields for your item here like:
    url = Field()
    title = Field()
    keywords = Field()    
    pass
