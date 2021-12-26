from scrapy import Item, Field


class ArticleItem(Item):
    id = Field()
    title = Field()
    abstract = Field()
    authors = Field()
    nbrCitations = Field()
    keywords = Field()
    date = Field()
    confLocation = Field()
    source = Field()
    pass
