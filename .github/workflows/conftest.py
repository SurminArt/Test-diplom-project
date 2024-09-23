import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask_app import create_app 
from models import Users, Tweets, Media, Base, engine, db as _db


@pytest.fixture
def app():
    _app = create_app()
    _app.config["TESTING"] = True
    _app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql+psycopg2://admin:admin@localhost/tweets_db'

    with _app.app_context():
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        objects = [
            Users(id=1, name='Artem', api_key='test'),
            Users(id=2, name='Ivan', api_key='test_i'),
            Tweets(content="Hello!", author_id=1),
            Tweets(content="Hi", author_id=2),
        ]
        _db.session.bulk_save_objects(objects)
        _db.session.commit()

        yield _app
        _db.session.close_all()
        Base.metadata.drop_all(engine)


@pytest.fixture
def client(app):
    client = app.test_client()
    yield client


@pytest.fixture
def db(app):
    with app.app_context():
        yield _db
