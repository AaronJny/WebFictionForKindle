# -*- coding: utf-8 -*-
# @File    : config.py
# @Author  : AaronJny
# @Time    : 2020/02/29
# @Desc    :
import os


class Config:
    # 数据库配置
    DB_HOST = 'localhost'
    DB_PORT = 3306
    DB_USERNAME = 'root'
    DB_PASSWORD = '123456'
    DB_NAME = 'kindle_web_fiction'
    # ORM配置
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{username}:{password}@{host}:{port}/{db}'.format(
        username=DB_USERNAME, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT, db=DB_NAME)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 消息队列地址
    RABBITMQ_URL = 'amqp://guest:guest@localhost:5672/%2F'
    # 消息队列交换机名称
    RABBITMQ_EXCHANGE = 'spider_exchange'
    EXCHANGE_TYPE = 'direct'
    RABBITMQ_QUEUE = 'standard'
    ROUTING_KEY = 'requests'
    # 临时文件夹路径
    TEMPORARY_FILE_PATH = os.path.abspath(os.path.join(os.curdir, './tmp'))
