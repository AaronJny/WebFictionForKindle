# -*- coding: utf-8 -*-
# @File    : views.py
# @Author  : AaronJny
# @Time    : 2020/03/01
# @Desc    :
from flask import render_template
from . import main_blueprint


@main_blueprint.route('/')
def index():
    return render_template('index.html')
