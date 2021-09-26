import scrapy
import re
from soufangwang.items import SoufangwangItem, EsfHouseItem
from scrapy_redis.spiders import RedisSpider
# 要是Crawl模板的的话 改为分布式 就是用RedisCrawlSpider

class SoufangSpider(RedisSpider):
    name = 'soufang'
    allowed_domains = ['fang.com']
    # start_urls = ['https://www.fang.com/SoufunFamily.htm']
    redis_key = "soufang:start_url"
    # 指明爬虫从Redis那个key开始读取

    # 先爬取首页的城市的url 拼接为新房和二手房的URL
    def parse(self, response):
        trs = response.xpath('//div[@class="outCont"]//tr')[:-1]
        province = None
        for tr in trs:
            tds = tr.xpath('.//td[not(@class)]')
            province_td = tds[0]
            province_textt = province_td.xpath(".//text()").get()
            province_text = re.sub(r"\s", "", province_textt)
            if province_text:
                province = province_text
            city_td = tds[1]
            city_links = city_td.xpath(".//a")
            for city_link in city_links:
                city = city_link.xpath(".//text()").get()
                city_url = city_link.xpath(".//@href").get()
                # 构建新房的Url链接
                b = city_url.split('//')
                new_house = b[0] + '//' + 'newhouse.' + b[1] + 'house/s/'
                # 构建二手房的链接
                c = city_url.split('.')
                old_house = c[0] + '.esf.' + c[1] + '.' + c[2]
                yield scrapy.Request(url=new_house,callback=self.parse_newhouse,meta={"info":(province,city)})
                yield scrapy.Request(url=old_house, callback=self.parse_oldhouse, meta={"info": (province, city)})

    # 新房的URL解析数据
    def parse_newhouse(self, response):
        province, city = response.meta.get('info')
        lis = response.xpath('//div[contains(@class,"nl_con")]/ul/li')
        for li in lis:
            # 名字的处理
            name = li.xpath('.//div[@class="nlcd_name"]/a/text()').get().strip()
            # 金额的处理
            pricee = li.xpath('.//div[@class="nhouse_price"]//text()').getall()
            price = ''.join(list(map(lambda x: re.sub("\s", "", x), pricee)))
            # 就是几居室 rooms的处理 ，有多个a标签的数据
            house_types = li.xpath('.//div[contains(@class,"house_type")]/a/text()').getall()
            rooms = ','.join(list(map(lambda x: re.sub("\s", "", x), house_types)))
            # 这个卖房的url
            origin_url = response.url
            # 面积的处理 因为有多行文字 所以说用getall，直接转换为字符串
            house_type = "".join(li.xpath('.//div[contains(@class,"house_type")]/text()').getall())
            area = re.sub("\s|/|—", "", house_type)
            # 位置的处理
            addre = li.xpath('.//div[@class="address"]/a/text()').getall()
            address = ''.join(list(map(lambda x: re.sub("\s", "", x), addre)))
            # 给他放到item里面
            item = SoufangwangItem(
                province=province,
                city=city,
                name=name,
                rooms=rooms,
                origin_url=origin_url,
                area=area,
                address=address,
                price=price
            )
            yield item
        # 这个地方还有一个下一页的数据 就是说他只有参数 域名是当前访问的url+这个参数就是下一页 也就是说用urljoin
        # 把原始的url加上参数 response.urljoin(next_url) 还有用yield scrapy 和上面一样调用自己就可以了
        # 这个地方算是一个方法把 细节的处理
        next_url = response.xpath('//div[@class="page"]//a[@class="next"]/@href').get()
        if next_url:  # 如果找得到这个url
            yield scrapy.Request(url=response.urljoin(next_url), callback=self.parse_newhouse,
                                 meta={"info": (province, city)})

    # 二手房的URL解析数据
    def parse_oldhouse(self, response):
        global year, name, address, rooms, area, floor, toward, price, unit
        province, city = response.meta.get('info')
        dls = response.xpath('//div[@class="shop_list shop_list_4"]/dl')
        for dl in dls:
            # 处理名字
            try:
                name = dl.xpath('.//p[@class="add_shop"]/a/text()').get().strip()
            except:
                pass

            # 处理地址
            try:
                address = dl.xpath('.//p[@class="add_shop"]/span/text()').get().strip()
            except:
                pass

            # 处理 几室几厅，朝向 面积，层数 年份
            try:
                ps = dl.xpath('.//p[@class="tel_shop"]//text()').getall()
                pss = list(map(lambda x: re.sub("\s|\|", "", x), ps))
                # 几室几厅
                rooms = pss[0]
                # 面积
                area = pss[2]
                # 楼层
                floor = pss[4]
                # 朝向
                toward = pss[6]
                # 年代
                year = pss[8]
            except Exception:
                pass

            # 原始url
            origin_url = response.url

            #处理总价和单价
            try:
                prs = dl.xpath('.//dd[@class="price_right"]//span//text()').getall()
                price = prs[1]+prs[2]
                unit = prs[3]
            except Exception:
                pass

            # 处理Item
            item = EsfHouseItem(
                province=province,
                city=city,
                name=name,
                origin_url=origin_url,
                address=address,
                rooms=rooms,
                area=area,
                floor=floor,
                toward=toward,
                year=year,
                price=price,
                unit=unit
            )
            yield item

        next_url = response.xpath('//div[@class="page_box"]//p[1]/a/@href').get()
        print(next_url)
        if next_url:  # 如果找得到这个url
            yield scrapy.Request(url=response.urljoin(next_url), callback=self.parse_oldhouse,
                                 meta={"info": (province, city)})