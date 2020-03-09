# -*- coding: utf-8 -*-
# @File    : init_app.py
# @Author  : AaronJny
# @Time    : 2020/03/09
# @Desc    :
import shutil
import os
from config import Config
from models import SpiderConfig
from spiders import BaseSpider
from utils import mysql


def init_spider_configs(session):
    """
    解析爬虫脚本中的全部爬虫类，并将新增的爬虫类信息添加到数据库中

    Args:
        session: 数据库链接
    """
    # 先加载全部的爬虫配置信息
    spider_configs = session.query(SpiderConfig).all()
    spider_cls_names = {spider_config.cls_name for spider_config in spider_configs}
    # 再将新增爬虫信息加入到数据库中
    tmp_globals = globals()
    for key, obj in tmp_globals.items():
        if 'Spider' in key and key != 'BaseSpider' and issubclass(obj, BaseSpider) and key not in spider_cls_names:
            spider_config = SpiderConfig(site=obj.site, domain=obj.domain, cls_name=key)
            session.add(spider_config)
            session.commit()


def init_before_app_start():
    """
    在web程序启动前，执行一些初始化操作
    """
    # 清空临时文件夹
    temporary_file_path = Config.TEMPORARY_FILE_PATH
    if os.path.exists(temporary_file_path):
        shutil.rmtree(temporary_file_path)
    os.mkdir(temporary_file_path)
    # 初始化数据库
    session, metadata = mysql.create_sqlalchemy_session_and_metadata()
    metadata.create_all()
    # 初始爬虫信息
    init_spider_configs(session)

    session.close()


if __name__ == '__main__':
    init_before_app_start()
