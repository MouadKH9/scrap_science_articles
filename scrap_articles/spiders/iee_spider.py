import scrapy
from scrapy_splash import SplashRequest


def get_page(keyword, current):
    return f'https://ieeexplore.ieee.org/search/searchresult.jsp?queryText={keyword}&pageNumber={current}'


class IEEESpider(scrapy.Spider):
    name = "ieee_spider"
    current_page = 1

    def __init__(self, keyword='', **kwargs):
        self.keyword = keyword
        self.start_urls = [get_page(keyword, self.current_page)]
        super().__init__(**kwargs)

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, self.parse, args={'wait': 2})

    def parse(self, response):
        for item in response.css("xpl-results-item h2 a::attr(href)").getall():
            yield SplashRequest(response.urljoin(item), self.parse_article, args={'wait': 5})
            return

        if self.current_page < 3:
            self.current_page += 1
            yield SplashRequest(get_page(self.keyword, self.current_page), self.parse, args={'wait': 2})

    def parse_article(self, response):
        yield {
            'title': response.css('.document-title span::text').get(),
        }
