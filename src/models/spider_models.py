# -*- coding: utf-8 -*-
# @File    : spider_models.py
# @Author  : AaronJny
# @Time    : 2020/02/28
# @Desc    :
from attr import attrs, attrib


@attrs
class FictionSearchItem(object):
    """
    小说搜索结果
    """

    # 小说名称
    fiction_name = attrib(type=str, default='')
    # 小说封面地址
    image_url = attrib(type=str, default='')
    # 小说作者
    author = attrib(type=str, default='')
    # 小说类型
    fiction_kind = attrib(type=str, default='')
    # 更新时间
    update_date = attrib(type=str, default='')
    # 最新章节
    latest_chapter = attrib(type=str, default='')
    # 简介
    introduction = attrib(type=str, default='')
    # 小说站点
    site = attrib(type=str, default='')
    # 小说地址
    origin_url = attrib(type=str, default='')
    # 在来源站点上的编号
    origin_id = attrib(type=str, default='')


@attrs
class SimpleChapter(object):
    """
    简要章节信息
    """

    # 章节在原始网站上的编号
    origin_id = attrib(type=int, default=0)
    # 章节名称
    chapter_name = attrib(type=str, default='')
    # 章节链接
    chapter_url = attrib(type=str, default='')
    # 章节排序,越小越靠前
    chapter_order = attrib(type=int, default=0)


@attrs
class MiddleChapter(object):
    """
    含有更多章节信息的数据项，用于生成爬虫请求队列
    """
    # 章节在原始网站上的编号
    origin_id = attrib(type=int, default=0)
    # 章节名称
    chapter_name = attrib(type=str, default='')
    # 章节链接
    chapter_url = attrib(type=str, default='')
    # 章节排序,越小越靠前
    chapter_order = attrib(type=int, default=0)
    # 小说编号
    fiction_id = attrib(type=int, default=0)
    # 章节内容
    chapter_content = attrib(type=str, default='')
    # 来源网站
    site = attrib(type=str, default='')
    # 小说主页地址
    fiction_url = attrib(type=str, default='')
