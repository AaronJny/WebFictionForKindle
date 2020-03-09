# -*- coding: utf-8 -*-
# @File    : db_models.py
# @Author  : AaronJny
# @Time    : 2020/02/29
# @Desc    :
from datetime import datetime
import typing
from . import db


class SpiderConfig(db.Model):
    """
    爬虫配置信息
    """
    scid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    site = db.Column(db.String(32), nullable=False, default='', comment='网站名称')
    domain = db.Column(db.String(32), nullable=False, default='', comment='网站域名')
    cls_name = db.Column(db.String(32), nullable=False, default='', comment='爬虫类名')
    spider_status = db.Column(db.SmallInteger, nullable=False, default=1, comment='爬虫状态 0-关闭，1-开启')

    def to_dict(self):
        data = {
            'scid': self.scid,
            'site': self.site,
            'domain': self.domain,
            'cls_name': self.cls_name,
            'spider_status': self.spider_status
        }
        return data

    @classmethod
    def all_usable_spider_configs(cls):
        """
        获取全部开启状态的爬虫信息
        """
        spider_configs = SpiderConfig.query.filter(SpiderConfig.spider_status == 1).all()
        return spider_configs

    @classmethod
    def all_spider_configs(cls):
        """
        获取全部的爬虫信息
        """
        spider_configs = SpiderConfig.query.all()
        return spider_configs


class Fictions(db.Model):
    """
    小说信息表
    """

    fid = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    site = db.Column(db.String(32), nullable=False, comment='来源站点', index=True)
    origin_id = db.Column(db.String(64), nullable=False, comment='小说在来源站点上的编号,可能是字符,选string类型', index=True)
    fiction_name = db.Column(db.String(32), nullable=False, comment='小说名称')
    fiction_author = db.Column(db.String(32), nullable=False, default='', comment='小说作者')
    fiction_url = db.Column(db.String(128), nullable=False, default='', comment='小说原始链接')
    fiction_chapters_total = db.Column(db.Integer, nullable=False, default=0, comment='小说在原网站上的总章节数')
    image_url = db.Column(db.String(128), nullable=False, default='', comment='小说图片地址')
    update_time = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='更新时间')
    # fiction_cached = db.Column(db.SmallInteger, nullable=False, default=0, comment='小说是否已经进行缓存，1-是，0-否')

    # 小说对应的全部章节
    chapters = db.relationship('FictionChapters', backref='fiction', lazy=True)

    def to_dict(self):
        data = {
            'fid': self.fid,
            'site': self.site,
            'origin_id': self.origin_id,
            'fiction_name': self.fiction_name,
            'fiction_author': self.fiction_author,
            'fiction_url': self.fiction_url,
            'fiction_chapters_total': self.fiction_chapters_total,
            'image_url': self.image_url,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        return data

    @property
    def cached_chapters_number(self):
        """
        查询当前小说在数据库中缓存的章节数
        """
        chapters_number = FictionChapters.query.filter_by(fiction_id=self.fid).count()
        return chapters_number

    @property
    def cached_chapter_origin_ids(self):
        """
        查询当前小说在数据库中缓存的章节的原始编号
        """
        origin_ids = FictionChapters.query.filter(FictionChapters.fiction_id == self.fid).with_entities(
            FictionChapters.origin_id).all()
        return origin_ids

    def add_or_update(self):
        """
        如果是新小说，就加入到小说信息表中。
        如果已经在表中了，就更新小说链接和缓存状态
        """
        fiction: Fictions = Fictions.query.filter(Fictions.site == self.site,
                                                  Fictions.origin_id == self.origin_id).first()
        if fiction:
            fiction.fiction_url = self.fiction_url
            fiction.fiction_cached = 0
            ret = fiction
        else:
            db.session.add(self)
            ret = self
        db.session.commit()
        return ret

    def generate_txt_bytes(self):
        """
        生成文本数据字节序列
        """
        cached_chapters: typing.List[FictionChapters] = sorted(self.chapters, key=lambda x: x.chapter_order)
        texts = []
        for chapter in cached_chapters:
            text = '{}\n\n{}\n'.format(chapter.chapter_name, chapter.chapter_content)
            texts.append(text)
        fiction_txt_str = '\n'.join(texts)
        fiction_txt_bytes = fiction_txt_str.encode('utf8')
        return fiction_txt_bytes


class FictionChapters(db.Model):
    """
    小说章节信息表
    """

    fcid = db.Column(db.Integer, nullable=False, autoincrement=True, primary_key=True)
    fiction_id = db.Column(db.Integer, db.ForeignKey('fictions.fid'), nullable=False, comment='小说编号')
    chapter_name = db.Column(db.String(64), nullable=False, default='', comment='章节名')
    chapter_content = db.Column(db.Text, nullable=False, default='', comment='章节内容')
    chapter_order = db.Column(db.Integer, nullable=False, default=0, comment='章节排序')
    origin_url = db.Column(db.String(128), nullable=False, default='', comment='来源地址')
    origin_id = db.Column(db.Integer, nullable=False, default=0, comment='来源网站上的小说章节编号')
    add_time = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='下载日期')


class EmailConfig(db.Model):
    """
    邮箱配置信息
    """

    ecid = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    sender = db.Column(db.String(64), nullable=False, default='', comment='发件人邮箱')
    password = db.Column(db.String(64), nullable=False, default='', comment='密码或授权码')
    smtp_host = db.Column(db.String(64), nullable=False, default='', comment='smtp主机地址')
    smtp_port = db.Column(db.Integer, nullable=False, default=465, comment='smtp端口地址')
    recipient = db.Column(db.String(64), nullable=False, default='', comment='收件人邮箱(kindle接收邮箱)')

    def to_dict(self):
        data = {
            'ecid': self.ecid,
            'sender': self.sender,
            'password': self.password,
            'smtp_host': self.smtp_host,
            'smtp_port': self.smtp_port,
            'recipient': self.recipient
        }
        return data

    @classmethod
    def get_email_config(cls):
        """
        从数据库中查询一个可用的邮箱配置
        """
        email_config = EmailConfig.query.first()
        return email_config
