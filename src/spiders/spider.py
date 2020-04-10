# -*- coding: utf-8 -*-
# @File    : run_spider.py
# @Author  : AaronJny
# @Time    : 2020/02/28
# @Desc    :
import json
import re
import traceback
import typing
from cattr import structure
from bs4 import BeautifulSoup
from loguru import logger
import requests
from tenacity import retry, stop_after_attempt, wait_fixed
from urllib.parse import urljoin
from models import FictionSearchItem, SpiderConfig, SimpleChapter
from models import MiddleChapter, FictionChapters
from models import db
from utils import rabbitmq


class BaseSpider:
    """
    爬虫基本类
    """

    # 域名
    domain = 'sample.com'
    # 网站名称
    site = '示例网站'

    @classmethod
    def replace_br(cls, content: bytes, encoding='utf8'):
        """
        将content中的br标签，替换成\n+br，以保证换行被正确保留

        Args:
            content: 网页字节序列
            encoding: 编码方式
        """
        html = content.decode(encoding, errors='ignore')
        html = re.sub('<[ ]*br[ ]*/?[ ]*>', '\n<br>', html)
        return html

    def search_fictions_by_name(self, fiction_name):
        """
        通过书名检索相关书籍

        Args:
            fiction_name: 小说名称

        Returns:
            检索到的小说信息列表
        """
        try:
            results = self._search_fictions_by_name(fiction_name)
        except Exception as e:
            results = []
            logger.error(str(e))
        return results

    def _search_fictions_by_name(self, fiction_name):
        raise NotImplementedError

    def get_chapters(self, fiction_url: str, fiction_name: str):
        """
        解析小说全部章节信息

        Args:
            fiction_url: 小说主页地址
            fiction_name: 小说名称
        """
        try:
            result = self._get_chapters(fiction_url, fiction_name)
        except Exception as e:
            result = []
            traceback.print_exc()
            logger.error(e)
        return result

    def _get_chapters(self, fiction_url, fiction_name):
        raise NotImplementedError

    def download_chapter(self, middle_chapter: MiddleChapter):
        """
        根据章节信息，从网络上下载章节内容

        Args:
            middle_chapter: 章节基本信息

        Returns:
            MiddleChapter
        """
        try:
            result = self._download_chapter(middle_chapter)
        except Exception as e:
            result = None
            logger.error(e)
        return result

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _download_chapter(self, middle_chapter: MiddleChapter):
        raise NotImplementedError


class ZwdaSpider(BaseSpider):
    domain = 'www.zwda.com'
    site = 'E小说'

    def _search_fictions_by_name(self, fiction_name):
        headers = {
            'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36',
            'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Referer': 'https://{}'.format(self.domain),
        }

        params = (('q', fiction_name), )

        response = requests.get('https://{}/search.php'.format(self.domain),
                                headers=headers,
                                params=params,
                                timeout=20)

        bsobj = BeautifulSoup(response.content, 'lxml')
        # 提取搜索结果列表
        fiction_divs = bsobj.find('div', {
            'class': 'result-list'
        }).find_all('div', {'class': 'result-item'})
        results = []
        # 逐个解析小说信息
        for fiction_div in fiction_divs:
            # 小说封面地址
            image_url = fiction_div.find('div', {
                'class': 'result-game-item-pic'
            }).find('img').get('src')
            # 小说标题
            title = fiction_div.find('h3', {
                'class': 'result-item-title'
            }).get_text().strip()
            # 小说简介
            desc = fiction_div.find('p', {
                'class': 'result-game-item-desc'
            }).get_text().strip()
            info_tags = fiction_div.find('div', {
                'class': 'result-game-item-info'
            }).find_all('p', {'class': 'result-game-item-info-tag'})
            # 作者
            author = info_tags[0].find_all('span')[1].get_text().strip()
            # 类型
            fiction_kind = info_tags[1].find_all('span')[1].get_text().strip()
            # 更新时间
            update_date = info_tags[2].find_all('span')[1].get_text().strip()
            # 最新章节
            latest_chapter = info_tags[3].find('a').get_text().strip()
            # 小说地址
            origin_url = fiction_div.find('h3').find('a').get('href')
            origin_url = urljoin('https://{}'.format(self.domain), origin_url)
            # 来源站点上的编号
            origin_id = origin_url.strip('/').split('/')[-1]
            # 创建实例
            fiction_search_item = FictionSearchItem(
                fiction_name=title,
                image_url=image_url,
                author=author,
                fiction_kind=fiction_kind,
                update_date=update_date,
                latest_chapter=latest_chapter,
                introduction=desc,
                site=self.site,
                origin_url=origin_url,
                origin_id=origin_id)
            results.append(fiction_search_item)
        return results

    def _get_chapters(self, fiction_url, fiction_name):
        headers = {
            'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36',
            'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Referer': 'https://{}/search.php?keyword='.format(self.domain),
        }
        response = requests.get(fiction_url, headers=headers, timeout=20)

        chapters = []

        bsobj = BeautifulSoup(response.content, 'lxml')
        a_tags = bsobj.find('div', {'id': 'list'}).find_all('a')
        for index, a_tag in enumerate(a_tags):
            chapter_url = a_tag.get('href')
            chapter_url = urljoin(fiction_url, chapter_url)
            origin_id = int(chapter_url.strip('/').split('/')[-1])
            chapter_name = a_tag.get_text().strip()
            simple_chapter = SimpleChapter(origin_id=origin_id,
                                           chapter_name=chapter_name,
                                           chapter_url=chapter_url,
                                           chapter_order=index)
            chapters.append(simple_chapter)
        return chapters

    def _download_chapter(self, middle_chapter: MiddleChapter):
        headers = {
            'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36',
            'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Referer': middle_chapter.fiction_url,
        }
        response = requests.get(middle_chapter.chapter_url,
                                headers=headers,
                                timeout=20)
        html = self.replace_br(response.content, encoding='gbk')
        bsobj = BeautifulSoup(html, 'lxml')
        content = bsobj.find('div', {'id': 'content'}).get_text()
        middle_chapter.chapter_content = content
        return middle_chapter


class SpiderManager:
    """
    爬虫管理器
    """
    def __init__(self, spiders: typing.Dict[str, BaseSpider] = None):
        if spiders:
            self.spiders = spiders
        else:
            spider_configs = SpiderConfig.all_usable_spider_configs()
            self.spiders = self.spider_configs_to_spiders(spider_configs)
        # 数据库连接，默认不创建，按需创建
        self.session = None

    @classmethod
    def spider_configs_to_spiders(cls,
                                  spider_configs: typing.List[SpiderConfig]):
        """
        给定爬虫配置数据，创建并返回爬虫实例

        Args:
            spider_configs: 爬虫配置信息

        Returns:
            typing.Dict[str,BaseSpider]
        """

        spiders = {}
        for spider_config in spider_configs:
            # 根据爬虫类名查找对应爬虫类
            spider_cls = globals().get(spider_config.cls_name, None)
            # 利用反射机制创建相应实例
            if spider_cls:
                spider: BaseSpider = spider_cls()
                spider.site = spider_config.site
                spider.domain = spider.domain
                spiders[spider.site] = spider
        return spiders

    @classmethod
    def from_spider_configs(cls, spider_configs: typing.List[SpiderConfig]):
        """
        从爬虫配置信息创建爬虫管理器

        Args:
            spider_configs: 爬虫配置信息

        Returns:
            爬虫管理器实例
        """
        spiders = cls.spider_configs_to_spiders(spider_configs)
        return cls(spiders=spiders)

    def search_fictions_by_name(self, fiction_name: str):
        """
        根据小说名称，使用爬虫查询相关小说信息

        Args:
            fiction_name: 小说名称

        Returns:
            typing.List[FictionSearchItem]
        """
        fiction_search_items = []
        for site, spider in self.spiders.items():
            fiction_search_items.extend(
                spider.search_fictions_by_name(fiction_name))
        return fiction_search_items

    def get_chapters(self, fiction_url: str, fiction_name, site: str):
        """
        根据给定的小说主页地址和网站名称，抓取小说的章节列表
        Args:
            fiction_url: 小说主页地址
            fiction_name: 小说名称
            site: 网站名称

        Returns:
            typing.List[SimpleChapter]
        """
        spider: BaseSpider = self.spiders.get(site)
        if spider:
            return spider.get_chapters(fiction_url, fiction_name)
        else:
            return []

    def crawl_chapter_content(self, channel, method_frame, header_frame, body):
        # 抓取章节内容
        data = json.loads(body)
        middle_chapter = structure(data, MiddleChapter)
        spider = self.spiders.get(middle_chapter.site)
        chapter: MiddleChapter = spider.download_chapter(middle_chapter)
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        # 写入数据库
        if chapter:
            fiction_chapter = FictionChapters(
                fiction_id=chapter.fiction_id,
                chapter_name=chapter.chapter_name,
                chapter_content=chapter.chapter_content,
                chapter_order=chapter.chapter_order,
                origin_url=chapter.chapter_url,
                origin_id=chapter.origin_id)
            try:
                self.session.add(fiction_chapter)
                self.session.commit()
            except Exception as e:
                logger.error(e)
                self.session.rollback()
            logger.info('已缓存章节 {}!'.format(chapter.chapter_name))

    def listen_and_crawl_chapter_contents(self, session):
        """
        监听消息队列，持续读取采集需求并进行处理

        Args:
            session: 数据库会话
        """
        connection, channel = rabbitmq.create_rabbitmq_connection()
        channel.basic_consume('standard', self.crawl_chapter_content)
        self.session = session
        while True:
            try:
                channel.start_consuming()
            except KeyboardInterrupt:
                channel.stop_consuming()
                break
            except Exception as e:
                logger.error(e)


def init_spider_configs():
    """
    解析爬虫脚本中的全部爬虫类，并将新增的爬虫类信息添加到数据库中
    """
    # 先加载全部的爬虫配置信息
    spider_configs = SpiderConfig.all_spider_configs()
    spider_cls_names = {
        spider_config.cls_name
        for spider_config in spider_configs
    }
    # 再将新增爬虫信息加入到数据库中
    tmp_globals = globals()
    for key, obj in tmp_globals.items():
        if 'Spider' in key and key != 'BaseSpider' and issubclass(
                obj, BaseSpider) and key not in spider_cls_names:
            spider_config = SpiderConfig(site=obj.site,
                                         domain=obj.domain,
                                         cls_name=key)
            db.session.add(spider_config)
            db.session.commit()
