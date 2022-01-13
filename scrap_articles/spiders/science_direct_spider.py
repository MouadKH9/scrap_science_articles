import datetime
import scrapy
from scrapy_splash import SplashRequest
from urllib.parse import quote_plus
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from scrap_articles.items import ArticleItem, TopicItem


def get_page(keyword, current):
    return f'https://www.sciencedirect.com/search?qs={quote_plus(keyword)}&offset={(current - 1) * 25}'


class ScienceDirectSpider(scrapy.Spider):
    name = "science_direct_spider"
    current_page = 1

    def __init__(self, keyword='', **kwargs):
        self.keyword = keyword
        self.start_urls = [get_page(keyword, self.current_page)]
        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        desired_capabilities = options.to_capabilities()
        self.driver = webdriver.Chrome(executable_path="/Users/mouadk/chromedriver",
                                       desired_capabilities=desired_capabilities)
        super().__init__(**kwargs)

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, self.parse, args={'wait': 3})

    def parse(self, response):
        if self.current_page == 1:
            self.driver.get(response.url)
            topic = TopicItem()
            topic['id'] = self.keyword.lower().replace(" ", "_")
            topic['name'] = self.keyword
            topic['total'] = int(response.css(".search-body-results-text::text").get().split(" ")[0].replace(",", ""))
            show_filters = ".button-link[aria-label='Show more years filters']"
            show_filters_element = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, show_filters))
            )
            show_filters_element.click()
            self.driver.implicitly_wait(.5)
            years_elems = self.driver.find_elements(By.CSS_SELECTOR, "fieldset > ol > li > div > label")
            years = []
            for year in years_elems:
                for_attr = year.get_attribute('for')
                if "years-" not in for_attr:
                    continue
                value = \
                    year.find_element(By.CSS_SELECTOR, ".checkbox-label-value").text.split(" ")[1].split("(")[-1].split(
                        ")")[0]
                years.append({
                    "year": for_attr.split("-")[-1],
                    "value": value
                })
            topic['usage_by_year'] = years
            yield topic

        for item in response.css(".result-item-content h2 a::attr(href)").getall():
            yield SplashRequest(response.urljoin(item), self.parse_article, args={'wait': 3})

        if self.current_page < 20:
            self.current_page += 1
            yield SplashRequest(get_page(self.keyword, self.current_page), self.parse, args={'wait': 3})

    def parse_article(self, response):
        authors = []
        for author_elem in response.css(".author-group a"):
            authors.append(f'{author_elem.css(".given-name::text").get()} {author_elem.css(".surname::text").get()}')
        keywords = []
        for kw in response.css(".keyword span::text").getall():
            keywords.append(kw.strip())

        if self.keyword not in keywords:
            keywords.append(self.keyword)

        year = response.css(".copyright-line::text").get().split(" ")[1]
        if year == "©":
            year = response.css(".copyright-line::text").get().split(" ")[2]
        item = ArticleItem()

        item['id'] = response.url.split("/")[-1]
        item['title'] = response.css('.title-text::text').get()
        item['abstract'] = response.css('.abstract.author p::text').get()
        item['authors'] = authors
        item['keywords'] = keywords
        try:
            item['date'] = datetime.datetime(int(year), 1, 1)
        except:
            item['date'] = None
        item['source'] = "science_direct"

        self.driver.get(response.url)
        self.driver.implicitly_wait(2)
        citings_elems = WebDriverWait(self.driver, 10).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#citing-articles-header h2"), "(")
        )
        self.driver.find_element(By.ID, 'show-more-btn').click()
        self.driver.implicitly_wait(1)

        affiliations = self.driver.find_elements(By.CSS_SELECTOR, ".affiliation dd")
        unis = [aff.text for aff in affiliations]
        item['citations'] = int(
            self.driver.find_element(By.CSS_SELECTOR, "#citing-articles-header h2").text.split("(")[-1].split(")")[0])
        item['universities'] = unis
        item['countries'] = [uni.split(",")[-1].strip() for uni in unis]

        return item
