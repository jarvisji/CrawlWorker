__author__ = 'Ting'

import os
import json
from datetime import datetime

from scrapy import Spider, log


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
    MAX_FEED_LIMIT = 1000

    def __init__(self, op, **kwargs):
        self.op = op
        self.reach_limit = False
        self.last_feed_updated_time = None
        self.make_sure_path_exists(self.get_output_dir_path())
        # TODO: why print log in __int__ doesn't work?
        # self.log('Initializing spider...')
        Spider.__init__(self, self.name, **kwargs)

    def start_requests(self):
        self.log('start request...')
        self.log('spider name: %s, allowed_domains: %s, op: %s' % (self.name, self.allowed_domains, self.op))
        self.set_pipeline_class()  # doesn't work currently.
        if self.is_content_op(self):
            self.start_urls = self.get_content_start_urls()
        elif self.is_feed_op(self):
            self.last_feed_updated_time = self.get_last_feed_updated_time()
            self.start_urls = self.get_feed_start_urls()
        else:
            self.log('*' * 60, log.ERROR)
            self.log('*** Value of "op" parameter is not supported: %s ' % self.op, log.ERROR)
            self.log('*' * 60, log.ERROR)
        self.log('start_urls: %s' % self.start_urls)
        return Spider.start_requests(self)
        # return [scrapy.FormRequest("http://www.example.com/login",
        # formdata={'user': 'john', 'pass': 'secret'},
        # callback=self.logged_in)]

    def parse(self, response):
        self.log('parsing %s response...' % self.op)
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

    def get_feed_start_urls(self):
        """Set spider start_urls which Scrapy needs
        Each sub-class should implement this method"""
        raise NotImplementedError

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

    def get_content_start_urls(self):
        """Read content urls from in feed output files, and use 'content.history.txt' to record what we have done."""
        self.log('get_content_start_urls()')
        history_file_name = self.name + '.content.history.txt'
        history_file_path = self.get_output_dir_path() + history_file_name
        self.log('>> opening history file to get last crawled feed filename: %s' % history_file_path)

        # Get last checked feed file name
        line_separator = '-'
        if os.path.exists(history_file_path) and os.path.getsize(history_file_path) > 0:
            history_file = open(history_file_path, 'rb')
            history_file.seek(-500, os.SEEK_END)
            last_line = history_file.readlines()[-1].decode()
            history_file.close()
            line_content = last_line.split(line_separator)  # line content should be: <%datetime%>:<%feed_file_name%>
            last_feed_filename = line_content[1].strip() if len(line_content) > 1 else line_content[0].strip()
        else:
            last_feed_filename = None
        self.log('>> last_feed_filename: %s' % last_feed_filename)

        # find new feed files
        dir_file_names = os.listdir(self.get_output_dir_path())
        feed_file_names = []
        for dir_file_name in dir_file_names:
            if dir_file_name.startswith(self.get_feed_output_file_prefix()):
                if (last_feed_filename is None) or cmp(last_feed_filename, dir_file_name) == -1:
                    feed_file_names.append(dir_file_name)
        feed_file_names.sort()
        self.log('>> new feed files: %i' % len(feed_file_names))

        # Get feed files content
        content_urls = []
        history_file = open(history_file_path, 'a')
        for feed_file_name in feed_file_names:
            feed_file_path = self.get_output_dir_path() + feed_file_name
            self.log('>> opening feed file: %s' % feed_file_path)
            feed_file = open(feed_file_path, 'r')
            lines = feed_file.readlines()
            feed_file.close()
            count = 0
            for line in lines:
                try:
                    feed_item = json.loads(line)
                    content_urls.append(Utils.get_full_url(self.allowed_domains[0], feed_item['url']))
                    count += 1
                except ValueError:
                    self.log('>> ignore line: %s' % line.strip())
            self.log('>> %i urls append.' % count)
            # Update last feed file history
            history_file.write('%s  %s  %s%s' % (datetime.now().ctime(), line_separator, feed_file_name, os.linesep))
        history_file.close()
        return content_urls

    def parse_content_response(self, response):
        """content item information from detail page.
        :return item
        """
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
        self.reach_limit = self.MAX_FEED_LIMIT != 0 and count >= self.MAX_FEED_LIMIT

    def get_last_feed_updated_time(self):
        """Get last_feed_updated_time from last feed output file. This method should only run once."""
        last_feed_updated_time = datetime.fromtimestamp(0)
        output_dir = self.get_output_dir_path()
        files = os.listdir(output_dir)
        files.reverse()
        for filename in files:
            if filename.startswith(self.get_feed_output_file_prefix()):
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

    def get_feed_output_file_prefix(self):
        return self.name + '.feeds.'

    def get_feed_output_file_path(self):
        filename = self.get_feed_output_file_prefix() + datetime.now().strftime('%Y%m%d%H%M%S') + '.txt'
        return self.get_output_dir_path() + filename

    def get_content_output_dir_path(self):
        return self.get_output_dir_path() + "contents" + os.sep

    def get_content_output_file_path(self, item_id, item_name):
        if (not item_id) or (not item_name):
            raise RuntimeError('item_id and item_name parameters cannot be blank.')
        filename = self.name + '.' + item_id + '.' + item_name + '.txt'
        return self.get_content_output_dir_path() + filename

    def get_output_dir_path(self):
        """Output path is set to './output/<%spiderName%>'."""
        return os.curdir + os.sep + 'output' + os.sep + self.name + os.sep

    @staticmethod
    def make_sure_path_exists(path):
        if not os.path.isdir(path):
            os.makedirs(path)

    @staticmethod
    def is_feed_op(spider):
        return (spider.op is None) or (spider.op == 'feed')

    @staticmethod
    def is_content_op(spider):
        return spider.op == 'content'


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