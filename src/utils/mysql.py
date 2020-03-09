# -*- coding: utf-8 -*-
# @File    : mysql.py
# @Author  : AaronJny
# @Time    : 2020/03/06
# @Desc    :
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import Config


def create_sqlalchemy_session():
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    session_cls = sessionmaker(bind=engine)
    session = session_cls()
    return session
