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
        self.file = open(self.get_output_filename(), 'ab+')

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

        exporter = JsonLinesItemExporter(self.file)
        last_crawled_datetime = self.get_last_crawled_datetime()
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
        self.finish_export(new_relative_time, new_count)

    def finish_export(self, new_relative_time, new_count):
        if new_count > 0:
            self.file.write(
                '\nCrawled finished at %s, the latest active time of question is:\n' % datetime.now())
            self.file.write(self.datetime2str(new_relative_time) + '\n')
            self.file.write('=' * 80 + '\n')
            self.file.close()
        log.msg('Crawled %i new questions.' % new_count)

    def get_output_filename(self):
        return self.name + '.' + date.today().strftime('%Y%m%d') + '.out'

    def get_last_crawled_datetime(self):
        """In output file, we recorded datetime of the last question we crawled, here we get it back"""

        # the last line is 80 '=', the line before last line is datetime, e.g. '2015-04-14 10:10:52Z',
        # length is 20, so seek to position of last 120 bytes.
        output_file_size = os.path.getsize(self.get_output_filename())
        if output_file_size > 120:
            self.file.seek(-120, os.SEEK_END)
            last_line = self.file.readlines()[-2].decode()
            last_crawled_datetime = self.str2datetime(last_line.strip())
            # seek back to start, for later reading.
            self.file.seek(0, os.SEEK_SET)
        else:
            last_crawled_datetime = datetime.fromtimestamp(0)
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

    def datetime2str(self, dt):
        return dt.strftime('%Y-%m-%d %H:%M:%SZ')

