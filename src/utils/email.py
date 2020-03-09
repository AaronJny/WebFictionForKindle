# -*- coding: utf-8 -*-
# @File    : email.py
# @Author  : AaronJny
# @Time    : 2020/03/07
# @Desc    :
import yagmail


def create_smtp_client(email_config):
    """
    根据给定的邮箱配置信息，创建一个smtp客户端
    Args:
        email_config: 邮箱配置信息
    """
    smtp = yagmail.SMTP(user=email_config.sender, password=email_config.password, host=email_config.smtp_host,
                        port=email_config.smtp_port, encoding='gbk')
    return smtp
