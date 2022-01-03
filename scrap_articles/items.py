from scrapy import Item, Field


class ArticleItem(Item):
    id = Field()
    title = Field()
    abstract = Field()
    authors = Field()
    keywords = Field()
    date = Field()
    source = Field()
    universities = Field()
    countries = Field()
    type = Field()


class TopicItem(Item):
    id = Field()
    name = Field()
    usage_by_year = Field()
    total = Field()
    source = Field()
    type = Field()
