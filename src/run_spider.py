# -*- coding: utf-8 -*-
# @File    : run_spider.py
# @Author  : AaronJny
# @Time    : 2020/03/06
# @Desc    :
from loguru import logger
from models import SpiderConfig
from spiders import SpiderManager
from utils import mysql

logger.info('章节内容下载爬虫已启动，正在监听队列……')

session = mysql.create_sqlalchemy_session()
spider_configs = session.query(SpiderConfig).filter(SpiderConfig.spider_status == 1).all()

spider_manager = SpiderManager.from_spider_configs(spider_configs)
spider_manager.listen_and_crawl_chapter_contents(session)

session.close()

logger.info('爬虫已关闭！')
