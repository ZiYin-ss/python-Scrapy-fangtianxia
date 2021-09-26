# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exporters import JsonLinesItemExporter


class SoufangwangPipeline:
    def __init__(self):
        self.house_fp = open('huose.json','wb')
        self.house_exporter = JsonLinesItemExporter(self.house_fp,ensure_ascii=False)

    def process_item(self, item, spider):
        self.house_exporter.export_item(item)
        return item

    def close_spidef(self,spider):
        self.house_fp.close()