import logging
from datetime import datetime
from urllib.parse import quote_plus

import scrapy
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from scrap_articles.items import ArticleItem


def get_page(keyword, current):
    return f'https://ieeexplore.ieee.org/search/searchresult.jsp?queryText={quote_plus(keyword)}&pageNumber={current}'


class IEEESpider(scrapy.Spider):
    name = "ieee_spider"
    current_page = 1

    def __init__(self, keyword='', **kwargs):
        self.keyword = keyword
        self.start_urls = [get_page(keyword, self.current_page)]
        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        desired_capabilities = options.to_capabilities()
        self.driver = webdriver.Chrome(executable_path="/Users/mouadk/chromedriver",
                                       desired_capabilities=desired_capabilities)
        logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
        logger.setLevel(logging.WARNING)  # or any variant from ERROR, CRITICAL or NOTSET

        super().__init__(**kwargs)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, self.parse)

    def parse(self, response):
        self.driver.get(response.url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".Dashboard-header"))
        )

        if self.current_page == 1:
            self.driver.find_element(By.CSS_SELECTOR, ".cc-compliance a").click()
            self.driver.implicitly_wait(1)

        for item in self.driver.find_elements(By.CSS_SELECTOR, "xpl-results-item h2 a"):
            yield scrapy.Request(response.urljoin(item.get_attribute("href")), self.parse_article)

        if self.current_page < 10:
            self.current_page += 1
            yield scrapy.Request(get_page(self.keyword, self.current_page), self.parse)

    def parse_article(self, response):
        self.driver.get(response.url)
        title_elem = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".document-header-title-container h1 span"))
        )

        try:
            date = self.driver.find_element(By.CSS_SELECTOR, ".doc-abstract-dateadded").text.split(": ")[-1]
        except selenium.common.exceptions.NoSuchElementException:
            date = None
        item = ArticleItem()

        item['id'] = response.url.split("/")[-2]
        item['title'] = title_elem.text
        item['abstract'] = self.driver.find_element(By.CSS_SELECTOR, ".abstract-text strong+div").text
        item['date'] = datetime.strptime(date, '%d %B %Y') if date else None
        item['source'] = "ieee"
        item['keywords'] = [self.keyword]
        WebDriverWait(self.driver, 2).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "h3#authors"))
        )
        self.driver.find_element(By.CSS_SELECTOR, "h3#authors").click()
        self.driver.implicitly_wait(.5)
        unis = [uni.text for uni in
                self.driver.find_elements(By.CSS_SELECTOR,
                                          ".authors-accordion-container .author-card .col-24-24 div+div")]
        item['universities'] = unis
        item['countries'] = [uni.split(",")[-1].strip() for uni in unis]
        item['authors'] = [author.text for author in
                           self.driver.find_elements(By.CSS_SELECTOR, ".authors-accordion-container .author-card span")]

        return item
