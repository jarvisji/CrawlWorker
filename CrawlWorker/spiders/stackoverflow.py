__author__ = 'Ting'

import scrapy
from CrawlWorker.items import CrawlWorkerItem

class StackOverflowSpider(scrapy.Spider):
    name = "StackOverflowSpider"
    allowed_domains = ["http://stackoverflow.com/"]
    start_urls = [
        "http://stackoverflow.com/questions?sort=newest"
    ]

    def parse(self, response):
        """
        The lines below is a spider contract. For more info see:
        http://doc.scrapy.org/en/latest/topics/contracts.html

        @url http://www.dmoz.org/Computers/Programming/Languages/Python/Resources/
        @scrapes name
        """
        selector = scrapy.Selector(response)
        questions = selector.xpath('//div[@class="question-summary"]')
        items = []

        for question in questions:
            item = CrawlWorkerItem()
            item['url'] = question.xpath('div[@class="summary"]/h3/a/text()').extract()
            item['name'] = question.xpath('div[@class="summary"]/h3/a/@href').extract()

            yield item

            # items.append(item)

        # return items