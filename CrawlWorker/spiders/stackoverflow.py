__author__ = 'Ting'

from CrawlWorker.items import FeedItem
from CrawlWorker.base import FeedSpider, Utils


class StackOverflowSpider(FeedSpider):
    name = 'StackOverflowSpider'
    allowed_domains = ['stackoverflow.com']

    def __init__(self, op=None, **kwargs):
        FeedSpider.__init__(self, op, **kwargs)

    def get_feed_start_urls(self):
        return ['http://stackoverflow.com/questions?sort=active']

    def parse_feed_items(self, response):
        # summaries = response.xpath('//div[@class="question-summary"]')
        summaries = response.css('div.question-summary')
        items = []
        for question in summaries:
            item = FeedItem()
            item['url'] = question.css('.question-hyperlink').xpath('@href').extract()[0]
            item['updatedTime'] = question.css('.relativetime').xpath('@title').extract()[0]
            items.append(item)
        return items

    def parse_content_response(self, response):
        pass

    def parse_feed_next_url(self, response):
        next_url = None
        next_element = response.css('.page-numbers.next')
        if next_element:
            next_url = next_element.xpath('../@href').extract()[0]
            next_url = Utils.get_full_url(self.allowed_domains[0], next_url)
        return next_url
