__author__ = 'Ting'

from CrawlWorker.items import FeedItem, ContentItem
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
        item = ContentItem()
        # parse question item
        name_link_node = response.css('div#question-header .question-hyperlink')
        item['name'] = name_link_node.xpath('text()').extract()[0]
        item['url'] = name_link_node.xpath('@href').extract()[0]

        author_node = response.css('.post-signature.owner')
        item['author'] = author_node.css('.user-details').xpath('a/text()').extract()[0]
        item['authorInfo'] = ''
        item['createdTime'] = author_node.css('.relativetime').xpath('@title').extract()[0]

        question_node = response.css('.question')
        item['id'] = question_node.xpath('@data-questionid').extract()[0]
        item['content'] = question_node.css('.post-text').extract()[0]
        item['isAccepted'] = None
        item['voteCount'] = question_node.css('.vote-count-post::text').extract()[0]

        # parse answer items
        answer_nodes = response.css('#answers .answer')
        answers = []
        for answer_node in answer_nodes:
            answer = ContentItem()
            answer['author'] = answer_node.css('.user-details').xpath('a/text()').extract()[0]
            answer['createdTime'] = answer_node.css('.relativetime::attr(title)').extract()[0]
            answer['content'] = answer_node.css('.post-text').extract()[0]
            answer['isAccepted'] = len(answer_node.css('.vote-accepted-on'))
            answer['voteCount'] = answer_node.css('.vote-count-post::text').extract()[0]
            answers.append(answer)
        item['answers'] = answers
        return item

    def parse_feed_next_url(self, response):
        next_url = None
        next_element = response.css('.page-numbers.next')
        if next_element:
            next_url = next_element.xpath('../@href').extract()[0]
            next_url = Utils.get_full_url(self.allowed_domains[0], next_url)
        return next_url
