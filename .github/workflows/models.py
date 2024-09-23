import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, func, and_
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declarative_base, relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import sessionmaker
from flask import request
from flask_sqlalchemy import SQLAlchemy
from typing import Dict, Any
from diplom_project.main.config import ALLOWED_EXTENSIONS

db = SQLAlchemy()
engine = create_engine('postgresql+psycopg2://admin:admin@localhost/tweets_db')
session = sessionmaker(bind=engine)
session = session()

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), nullable=False)
    api_key = Column(String(50), nullable=False)
    followers = Column(ARRAY(Integer), nullable=True)
    following = Column(ARRAY(Integer), nullable=True)

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in
                self.__table__.columns}


class Tweets(Base):
    __tablename__ = 'tweets'

    id = Column(Integer, autoincrement=True, primary_key=True)
    content = Column(String(200), nullable=False)
    media_ids = Column(ARRAY(Integer), nullable=True)
    attachments = Column(ARRAY(String), nullable=True)
    author_id = Column(Integer, ForeignKey('users.id'))
    likes = Column(ARRAY(Integer), nullable=True)
    author = relationship("Users", backref=backref("tweets", cascade="all, delete-orphan", lazy="joined"))

    @hybrid_property
    def count_likes(self) -> int:
        return func.cardinality(self.likes)

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in
                self.__table__.columns}


class Media(Base):
    __tablename__ = 'media'

    id = Column(Integer, autoincrement=True, primary_key=True)
    filename = Column(String(50), nullable=False)
    upload_folder = Column(String(100), nullable=False)


def check_api_key():
    if 'api-key' in request.headers:
        api_key_in = request.headers['api-key']
        check_user_result = db.session.query(Users).where(Users.api_key == api_key_in).one_or_none()
        if check_user_result:
            return None, None, check_user_result
        else:
            error_type, error_message = "ValueError", "The user with the specified api_key was not found"
    else:
        error_type, error_message = "ValueError", "The value of the api-key header was not found"
    return error_type, error_message, None


def get_attachment(values_media_ids_in):
    lst_attachments_out = []
    if values_media_ids_in:
        if len(values_media_ids_in) >= 1:
            attachments_result = db.session.query(Media).where(Media.id.in_(values_media_ids_in)).all()
            lst_attachments_out = [os.path.join(i_attachment.upload_folder, i_attachment.filename)
                                   for i_attachment in attachments_result]
    return lst_attachments_out


def check_author_tweet(id_in):
    error_type, error_message, check_user_result_out = check_api_key()
    if not error_message:
        tweet_result = session.query(Tweets). \
            where(and_(Tweets.id == id_in, Tweets.author_id == check_user_result_out.id)).one_or_none()
        if not tweet_result:
            error_type, error_message = ("ValueError",
                                         "The tweet with the specified id was not found for this user")
    return error_type, error_message, check_user_result_out


def check_id_tweet(id_in):
    tweet_result_out = None
    error_type, error_message, check_user_result_out = check_api_key()
    if not error_message:
        tweet_result = db.session.query(Tweets).where(Tweets.id == id_in).one_or_none()
        if not tweet_result:
            error_type, error_message = ("ValueError",
                                         "The tweet with the specified id was not found for this user")
        else:
            tweet_result_out = tweet_result
    return error_type, error_message, check_user_result_out, tweet_result_out


def check_id_user(id_in):
    error_type, error_message, check_user_result_out = check_api_key()
    if not error_message:
        if id_in == check_user_result_out.id:
            error_type, error_message = ("ValueError",
                                         "Incorrect id")
    return error_type, error_message, check_user_result_out


def check_id_user_other(id_in, check_user_result_in):
    check_user_result_other_out = (db.session.query(Users).
                                   where(and_(Users.id == id_in, id != check_user_result_in.id)).one_or_none())
    if check_user_result_other_out:
        return None, None, check_user_result_other_out
    return "ValueError", "Incorrect id", None


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
