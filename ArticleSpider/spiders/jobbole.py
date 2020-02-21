# -*- coding: utf-8 -*-
from urllib import parse
import requests
import re
import json

import scrapy
from ArticleSpider.items import ArticleItemLoader
from scrapy import Request

from ArticleSpider.items import JobBoleArticleItem
from ArticleSpider.utils import common


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['news.cnblogs.com']
    start_urls = ['http://news.cnblogs.com/']

    # 不要立刻爬取所有的新闻
    def parse(self, response):
        """
        1.获取新闻列表页面中的新闻url 并交给scrapy进行下载后调用相应的解析方法
        2.获取下一页的url并交给scrapy进行下载，下载完成后交给parse继续跟进
        :param response:
        :return:
        """
        # post_nodes = response.css('#news_list .news_block')[1:10]
        post_nodes = response.css('#news_list .news_block')
        for post_node in post_nodes:
            image_url = post_node.css('.entry_summary a img::attr(src)').extract_first("")
            if not image_url.startswith("https:"):
                image_url = '{}{}'.format('https:', image_url)

            post_url = post_node.css('h2 a::attr(href)').extract_first("")
            yield Request(url=parse.urljoin(response.url, post_url), meta={"front_image_url": image_url}, callback=self.parse_detail)

        # 提取下一页并交给scrapy
        next_url = response.xpath("//a[contains(text(),'Next >')]/@href").extract_first("")
        yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)

    # 详情页面爬取
    def parse_detail(self, response):
        # 判断是否时常规的列表页面详情元素
        match_re = re.match(".*?(\d+)",response.url)
        if match_re:
            post_id = match_re.group(1)
            # article_item = JobBoleArticleItem()
            # 获取静态元素
            # title = response.css("#news_title a::text").extract_first("")
            # title = response.xpath("//*[@id='news_title']//a/text()").extract_first("")
            # create_date = response.css("#news_info .time::text").extract_first("")
            # create_date = response.xpath("//*[@id='news_info']//*[@class='time']/text()").extract_first("")
            # match_re = re.match(".*?(\d+.*)",create_date)
            # if match_re:
            #     create_date = match_re.group(1)
            # content = response.css("#news_content").extract()[0]
            # content = response.xpath("//*[@id='news_content']").extract()[0]
            # tag_list = response.css(".news_tags a::text").extract()
            # tag_list = response.xpath("//*[@class='news_tags']//a/text()").extract()
            # tags = ",".join(tag_list)

            # 获取动态js元素

            # html = requests.get(parse.urljoin(response.url, "/NewsAjax/GetAjaxNewsInfo?contentId={}".format(post_id)))
            # j_data = json.loads(html.text)

            # article_item["title"] = title
            # article_item["create_date"] = create_date
            # article_item["content"] = content
            # article_item["tags"] = tags
            # article_item["url"] = response.url
            # if response.meta.get("front_image_url", ""):
            #     article_item["front_image_url"] = [response.meta.get("front_image_url", "")]
            # else:
            #     article_item["front_image_url"] = []

            item_loader = ArticleItemLoader(item=JobBoleArticleItem(), response=response)
            item_loader.add_css("title", "#news_title a::text")
            item_loader.add_css("content", "#news_content")
            item_loader.add_css("tags", ".news_tags a::text")
            item_loader.add_css("create_date", "#news_info .time::text")
            item_loader.add_value("url", response.url)
            item_loader.add_value("front_image_url", response.meta.get("front_image_url", ""))

            # article_item = item_loader.load_item()

            yield Request(url=parse.urljoin(response.url, "/NewsAjax/GetAjaxNewsInfo?contentId={}".format(post_id)),
                          meta={"article_item": item_loader, "url": response.url}, callback=self.parse_nums)

    def parse_nums(self, response):
        j_data = json.loads(response.text)
        item_loader = response.meta.get("article_item", "")

        # praise_nums = j_data["DiggCount"]
        # fav_nums = j_data["TotalView"]
        # comment_nums = j_data["CommentCount"]

        # article_item["praise_nums"] = praise_nums
        # article_item["fav_nums"] = fav_nums
        # article_item["comment_nums"] = comment_nums
        # article_item["url_object_id"] = common.get_md5(article_item["url"])

        item_loader.add_value("praise_nums", j_data["DiggCount"])
        item_loader.add_value("fav_nums", j_data["TotalView"])
        item_loader.add_value("comment_nums", j_data["CommentCount"])
        item_loader.add_value("url_object_id", common.get_md5(response.meta.get("url", "")))
        article_item = item_loader.load_item()

        yield article_item
