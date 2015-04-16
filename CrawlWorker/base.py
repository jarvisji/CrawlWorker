__author__ = 'Ting'

import os
import json
from datetime import datetime, date

from scrapy import Spider
from scrapy.settings import Settings


class FeedSpider(Spider):
    """
        Defined main feed and scrape process, each site spider should extends this class
        There are two steps to crawl items:
        1. FEED summary information of recent active questions, compare their time to our saved the last crawled time,
            in this way, we get incremental list to crawl.
        2. CONTENT question content according to result of step 1.
    """
    name = None
    allowed_domains = []
    start_urls = []
    op = None  # 'content' to perform scrape item content, otherwise perform update feed list.
    MAX_FEED_LIMIT = 100

    def __init__(self, op, **kwargs):
        self.op = op
        self.reach_limit = False
        self.last_feed_updated_time = None
        FeedSpider.check_output_path(self.name)
        # TODO: why print log in __int__ doesn't work?
        # self.log('Initializing spider...')
        Spider.__init__(self, self.name, **kwargs)

    def start_requests(self):
        self.log('start request...')
        self.log('spider name: %s, allowed_domains: %s, op: %s' % (self.name, self.allowed_domains, self.op))
        self.set_pipeline_class()  # doesn't work currently.
        if self.op == 'content':
            self.start_urls = self.get_content_start_urls()
        else:
            self.last_feed_updated_time = self.get_last_feed_updated_time()
            self.start_urls = self.get_feed_start_urls()
        self.log('start_urls: %s' % self.start_urls)
        return Spider.start_requests(self)
        # return [scrapy.FormRequest("http://www.example.com/login",
        # formdata={'user': 'john', 'pass': 'secret'},
        # callback=self.logged_in)]

    def parse(self, response):
        self.log('parsing response...')
        if self.op == 'content':
            yield self.parse_content_response(response)
        else:
            items = self.parse_feed_items(response)
            self.log('feed items count: %i' % len(items))
            for item in items:
                if self.is_new_feed_item(item):
                    if not self.reach_limit:
                        yield item
                    else:
                        self.log('reach max limit %i, stop parse process.' % self.MAX_FEED_LIMIT)
                        return
                else:
                    self.log('parsed all new feed items, end parse process.')
                    return

            url = self.parse_feed_next_url(response)
            self.log('feed next url: %s' % url)
            if url:
                yield self.make_requests_from_url(url)

    def parse_feed_items(self, response):
        """
        Most sites have a feed/activity page to list latest item updates. We check it to recognize those questions
        we need to update.
        Each spider should implement this method, to get a list of updated questions after last crawl.
        As job list for content/feed question content.
        :return item or next page request
        """
        raise NotImplementedError

    def parse_feed_next_url(self, response):
        """
        find 'next' button on page, parse it's url and fetch data.
        Sub-class should override this method
        """
        raise NotImplementedError

    def parse_content_response(self, response):
        """content item information from detail page.
        :return item
        """
        raise NotImplementedError

    def get_feed_start_urls(self):
        """Set spider start_urls which Scrapy needs
        Each sub-class should implement this method"""
        raise NotImplementedError

    def get_content_start_urls(self):
        raise NotImplementedError

    def set_pipeline_class(self):
        """  TODO: try to set pipeline at runtime, but doesn't work currently."""
        # self.settings.set('ITEM_PIPELINES', 'CrawlWorker.pipelines.FeedWriterPipeline', 200)
        # self.log('setting up item pipelines: %s' % self.settings.get('ITEM_PIPELINES'))

    def is_new_feed_item(self, feed_item):
        """last_feed_updated_time is use to compare to new feed/activity items,
        any item which updated after last_feed_updated_time will be save to update feed list.
        By default, the time is the first line of last feed output file."""
        return Utils.str2datetime(feed_item['updatedTime']) > self.last_feed_updated_time

    def check_max_limit(self, count):
        """For test/demo purpose, we don't want crawl too many data. so we set MAX_FEED_LIMIT.
         pipeline will call this method to check if reach the limit while save data."""
        self.reach_limit = count >= self.MAX_FEED_LIMIT

    def get_last_feed_updated_time(self):
        """Get last_feed_updated_time from last feed output file. This method should only run once."""
        last_feed_updated_time = datetime.fromtimestamp(0)
        output_dir = FeedSpider.get_output_dir_path(self.name)
        files = os.listdir(output_dir)
        files.reverse()
        for filename in files:
            if filename.startswith(self.name + '.feeds.'):
                full_filename = output_dir + filename
                if os.path.getsize(full_filename):
                    self.log('Opening last feed file: %s' % full_filename)
                    last_feed_file = open(full_filename, 'r')
                    line = last_feed_file.readline()
                    last_feed_file.close()
                    try:
                        last_feed_item = json.loads(line)
                    except ValueError:
                        self.log('file first line is not valid json string: %s, trying next file.' % line)
                        continue
                    last_feed_updated_time = Utils.str2datetime(last_feed_item['updatedTime'])
                    break
        self.log('get_last_feed_updated_time(): %s' % last_feed_updated_time)
        return last_feed_updated_time


    @staticmethod
    def get_feed_output_filename(spider_name):
        filename = spider_name + '.feeds.' + datetime.now().strftime('%Y%m%d%H%M%S') + '.txt'
        return FeedSpider.get_feed_output_file_path(spider_name, filename)

    @staticmethod
    def get_output_dir_path(spider_name):
        """Output path is set to './output/<%spiderName%>'."""
        return os.curdir + os.sep + 'output' + os.sep + spider_name + os.sep

    @staticmethod
    def get_feed_output_file_path(spider_name, filename):
        return FeedSpider.get_output_dir_path(spider_name) + filename

    @staticmethod
    def get_content_output_filename(item_id, item_name, spider_name):
        if (not item_id) or (not item_name):
            raise RuntimeError('item_id and item_name parameters cannot be blank.')
        filename = spider_name + '.' + item_id + '.' + item_name + '.txt'
        return FeedSpider.get_feed_output_file_path(spider_name, filename)

    @staticmethod
    def check_output_path(spider_name):
        output_path = FeedSpider.get_output_dir_path(spider_name)
        if not os.path.isdir(output_path):
            os.mkdir(output_path)


class Utils(object):
    @staticmethod
    def get_full_url(domain_name, url):
        if url.find('://') > 0:
            # already is full url
            return url
        if url.startswith('/'):
            # remove first '/' if has
            url = url[1:]
        if url.startswith(domain_name):
            return 'http://' + url
        else:
            return 'http://' + domain_name + '/' + url

    @staticmethod
    def is_file_empty(file_name):
        """if file_name is not specified, or file not exists, or file size is 0, it's empty"""
        if not file_name:
            return True
        if (not os.path.exists(file_name)) or os.path.getsize(file_name) == 0:
            return True
        return False

    @staticmethod
    def str2datetime(value):
        """
            Serialize datetime string to datetime object.
            xpath().extract() method returns list always, so we first check input value is list or not.
        """
        # log.msg('serialize_datetime_str(): input value=%s, type=%s' % (value, type(value)))
        if isinstance(value, list):
            value = value[0]
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%SZ')

    @staticmethod
    def datetime2str(dt):
        return dt.strftime('%Y-%m-%d %H:%M:%SZ')