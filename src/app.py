# -*- coding: utf-8 -*-
# @File    : app.py
# @Author  : AaronJny
# @Time    : 2020/03/01
# @Desc    :
from flask import Flask
from config import Config
from models import db
from flask_cors import CORS

cors = CORS()


def create_app():
    app = Flask(__name__, static_folder='../dist', template_folder='../dist', static_url_path='')
    # 使用Config类初始化配置参数
    app.config.from_object(Config)

    # 允许跨域请求
    cors.init_app(app)

    # 初始化数据库链接
    db.init_app(app)

    # 挂载api_v1_blueprint
    from api import api_v1_blueprint
    app.register_blueprint(api_v1_blueprint)
    # 挂载main_blueprint
    from main import main_blueprint
    app.register_blueprint(main_blueprint)

    # 退出程序时关闭数据库连接
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    return app


app = create_app()

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=7777)
