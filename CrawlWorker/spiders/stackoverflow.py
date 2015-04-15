__author__ = 'Ting'

from scrapy import Spider, log
from scrapy.contrib.exporter import JsonLinesItemExporter
from CrawlWorker.items import CrawlWorkerItem, QuestionSummaryItem
from datetime import datetime, date
import os


class StackOverflowSpider(Spider):
    name = 'StackOverflowSpider'
    allowed_domains = ['stackoverflow.com']
    start_urls = [
        'http://stackoverflow.com/questions?sort=active'
    ]

    def __init__(self, name=None, **kwargs):
        Spider.__init__(self, name=None, **kwargs)
        self.check_output_path()

    def parse(self, response):
        """
        There are two steps to crawl questions:
        1. Get summary information of recent active questions, compare their time to our saved the last crawled time,
           in this way, we get incremental list to crawl.
        2. Crawl question content according to result of step 1.
        """
        # summaries = response.xpath('//div[@class="question-summary"]')
        summaries = response.css('div.question-summary')
        items = []

        last_crawled_datetime = self.get_last_crawled_datetime()
        current_queue_file = open(self.get_output_filename(), 'ab+')
        exporter = JsonLinesItemExporter(current_queue_file)
        new_relative_time = self.str2datetime(summaries[0].css('.relativetime').xpath('@title').extract())
        new_count = 0
        for question in summaries:
            question_relative_time = self.str2datetime(
                question.css('.relativetime').xpath('@title').extract())
            log.msg('parsing question index %i, question_relative_time=%s' % (new_count, question_relative_time))
            if question_relative_time.__le__(last_crawled_datetime):
                log.msg('no new updates, ending...')
                break
            item = QuestionSummaryItem()
            item['url'] = question.css('.question-hyperlink').xpath('@href').extract()
            item['lastModifiedTime'] = question_relative_time
            exporter.export_item(item)
            new_count += 1
        self.finish_export(new_relative_time, new_count, current_queue_file)

    def finish_export(self, new_relative_time, new_count, current_queue_file):
        if new_count > 0:
            current_queue_file.write(
                '%sCrawled finished at %s, the latest active time of question is:%s' % (
                    os.linesep, datetime.now(), os.linesep))
            current_queue_file.write(self.datetime2str(new_relative_time) + os.linesep)
            current_queue_file.write('=' * 80 + os.linesep)
            current_queue_file.close()
        log.msg('Crawled %i new questions.' % new_count)

    def check_output_path(self):
        output_path = self.get_output_path()
        if not os.path.isdir(output_path):
            os.mkdir(output_path)

    @staticmethod
    def get_output_path():
        return os.curdir + os.sep + 'output'

    def get_file_path(self, filename):
        return self.get_output_path() + os.sep + filename

    def get_output_filename(self):
        filename = self.name + '.queue.' + date.today().strftime('%Y%m%d') + '.txt'
        return self.get_file_path(filename)

    def get_latest_output_filename(self):
        """Get file list in output path, order them and get the last one"""
        files = os.listdir(self.get_output_path())
        files.reverse()
        for filename in files:
            file_path = self.get_file_path(filename)
            if filename.startswith(self.name + '.queue.') and os.path.getsize(file_path) > 0:
                return file_path

    @staticmethod
    def is_file_empty(file_name):
        """if file_name is not specified, or file not exists, or file size is 0, it's empty"""
        if not file_name:
            return True
        if (not os.path.exists(file_name)) or os.path.getsize(file_name) == 0:
            return True
        return False

    def get_last_crawled_datetime(self):
        """In output file, we recorded datetime of the last question we crawled, here we get it back"""
        queue_filename = self.get_output_filename()
        if self.is_file_empty(queue_filename):
            queue_filename = self.get_latest_output_filename()
            log.msg('Today\'s output file does not exist: %s, try to open latest one: %s' % (
                self.get_output_filename(), queue_filename))

        # the last line is 80 '=', the line before last line is datetime, e.g. '2015-04-14 10:10:52Z',
        # length is 20, so seek to position of last 120 bytes.
        last_crawled_datetime = datetime.fromtimestamp(0)
        if not self.is_file_empty(queue_filename):
            output_file_size = os.path.getsize(queue_filename)
            if output_file_size > 120:
                queue_file = open(queue_filename, 'r')
                queue_file.seek(-120, os.SEEK_END)
                last_line = queue_file.readlines()[-2].decode()
                last_crawled_datetime = self.str2datetime(last_line.strip())
                queue_file.close()
        log.msg('Last crawled datetime: %s' % last_crawled_datetime)
        return last_crawled_datetime

    def str2datetime(self, value):
        """
        Serialize datetime string to datetime object.
        xpath().extract() method returns list always, so we first check input value is list or not.
        """
        # log.msg('serialize_datetime_str(): input value=%s, type=%s' % (value, type(value)))
        if isinstance(value, list):
            return self.str2datetime(value[0])
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%SZ')

    @staticmethod
    def datetime2str(dt):
        return dt.strftime('%Y-%m-%d %H:%M:%SZ')

