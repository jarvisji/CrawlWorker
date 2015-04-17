# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import os

from scrapy.contrib.exporter import JsonLinesItemExporter
from scrapy.exceptions import DropItem
from scrapy import log

from CrawlWorker.items import FeedItem
from CrawlWorker.base import FeedSpider


class FeedWriterPipeline(object):
    def __init__(self):
        log.msg('FeedWriterPipeline.__init__()')
        self.file = None
        self.item_exporter = None
        self.count = 0

    def open_spider(self, spider):
        if FeedSpider.is_feed_op(spider):
            spider_name = spider.name
            FeedSpider.check_output_path(spider_name)
            file_name = FeedSpider.get_feed_output_filename(spider_name)
            self.file = open(file_name, 'a')
            self.item_exporter = JsonLinesItemExporter(self.file)
            log.msg('FeedWriterPipeline, opened file %s to append.' % file_name)

    def process_item(self, item, spider):
        if FeedSpider.is_feed_op(spider) and isinstance(item, FeedItem):
            self.item_exporter.export_item(item)
            self.count += 1
            spider.check_max_limit(self.count)
            raise DropItem('Save item success')
        else:
            return item

    def close_spider(self, spider):
        if FeedSpider.is_feed_op(spider):
            self.file.write('Parsed %i feed items.%s' % (self.count, os.linesep))
            self.file.close()
            log.msg('closed file, appended %i items.' % self.count)