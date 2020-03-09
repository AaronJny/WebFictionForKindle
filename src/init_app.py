# -*- coding: utf-8 -*-
# @File    : init_app.py
# @Author  : AaronJny
# @Time    : 2020/03/09
# @Desc    :
import shutil
import os
from app import app
from models import db
from models import SpiderConfig
from spiders import BaseSpider


def init_spider_configs():
    """
    解析爬虫脚本中的全部爬虫类，并将新增的爬虫类信息添加到数据库中
    """
    # 先加载全部的爬虫配置信息
    spider_configs = SpiderConfig.all_spider_configs()
    spider_cls_names = {spider_config.cls_name for spider_config in spider_configs}
    # 再将新增爬虫信息加入到数据库中
    tmp_globals = globals()
    for key, obj in tmp_globals.items():
        if 'Spider' in key and key != 'BaseSpider' and issubclass(obj, BaseSpider) and key not in spider_cls_names:
            spider_config = SpiderConfig(site=obj.site, domain=obj.domain, cls_name=key)
            db.session.add(spider_config)
            db.session.commit()


def init_before_app_start():
    """
    在web程序启动前，执行一些初始化操作
    """
    # 清空临时文件夹
    temporary_file_path = app.config.get('TEMPORARY_FILE_PATH')
    if os.path.exists(temporary_file_path):
        shutil.rmtree(temporary_file_path)
    os.mkdir(temporary_file_path)
    with app.app_context():
        # 初始化数据库
        db.create_all()
        # 初始爬虫信息
        init_spider_configs()

    db.session.remove()


if __name__ == '__main__':
    init_before_app_start()
