import os
from werkzeug.utils import secure_filename
from sqlalchemy import create_engine, delete, update, desc, func, or_, and_

from flask import Flask, request, render_template, send_from_directory
from diplom_project.main.models import Tweets, Users, Media, Base
from sqlalchemy.dialects.postgresql import insert
from psycopg2 import OperationalError, InterfaceError, DatabaseError, DataError, IntegrityError, InternalError, \
    ProgrammingError, NotSupportedError
from diplom_project.main.config import (TEMPLATE_FOLDER, JS_DIRECTORY, CSS_DIRECTORY,
                                        IMAGES_DIRECTORY, UPLOAD_FOLDER)
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from flasgger import APISpec, Swagger, swag_from
from diplom_project.main.schemas import (ResponseTweets, ResponseTweetTrue, ResponseMediaTrue, ResponseTrue,
                                         ResponseFalse, ResponseUser)
from diplom_project.main.models import (engine, session, db, Base, check_api_key, check_id_user_other, check_id_user,
                                        check_id_tweet, check_author_tweet, allowed_file, get_attachment)


def create_app():

    app = Flask(__name__, template_folder=TEMPLATE_FOLDER)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql+psycopg2://admin:admin@localhost/tweets_db'
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    spec = APISpec(
        title='Tweets and Users',
        version='1.0.0',
        openapi_version='2.0',
        plugins=[
            FlaskPlugin(),
            MarshmallowPlugin(),
        ],
    )
    template = spec.to_flasgger(
        app,
        definitions=[ResponseTweetTrue, ResponseMediaTrue, ResponseTrue, ResponseFalse, ResponseUser,
                     ResponseTweets]
    )
    swagger = Swagger(app, template=template)

    db.init_app(app)

    def before_request_func():
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

        objects = [
            Users(id=1, name='Artem', api_key='test'),
            Users(id=2, name='Ivan', api_key='test_i'),
            Tweets(content="Hello!", author_id=1),
            Tweets(content="Hi", author_id=2),
        ]
        session.bulk_save_objects(objects)
        session.commit()

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/js/<path:path>")
    def send_js(path):
        return send_from_directory(JS_DIRECTORY, path)

    @app.route("/css/<path:path>")
    def send_css(path):
        return send_from_directory(CSS_DIRECTORY, path)

    @app.route("/images/<path:path>")
    def send_images(path):
        return send_from_directory(IMAGES_DIRECTORY, path)

    @app.route('/api/tweets', methods=['POST'])
    @swag_from('spec/post_add_tweet.yml')
    def add_tweet_handler():
        content_tweet = request.json.get('tweet_data')
        if not isinstance(content_tweet, str):
            return {"result": False, "error_type": "TypeError", "error_message": "Invalid data type"}, 400
        values_media_ids = request.json.get('tweet_media_ids')
        try:
            error_type, error_message, check_user_result = check_api_key()
            if not error_message:
                lst_attachments = get_attachment(values_media_ids)
                add_tweet = db.session.execute(insert(Tweets).
                                            returning(Tweets.id).
                                            values(content=content_tweet,
                                                   attachments=lst_attachments,
                                                   media_ids=values_media_ids,
                                                   author_id=check_user_result.id))
                db.session.commit()
                add_result = add_tweet.fetchone()
                if add_result:
                    return {"result": True, "tweet_id": add_result[0]}, 200
            return {"result": False, "error_type": error_type, "error_message": error_message}, 400
        except (OperationalError, InterfaceError, DatabaseError, DataError, IntegrityError, InternalError,
                ProgrammingError, NotSupportedError) as exc:
            return {"result": False, "error_type": type(exc), "error_message": exc}, 400

    @app.route('/api/medias', methods=['POST'])
    @swag_from('spec/post_upload_media.yml')
    def upload_file_handler():
        file = request.files['file']
        try:
            error_type, error_message, check_user_result = check_api_key()
            if not error_message:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    with engine.connect() as connection_:
                        add_filename = connection_.execute(insert(Media).returning(Media.id).
                                                           values(filename=filename, upload_folder=UPLOAD_FOLDER))
                        connection_.commit()
                    filename_id = add_filename.fetchone()
                    if filename_id:
                        return {"result": True, "media_id": filename_id[0]}, 200
                else:
                    error_type, error_message = "ValueError", "Invalid file name or extension"
            return {"result": False, "error_type": error_type, "error_message": error_message}, 400
        except Exception as exc:
            return {"result": False, "error_type": type(exc), "error_message": exc}, 400

    @app.route('/api/tweets/<int:id>', methods=['DELETE'])
    @swag_from('spec/delete_tweet.yml')
    def delete_tweet_handler(id: int):
        try:
            error_type, error_message, check_user_result = check_author_tweet(id)
            if not error_message:
                result = delete(Tweets).returning(Tweets.id). \
                    where(and_(Tweets.id == id and Tweets.author_id == check_user_result.id))
                deleted_row = db.session.execute(result).fetchone()
                db.session.commit()
                if deleted_row:
                    return {"result": True}, 200
            return {"result": False, "error_type": error_type, "error_message": error_message}, 400
        except (OperationalError, InterfaceError, DatabaseError, DataError, IntegrityError, InternalError,
                ProgrammingError, NotSupportedError) as exc:
            return {"result": False, "error_type": type(exc), "error_message": exc}, 400

    @app.route('/api/tweets/<int:id>/likes', methods=['DELETE'])
    @swag_from('spec/delete_like.yml')
    def delete_likes_tweet_handler(id: int):
        try:
            error_type, error_message, check_user_result, tweet_result = check_id_tweet(id)
            if not error_message:
                if tweet_result:
                    if check_user_result.id in tweet_result.likes:
                        lst_tweet_likes = tweet_result.likes
                        lst_tweet_likes.remove(check_user_result.id)
                        result = update(Tweets). \
                            where(Tweets.id == id).values(likes=lst_tweet_likes)
                        db.session.execute(result)
                        db.session.commit()
                        return {"result": True}, 200
            return {"result": False, "error_type": error_type, "error_message": error_message}, 400
        except (OperationalError, InterfaceError, DatabaseError, DataError, IntegrityError, InternalError,
                ProgrammingError, NotSupportedError) as exc:
            return {"result": False, "error_type": type(exc), "error_message": exc}, 400

    @app.route('/api/tweets/<int:id>/likes', methods=['POST'])
    @swag_from('spec/post_add_like.yml')
    def set_likes_tweet_handler(id: int):
        try:
            error_type, error_message, check_user_result, tweet_result = check_id_tweet(id)
            if not error_message:
                if tweet_result:
                    if tweet_result.author_id != check_user_result.id:
                        if tweet_result.likes is None:
                            tweet_result.likes = []
                        lst_likes = tweet_result.likes
                        lst_likes.append(check_user_result.id)
                        tweet_result.likes = lst_likes
                        tweets_update_likes = update(Tweets).where(Tweets.id == id).values(likes=lst_likes)
                        db.session.execute(tweets_update_likes)
                        db.session.commit()
                        return {"result": True}, 200
                    else:
                        error_type, error_message = "ValueError", "Incorrect id"
                else:
                    error_type, error_message = ("ValueError",
                                                 "The tweet with the specified id was not found for this user")
            return {"result": False, "error_type": error_type, "error_message": error_message}, 400
        except (OperationalError, InterfaceError, DatabaseError, DataError, IntegrityError, InternalError,
                ProgrammingError, NotSupportedError) as exc:
            return {"result": False, "error_type": type(exc), "error_message": exc.messages}, 400

    @app.route('/api/users/<int:id>/follow', methods=['POST'])
    @swag_from('spec/post_add_follow.yml')
    def set_follow_user_handler(id: int):
        try:
            error_type, error_message, check_user_result = check_id_user(id)
            if not error_message:
                error_type, error_message,check_user_result_other = check_id_user_other(id, check_user_result)
                if check_user_result_other:
                    if check_user_result_other.followers is None:
                        check_user_result_other.followers = []
                    if check_user_result.following is None:
                        check_user_result.following = []
                    if check_user_result.id not in check_user_result_other.followers \
                            and id not in check_user_result.following:
                        lst_following = check_user_result.following
                        lst_following.append(id)
                        user_result_following_update = (update(Users).where(Users.id == check_user_result.id).
                                                        values(following=lst_following))
                        db.session.execute(user_result_following_update)
                        lst_followers = check_user_result_other.followers
                        lst_followers.append(check_user_result.id)
                        user_result_followers_update = (update(Users).where(Users.id == id).
                                                        values(followers=lst_followers))
                        db.session.execute(user_result_followers_update)
                        db.session.commit()
                        return {"result": True}, 200
                    else:
                        error_type, error_message = "ValueError", \
                            "The user with the specified id is already in the list of followers or followings"
            return {"result": False, "error_type": error_type, "error_message": error_message}, 400
        except (OperationalError, InterfaceError, DatabaseError, DataError, IntegrityError, InternalError,
                ProgrammingError, NotSupportedError) as exc:
            return {"result": False, "error_type": type(exc), "error_message": exc.messages}, 400

    @app.route('/api/users/<int:id>/follow', methods=['DELETE'])
    @swag_from('spec/delete_follow.yml')
    def delete_follow_user_handler(id: int):
        try:
            error_type, error_message, check_user_result = check_id_user(id)
            if not error_message:
                error_type, error_message, check_user_result_other = check_id_user_other(id, check_user_result)
                if check_user_result_other:
                    if check_user_result_other.followers and check_user_result.following:
                        if check_user_result.id in check_user_result_other.followers \
                                and id in check_user_result.following:
                            lst_users_following = check_user_result.following
                            lst_users_following.remove(id)
                            user_result_following_del = update(Users).where(Users.id == check_user_result.id).values(
                                following=lst_users_following)
                            db.session.execute(user_result_following_del)
                            lst_users_followers = check_user_result_other.followers
                            lst_users_followers.remove(check_user_result.id)
                            user_result_followers_del = (update(Users).where(Users.id == id).
                                                         values(followers=lst_users_followers))
                            db.session.execute(user_result_followers_del)
                            db.session.commit()
                            return {"result": True}, 200
                    else:
                        error_type, error_message = ("ValueError",
                                                     "Deletion error: lists of followers and following are empty")
            return {"result": False, "error_type": error_type, "error_message": error_message}, 400
        except (OperationalError, InterfaceError, DatabaseError, DataError, IntegrityError, InternalError,
                ProgrammingError, NotSupportedError) as exc:
            return {"result": False, "error_type": type(exc), "error_message": exc.messages}, 400

    @app.route('/api/tweets', methods=['GET'])
    @swag_from('spec/get_tweets.yml')
    def tweets_user_handler():
        try:
            error_type, error_message, check_user_result = check_api_key()
            if not error_message:
                if check_user_result.following:
                    result_tweets_likes_following = (db.session.query(Tweets).
                                                     where(and_(Tweets.likes != [],
                                                                Tweets.likes is not None,
                                                                Tweets.author_id.not_in(check_user_result.following))).
                                                     all())
                    lst_tweets_likes_following = [i_tweet for i_tweet in result_tweets_likes_following
                                                  if list(set(i_tweet.likes) & set(check_user_result.following)) != []]
                    result_tweets = (db.session.query(Tweets).
                                     where(or_(Tweets.author_id.in_(check_user_result.following),
                                               Tweets.author_id == check_user_result.id)).
                                     order_by(desc(func.cardinality(Tweets.likes))).all())
                    if lst_tweets_likes_following:
                        result_tweets.extend(lst_tweets_likes_following)
                else:
                    result_tweets = (db.session.query(Tweets).where(Tweets.author_id == check_user_result.id).
                                     order_by(desc(func.cardinality(Tweets.likes))).all())
                lst_tweets = []
                for tweet in result_tweets:
                    name_author = db.session.query(Users).where(Users.id == tweet.author_id).one_or_none()
                    if tweet.likes:
                        names_users = db.session.query(Users).where(Users.id.in_(tweet.likes)).all()
                    else:
                        names_users = []
                    if names_users:
                        lst_likes = [{"user_id": tweet.likes[i], "name": names_users[i].name}
                                     for i in range(len(tweet.likes))]
                    else:
                        lst_likes = []
                    dct_tweet = {"id": tweet.id,
                                 "content": tweet.content,
                                 "attachment": tweet.attachments,
                                 "author": {"id": tweet.author_id, "name": name_author.name},
                                 "likes": lst_likes}
                    lst_tweets.append(dct_tweet)
                return {"result": True, "tweets": lst_tweets}, 200
            return {"result": False, "error_type": error_type, "error_message": error_message}, 400
        except (OperationalError, InterfaceError, DatabaseError, DataError, IntegrityError, InternalError,
                ProgrammingError, NotSupportedError) as exc:
            return {"result": False, "error_type": type(exc), "error_message": exc.messages}, 400

    @app.route('/api/users/me', methods=['GET'])
    @swag_from('spec/get_profile_me.yml')
    def profile_me_handler():
        try:
            error_type, error_message, check_user_result = check_api_key()
            if not error_message:
                if check_user_result.followers:
                    names_followers = db.session.query(Users).where(Users.id.in_(check_user_result.followers)).all()
                    ids_followers = [id_follower for id_follower in check_user_result.followers]
                    lst_followers = [{"id": ids_followers[i], "name": names_followers[i].name}
                                     for i in range(len(ids_followers))]
                else:
                    lst_followers = []
                if check_user_result.following:
                    names_following = db.session.query(Users).where(Users.id.in_(check_user_result.following)).all()
                    ids_following = [id_following for id_following in check_user_result.following]
                    lst_following = [{"id": ids_following[i], "name": names_following[i].name}
                                     for i in range(len(ids_following))]
                else:
                    lst_following = []
                profile_me_result = {"result": True,
                                     "user": {"id": check_user_result.id,
                                              "name": check_user_result.name,
                                              "followers": lst_followers,
                                              "following": lst_following}}

                return profile_me_result, 200
            return {"result": False, "error_type": error_type, "error_message": error_message}, 400
        except (OperationalError, InterfaceError, DatabaseError, DataError, IntegrityError, InternalError,
                ProgrammingError, NotSupportedError) as exc:
            return {"result": False, "error_type": type(exc), "error_message": exc.messages}, 400

    @app.route('/api/users/<int:id>', methods=['GET'])
    @swag_from('spec/get_profile_user.yml')
    def profile_user_handler(id: int):
        try:
            error_type, error_message, check_user_result = check_api_key()
            if not error_message:
                error_type, error_message, profile_user = check_id_user(id)
                if profile_user:
                    if profile_user.followers:
                        names_followers = db.session.query(Users).where(Users.id.in_(profile_user.followers)).all()
                        ids_followers = [id_follower for id_follower in profile_user.followers]
                        lst_followers = [{"id": ids_followers[i], "name": names_followers[i].name}
                                         for i in range(len(ids_followers))]
                    else:
                        lst_followers = []
                    if profile_user.following:
                        names_following = db.session.query(Users).where(Users.id.in_(profile_user.following)).all()
                        ids_following = [id_following for id_following in profile_user.following]
                        lst_following = [{"id": ids_following[i], "name": names_following[i].name}
                                         for i in range(len(ids_following))]
                    else:
                        lst_following = []
                    profile_me_result = {"result": True,
                                         "user": {"id": profile_user.id,
                                                  "name": profile_user.name,
                                                  "followers": lst_followers,
                                                  "following": lst_following}}

                    return profile_me_result, 200
            return {"result": False, "error_type": error_type, "error_message": error_message}, 400
        except (OperationalError, InterfaceError, DatabaseError, DataError, IntegrityError, InternalError,
                ProgrammingError, NotSupportedError) as exc:
            return {"result": False, "error_type": type(exc), "error_message": exc.messages}, 400
#    before_request_func()
    return app
