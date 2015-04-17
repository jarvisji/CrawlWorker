# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ContentItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    id = scrapy.Field()
    name = scrapy.Field()  # Name in url, removed invalid chars for file name limitation.
    displayName = scrapy.Field()  # Original name user input.
    url = scrapy.Field()
    author = scrapy.Field()
    authorInfo = scrapy.Field()
    createdTime = scrapy.Field()
    content = scrapy.Field()
    isAccepted = scrapy.Field()
    voteCount = scrapy.Field()
    answers = scrapy.Field()


class FeedItem(scrapy.Item):
    url = scrapy.Field()
    updatedTime = scrapy.Field()