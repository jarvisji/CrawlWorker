__author__ = 'Ting'

import scrapy
from scrapy.contrib.exporter import JsonItemExporter
from CrawlWorker.items import CrawlWorkerItem, QuestionSummaryItem
import datetime


class StackOverflowSpider(scrapy.Spider):
    name = 'StackOverflowSpider'
    allowed_domains = ['stackoverflow.com']
    start_urls = [
        'http://stackoverflow.com/questions?sort=active'
    ]

    def parse(self, response):
        """
        The lines below is a spider contract. For more info see:
        http://doc.scrapy.org/en/latest/topics/contracts.html

        @url http://www.dmoz.org/Computers/Programming/Languages/Python/Resources/
        @scrapes name
        """
        # summaries = response.xpath('//div[@class="question-summary"]')
        summaries = response.css('div.question-summary')
        items = []

        exporter = JsonItemExporter(open('stackoverflow.json', 'w'))
        for question in summaries:
            item = QuestionSummaryItem()
            item['url'] = question.css('.question-hyperlink').xpath('@href').extract()
            item['lastModifiedTime'] = question.css('.relativetime').xpath('@title').extract()
            exporter.export_item(item)

