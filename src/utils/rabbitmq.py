# -*- coding: utf-8 -*-
# @File    : rabbitmq.py
# @Author  : AaronJny
# @Time    : 2020/03/05
# @Desc    :
import pika
from config import Config


def create_rabbitmq_connection():
    """
    创建并初始化rabbitmq连接，返回连接和channel
    """
    # 创建连接
    parameters = pika.URLParameters(Config.RABBITMQ_URL)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.exchange_declare(exchange=Config.RABBITMQ_EXCHANGE, exchange_type=Config.EXCHANGE_TYPE, passive=False,
                             durable=True, auto_delete=False)
    channel.queue_declare(queue=Config.RABBITMQ_QUEUE, auto_delete=True)
    channel.queue_bind(queue=Config.RABBITMQ_QUEUE, exchange=Config.RABBITMQ_EXCHANGE, routing_key=Config.ROUTING_KEY)
    # 接收确认消息
    channel.confirm_delivery()
    return connection, channel


def send_msg(channel, data, content_type='application/json'):
    """
    通过channel将content_type类型的数据data写入到消息队列中

    Args:
        channel: 信道
        data: 待写入数据
        content_type: 数据类型
    """
    props = pika.BasicProperties(content_type=content_type, delivery_mode=2)
    channel.basic_publish(Config.RABBITMQ_EXCHANGE, routing_key=Config.ROUTING_KEY, body=data, properties=props)
