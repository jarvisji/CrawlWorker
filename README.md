# ScrapyCrawler
This is a demo of using Scrapy to crawling web pages content.


## Running the demo
To run this demo, please make sure [Python 2.7.6](https://www.python.org/) and [Scrapy 0.24](http://scrapy.org/) already installed correctly. This demo is tested base on the versions.

1. Clone the source codes.
2. Open command window, change path to where ScrapyCrawler is located, the same path to this README file.
3. Run `scrapy crawl StackOverflowSpider` or `scrapy crawl StackOverflowSpider -a op=feed` first. This step will crawl feed data from [stackoverflow.com](http://stackoverflow.com), and generate file: `./output/StackOverflowSpider/StackOverflowSpider.feeds.<datetime>.txt`
4. Run `scrapy crawl StackOverflowSpider -a op=content` after step 3 finished. This step will crawl each questions to individual file in `./output/StackOverflowSpider/contents` path.
5. Repeat 3-4 to crawl more and the newest questions.
Note, in step 4, will generate a file 'StackOverflowSpider.content.history.txt'. It records which feed files are crawled and they will not be tried again even re-run step 4. To get more data, you need run step 3, or delete some records in this file.  

Replace 'StackOverflowSpider' to 'ServerFaultSpider' in upon commands, will crawl data from [serverfault.com](http://serverfault.com)


## Implementation
For easier to demo, current implementation doesn't need any Database, all crawled data will be saved in local files.

[stackoverflow.com](http://stackoverflow.com) such website has a feed page, please refer to [http://stackoverflow.com/questions?sort=active](http://stackoverflow.com/questions?sort=active).
On this page, all questions are displayed in descending order of last activity time, for example, user edit the post, someone reply the question, will push the question to the top of list on this page.
So what we need to do is check the new data on this page, to crawl the questions from last updated to earlier.

As you can see upon, the crawling process has two steps, the first step is get new question feeds, the second step is get content base on the feeds.


## Statement
This demo and the chosen 'stackoverflow.com' are all for study purpose, please do not run huge crawling or other harmful operations on public sites.
  