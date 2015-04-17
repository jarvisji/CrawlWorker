# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import os

from scrapy.contrib.exporter import JsonLinesItemExporter, JsonItemExporter
from scrapy.exceptions import DropItem
from scrapy import log

from CrawlWorker.items import FeedItem, ContentItem
from CrawlWorker.base import FeedSpider


class FeedWriterPipeline(object):
    def __init__(self):
        log.msg('FeedWriterPipeline.__init__()')
        self.file = None
        self.item_exporter = None
        self.count = 0

    def open_spider(self, spider):
        if FeedSpider.is_feed_op(spider):
            spider.make_sure_path_exists(spider.get_output_dir_path())
            file_name = spider.get_feed_output_file_path()
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


class ContentWriterPipeline(object):
    def __init__(self):
        log.msg('ContentWriterPipeline.__init__()')
        self.file = None
        self.item_exporter = None
        self.count = 0

    def process_item(self, item, spider):
        if FeedSpider.is_content_op(spider) and isinstance(item, ContentItem):
            spider.make_sure_path_exists(spider.get_content_output_dir_path())
            file_path = spider.get_content_output_file_path(item['id'], item['name'].replace(' ', '-'))
            is_exist = os.path.exists(file_path)
            self.file = open(file_path, 'w')
            if is_exist:
                # if file already exists, clean it and write new content.
                self.file.seek(0)
                self.file.truncate()
            self.item_exporter = JsonItemExporter(self.file, indent=4)
            self.item_exporter.export_item(item)
            self.file.close()
            log.msg('ContentWriterPipeline, saved content file %s successful.' % file_path)
            raise DropItem('Save item success')
        else:
            return item
