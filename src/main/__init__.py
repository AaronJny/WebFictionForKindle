# -*- coding: utf-8 -*-
# @File    : __init__.py.py
# @Author  : AaronJny
# @Time    : 2020/03/01
# @Desc    :
from flask import Blueprint

main_blueprint = Blueprint('main_blueprint', __name__)

from . import views