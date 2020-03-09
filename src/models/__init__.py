# -*- coding: utf-8 -*-
# @File    : __init__.py.py
# @Author  : AaronJny
# @Time    : 2020/02/28
# @Desc    :
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .spider_models import *
from .db_models import *