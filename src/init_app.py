# -*- coding: utf-8 -*-
# @File    : init_app.py
# @Author  : AaronJny
# @Time    : 2020/03/09
# @Desc    :
import shutil
import os
from app import app
from models import db
from spiders import init_spider_configs


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
