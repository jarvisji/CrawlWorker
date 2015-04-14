# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import log
from datetime import datetime


class CrawlWorkerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    name = scrapy.Field()
    url = scrapy.Field()
    author = scrapy.Field()
    authorInfo = scrapy.Field()
    createdTime = scrapy.Field()
    content = scrapy.Field()
    isAccepted = scrapy.Field()
    voteNumber = scrapy.Field()


def serialize_datetime_str(value):
    """
    Serialize datetime string to datetime object. xpath().extract() method returns list always,
    so we first check input value is list or not.
    """
    # log.msg('serialize_datetime_str(): input value=%s, type=%s' % (value, type(value)))
    if isinstance(value, list):
        return serialize_datetime_str(value[0])
    return datetime.strptime(value, '%Y-%m-%d %H:%M:%SZ')


class QuestionSummaryItem(scrapy.Item):
    url = scrapy.Field()
    lastModifiedTime = scrapy.Field(serializer=serialize_datetime_str)