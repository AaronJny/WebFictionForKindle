# -*- coding: utf-8 -*-
# @File    : mysql.py
# @Author  : AaronJny
# @Time    : 2020/03/06
# @Desc    :
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from config import Config


def create_sqlalchemy_session(engine=None):
    if not engine:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    session_cls = sessionmaker(bind=engine)
    session = session_cls()
    return session


def create_sqlalchemy_metadata(engine=None):
    if not engine:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    metadata = MetaData(engine)
    return metadata


def create_sqlalchemy_session_and_metadata(engine=None):
    if not engine:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    session = create_sqlalchemy_session(engine=engine)
    metadata = create_sqlalchemy_metadata(engine=engine)
    return session, metadata
