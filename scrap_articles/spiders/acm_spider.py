import scrapy
from scrapy_splash import SplashRequest
from urllib.parse import quote_plus
from datetime import datetime

from scrap_articles.items import ArticleItem
from scrap_articles.spiders.utils import check_country


def get_page(keyword, current):
    return f'https://dl.acm.org/action/doSearch?AllField={quote_plus(keyword)}&pageSize={50}&startPage={current}'


class ACMSpider(scrapy.Spider):
    name = "acm_spider"
    current_page = 1

    def __init__(self, keyword='', **kwargs):
        self.keyword = keyword
        self.start_urls = [get_page(keyword, self.current_page)]
        super().__init__(**kwargs)

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, self.parse, args={'wait': 3})

    def parse(self, response):
        for item in response.css(".issue-item__title a::attr(href)").getall():
            yield SplashRequest(response.urljoin(item), self.parse_article, args={'wait': 3})

        if self.current_page < 3:
            self.current_page += 1
            yield SplashRequest(get_page(self.keyword, self.current_page), self.parse, args={'wait': 3})

    def parse_article(self, response):
        unis = response.css(".author-info__body p::text").getall()
        countries = [uni.split(",")[-1].strip() for uni in filter(lambda x: "," in x, unis)]
        countries = filter(lambda x: check_country(x), countries)
        date = response.css(".CitationCoverDate::text").get()
        item = ArticleItem()

        item['id'] = response.url.split("/")[-1]
        item['title'] = response.css('.citation__title::text').get()
        item['abstract'] = response.css('.abstractSection p::text').get()
        item['authors'] = ';'.join(response.css(".loa__author-name span::text").getall())
        item['countries'] = ';'.join(countries)
        item['universities'] = ';'.join(unis)
        item['keywords'] = [self.keyword]
        item['date'] = datetime.strptime(date, '%d %B %Y') if date else None
        item['source'] = "acm"

        return item
