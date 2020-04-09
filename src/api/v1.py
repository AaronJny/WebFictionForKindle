# -*- coding: utf-8 -*-
# @File    : v1.py
# @Author  : AaronJny
# @Time    : 2020/02/28
# @Desc    :
from datetime import datetime
import mimetypes
import json
import os
import typing
from cattr import unstructure
from flask import request, jsonify, current_app
from flask import make_response
from flask import Blueprint
from loguru import logger
from spiders import SpiderManager
from models import Fictions, SimpleChapter, MiddleChapter, FictionChapters
from models import SpiderConfig, EmailConfig
from models import db
from utils import rabbitmq, email

api_v1_blueprint = Blueprint('api_v1_blueprint', __name__, url_prefix='/api/v1')


@api_v1_blueprint.route('/search/name/', methods=['POST'])
def search_fiction_by_name():
    """
    通过网文名称搜索
    """
    fiction_name = request.json.get('fiction_name', '')
    spider_manager = SpiderManager()
    fictions = spider_manager.search_fictions_by_name(fiction_name)
    ret = {
        'code': 0,
        'total': len(fictions),
        'fictions': unstructure(fictions)
    }
    return jsonify(ret)


@api_v1_blueprint.route('/fictions/add/', methods=['POST'])
def add_fiction():
    """
    添加一本小说到数据库中
    """
    fiction_name = request.json.get('fiction_name')
    fiction_author = request.json.get('fiction_author')
    fiction_url = request.json.get('fiction_url')
    site = request.json.get('site')
    origin_id = request.json.get('origin_id')
    image_url = request.json.get('image_url')

    fiction = Fictions(site=site, origin_id=origin_id, fiction_name=fiction_name, fiction_author=fiction_author,
                       fiction_url=fiction_url, image_url=image_url)
    fiction = fiction.add_or_update()
    ret = {
        'code': 0,
        'msg': '添加成功！',
        'fiction_id': fiction.fid
    }
    return jsonify(ret)


@api_v1_blueprint.route('/fictions/update/', methods=['POST'])
def update_fiction_by_id():
    """
    根据给定的小说编号，从数据库中加载小说信息，并通过爬虫采集小说章节列表，
    将新增章节推送到采集队列中等待采集
    """
    fiction_id = request.json.get('fiction_id')
    fiction: Fictions = Fictions.query.get(fiction_id)
    if not fiction:
        raise Exception('指定小说不存在！')
    # 获取已经缓存的章节列表
    chapter_origin_ids = {item[0] for item in fiction.cached_chapter_origin_ids}
    # 使用爬虫加载最新的章节列表
    spider_manager = SpiderManager()
    simple_chapters: typing.List[SimpleChapter] = spider_manager.get_chapters(fiction.fiction_url, fiction.fiction_name,
                                                                              fiction.site)
    # 更新fiction中完整章节数
    fiction.fiction_chapters_total = len(simple_chapters)
    fiction.update_time = datetime.now()
    db.session.commit()
    # 过滤出需要采集的章节列表
    uncached_chapters = [chapter for chapter in simple_chapters if chapter.origin_id not in chapter_origin_ids]
    # 推送到采集队列中
    connection, channel = rabbitmq.create_rabbitmq_connection()
    for chapter in uncached_chapters:
        middle_chapter = MiddleChapter(origin_id=chapter.origin_id, chapter_name=chapter.chapter_name,
                                       chapter_url=chapter.chapter_url, chapter_order=chapter.chapter_order,
                                       fiction_id=fiction_id, chapter_content='', site=fiction.site,
                                       fiction_url=fiction.fiction_url)
        rabbitmq.send_msg(channel, json.dumps(unstructure(middle_chapter)))
    connection.close()
    # 返回响应
    ret = {
        'code': 0,
        'msg': '请求成功！',
        'uncached_chapters': len(uncached_chapters)
    }
    return jsonify(ret)


@api_v1_blueprint.route('/fictions/all/', methods=['POST'])
def all_fictions():
    """
    读取全部小说信息
    """
    cur_page = request.json.get('cur_page', 0)
    page_size = request.json.get('page_size', 18)
    # 按时间倒序
    fictions = Fictions.query.order_by(Fictions.update_time.desc()).limit(page_size).offset(
        (cur_page - 1) * page_size).all()
    # 统计每个小说当前缓存了多少章节
    fiction_ids = {fiction.fid for fiction in fictions}
    count_result = FictionChapters.query.with_entities(FictionChapters.fiction_id,
                                                       db.func.count(FictionChapters.fcid)).filter(
        FictionChapters.fiction_id.in_(fiction_ids)).group_by(FictionChapters.fiction_id).all()
    chapters_count_map = {fiction_id: chapters_count for fiction_id, chapters_count in count_result}
    # 转小说信息转成dict，并将缓存章节数量注入其中
    fiction_infos = []
    for fiction in fictions:
        fiction_info = fiction.to_dict()
        fiction_info['cached_chapters_number'] = chapters_count_map.get(fiction.fid, 0)
        if fiction.fiction_chapters_total == 0:
            cached_percentage = 100
        else:
            cached_percentage = fiction_info['cached_chapters_number'] / fiction.fiction_chapters_total * 100
        fiction_info['cached_percentage'] = round(cached_percentage, 2)
        fiction_infos.append(fiction_info)
    total = Fictions.query.count()
    ret = {
        'code': 0,
        'msg': '请求成功',
        'fictions': fiction_infos,
        'total': total
    }
    return jsonify(ret)


@api_v1_blueprint.route('/fictions/delete/<fiction_id>/', methods=['GET'])
def delete_fiction(fiction_id):
    """
    删除指定小说

    Args:
        fiction_id: 小说编号
    """
    fiction_id = int(fiction_id)
    fiction: Fictions = Fictions.query.get(fiction_id)
    if not fiction:
        raise Exception('指定小说不存在！')
    # 先删除所有章节
    FictionChapters.query.filter(FictionChapters.fiction_id == fiction_id).delete()
    # 再删除小说
    db.session.delete(fiction)
    db.session.commit()
    ret = {
        'code': 0,
        'msg': '删除成功！'
    }
    return jsonify(ret)


@api_v1_blueprint.route('/fictions/download/<fiction_id>/', methods=['GET'])
def download_fiction(fiction_id):
    """
    从数据库中读取指定小说章节内容，并组织成txt文件返回

    Args:
        fiction_id: 小说编号
    """
    fiction_id = int(fiction_id)
    fiction: Fictions = Fictions.query.get(fiction_id)
    if not fiction:
        raise Exception('指定小说不存在！')
    # 抽取小说内容
    fiction_txt_bytes = fiction.generate_txt_bytes()
    file_name = '{}.txt'.format(fiction.fiction_name)
    response = make_response(fiction_txt_bytes)
    mime_type = mimetypes.guess_type(file_name)
    response.headers['Content-Type'] = mime_type
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(file_name.encode().decode('latin-1'))
    return response


@api_v1_blueprint.route('/fictions/progress/<fiction_id>/', methods=['GET'])
def check_fiction_cached_progress(fiction_id):
    """
    获取指定小说的章节下载进度

    Args:
        fiction_id: 小说编号
    """
    fiction_id = int(fiction_id)
    fiction: Fictions = Fictions.get(fiction_id)
    if not fiction:
        raise Exception('小说不存在！')
    cached_number = fiction.cached_chapters_number
    total_number = fiction.fiction_chapters_total
    ret = {
        'code': 0,
        'msg': '请求成功！',
        'cached_number': cached_number,
        'total_number': total_number
    }
    return jsonify(ret)


@api_v1_blueprint.route('/spider_configs/all/', methods=['GET'])
def all_spider_configs():
    """
    去读所有爬虫配置信息
    """
    spider_configs: typing.List[SpiderConfig] = SpiderConfig.query.order_by(SpiderConfig.spider_status.desc()).all()
    spider_configs = [spider_config.to_dict() for spider_config in spider_configs]
    ret = {
        'code': 0,
        'msg': '请求成功！',
        'spider_configs': spider_configs
    }
    return jsonify(ret)


@api_v1_blueprint.route('/spider_configs/update/', methods=['POST'])
def update_spider_config():
    """
    更新爬虫配置信息
    """
    scid = request.json.get('scid', 0)
    spider_config: SpiderConfig = SpiderConfig.query.get(scid)
    if not spider_config:
        raise Exception('找不到爬虫配置信息！')
    domain = request.json.get('domain')
    open_status = request.json.get('open_status')
    spider_status = 1 if open_status else 0
    # 当数据变化时更新数据库
    if spider_config.domain != domain or spider_config.spider_status != spider_status:
        spider_config.domain = domain
        spider_config.spider_status = spider_status
        db.session.commit()
    ret = {
        'code': 0,
        'msg': '更新成功！'
    }
    return jsonify(ret)


@api_v1_blueprint.route('/email_config/', methods=['GET'])
def read_email_config():
    """
    从数据库中读取邮件推送配置配置信息
    """
    email_config = EmailConfig.query.first()
    if email_config:
        data = email_config.to_dict()
    else:
        data = {
            'ecid': 0,
            'sender': '',
            'password': '',
            'smtp_host': 'smtp.163.com',
            'smtp_port': 465,
            'recipient': ''
        }
    ret = {
        'code': 0,
        'email_config': data
    }
    return jsonify(ret)


@api_v1_blueprint.route('/email_config/update/', methods=['POST'])
def update_email_config():
    """
    更新邮件推送相关配置
    """
    ecid = request.json.get('ecid')
    sender = request.json.get('sender')
    password = request.json.get('password')
    smtp_host = request.json.get('smtp_host')
    smtp_port = int(request.json.get('smtp_port'))
    recipient = request.json.get('recipient')

    email_config = None
    if ecid:
        email_config: EmailConfig = EmailConfig.query.get(ecid)
    # 有就更新
    if email_config:
        email_config.sender = sender
        email_config.password = password
        email_config.smtp_host = smtp_host
        email_config.smtp_port = smtp_port
        email_config.recipient = recipient
    # 没有就新增
    else:
        email_config = EmailConfig(sender=sender, password=password, smtp_host=smtp_host, smtp_port=smtp_port,
                                   recipient=recipient)
        db.session.add(email_config)
    db.session.commit()

    ret = {
        'code': 0,
        'msg': '更新成功！'
    }
    return jsonify(ret)


@api_v1_blueprint.route('/fictions/send/<fiction_id>/', methods=['GET'])
def send_fiction_to_kindle(fiction_id):
    """
    将指定小说通过邮箱推送到kindle上

    Args:
        fiction_id: 小说编号
    """
    # 定位小说
    fiction_id = int(fiction_id)
    fiction: Fictions = Fictions.query.get(fiction_id)
    if not fiction:
        raise Exception('指定小说不存在！')
    # 生成临时小说
    text_bytes = fiction.generate_txt_bytes()
    filename = '{}_{}.txt'.format(fiction.fiction_name, int(datetime.now().timestamp()))
    temporary_file_path = current_app.config.get('TEMPORARY_FILE_PATH')
    file_path = os.path.join(temporary_file_path, filename)
    with open(file_path, 'wb') as f:
        f.write(text_bytes)
    # 读取邮箱配置信息
    email_config: EmailConfig = EmailConfig.query.first()
    if not email_config:
        ret = {
            'code': -1,
            'msg': '邮箱信息不正确！请重新配置！'
        }
    else:
        # 发送邮件
        try:
            smtp = email.create_smtp_client(email_config)
            smtp.send(to=email_config.recipient, subject=fiction.fiction_name, contents=[file_path, ])
            ret = {
                'code': 0,
                'msg': '邮件推送成功，kindle更新有延迟，请耐心等待～'
            }
        except Exception as e:
            logger.error(e)
            ret = {
                'code': -1,
                'msg': '邮件发送失败，请确认邮箱配置！'
            }
    # 删除临时小说
    os.remove(file_path)
    return jsonify(ret)
