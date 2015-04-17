__author__ = 'Ting'

from CrawlWorker.spiders.stackoverflow import StackOverflowSpider


class ServerFaultSpider(StackOverflowSpider):
    name = 'ServerFaultSpider'
    allowed_domains = ['serverfault.com']

    def __init__(self, op=None, **kwargs):
        StackOverflowSpider.__init__(self, op, **kwargs)

    def get_feed_start_urls(self):
        return ['http://serverfault.com/questions']