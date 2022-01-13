import pymongo
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class ScrapArticlesPipeline:
    def open_spider(self, spider):
        self.client = pymongo.MongoClient('localhost', 27017)
        self.db = self.client.get_database('articles_')

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if "abstract" not in adapter.field_names():
            self.db.get_collection('topics').insert_one(adapter.asdict())
        else:
            if not adapter['title']:
                raise DropItem(f"No title given for {adapter['id']}")
            adapter['countries'] = list(dict.fromkeys((adapter['countries'])))
            self.db.get_collection(f"articles").insert_one(adapter.asdict())
        return item
