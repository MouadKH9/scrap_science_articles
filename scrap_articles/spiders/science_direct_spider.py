import re

import scrapy
from scrapy_splash import SplashRequest


def get_page(keyword, current):
    return f'https://www.sciencedirect.com/search?qs={keyword}&offset={(current - 1) * 25}'


class ScienceDirectSpider(scrapy.Spider):
    name = "science_direct_spider"
    current_page = 1

    def __init__(self, keyword='', **kwargs):
        self.keyword = keyword
        self.start_urls = [get_page(keyword, self.current_page)]
        super().__init__(**kwargs)

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, self.parse, args={'wait': 1})

    def parse(self, response):
        for item in response.css(".result-item-content h2 a::attr(href)").getall():
            yield SplashRequest(response.urljoin(item), self.parse_article, args={'wait': 5})

        if self.current_page < 3:
            self.current_page += 1
            yield SplashRequest(get_page(self.keyword, self.current_page), self.parse, args={'wait': 1})

    def parse_article(self, response):
        authors = []
        for author_elem in response.css(".author-group a"):
            authors.append(f'{author_elem.css(".given-name::text").get()} {author_elem.css(".surname::text").get()}')
        keywords = []
        for kw in response.css(".keyword span::text").getall():
            keywords.append(kw)

        # This doesn't work because the page takes a lot of time to fetch this info
        citations_reg = re.search(r'\d+', response.css('#citing-articles-header .section-title::text').get())
        number_citations = int(citations_reg.group()) if citations_reg else 0

        year = response.css(".copyright-line::text").get().split(" ")[1]

        yield {
            'id': response.url.split("/")[-1],
            'title': response.css('.title-text::text').get(),
            'abstract': response.css('.abstract.author p::text').get(),
            'nbrCitations': number_citations,
            'authors': ';'.join(authors),
            'keywords': ';'.join(keywords),
            'date': f'01-01-{year}',
            'source': "science_direct"
        }
