import json
from models import Users, Tweets


def test_add_tweet(client, db) -> None:
    client_data = {
        "tweet_data": "Hello",
    }
    resp = client.post("/api/tweets", data=json.dumps(client_data), headers={'Content-Type': 'application/json',
                                                                 'Accept': 'application/json', 'api-key': 'test'})
    result_tweet = db.session.query(Tweets).where(Tweets.id == 3).one_or_none()
    assert resp.json == {"result": True, "tweet_id": 3}
    assert result_tweet.author_id == 1
    assert len(db.session.query(Tweets).all()) == 3


def test_delete_tweet(client, db) -> None:
    client_data = {
        "tweet_data": "Good bye",
    }
    resp_add = client.post("/api/tweets", data=json.dumps(client_data), headers={'Content-Type': 'application/json',
                                                                             'Accept': 'application/json',
                                                                             'api-key': 'test'})
    count_tweet_before = db.session.query(Tweets).count()
    resp_delete = client.delete("/api/tweets/3", headers={'Content-Type': 'application/json',
                                                          'Accept': 'application/json', 'api-key': 'test'})
    count_tweet_after = db.session.query(Tweets).count()
    assert count_tweet_before - count_tweet_after == 1
    assert resp_delete.json["result"] is True


def test_add_likes(client, db) -> None:
    client_data = {
        "tweet_data": "Fine day",
    }
    resp_add_tweet = client.post("/api/tweets", data=json.dumps(client_data), headers={'Content-Type': 'application/json',
                                                                             'Accept': 'application/json',
                                                                             'api-key': 'test_i'})
    resp_add_like = client.post("/api/tweets/3/likes", headers={'Content-Type': 'application/json',
                                                                             'Accept': 'application/json',
                                                                             'api-key': 'test'})
    result_tweet = db.session.query(Tweets).where(Tweets.content == "Fine day").one_or_none()
    assert 1 in result_tweet.likes
    assert resp_add_like.json["result"] is True


def test_delete_tweet_alien(client, db) -> None:
    client_data = {
        "tweet_data": "How are you?",
    }
    resp_add = client.post("/api/tweets", data=json.dumps(client_data), headers={'Content-Type': 'application/json',
                                                                             'Accept': 'application/json',
                                                                             'api-key': 'test'})
    count_tweet_before = len(db.session.query(Tweets).all())
    resp_delete = client.delete("/api/tweets/3", headers={'Content-Type': 'application/json',
                                                          'Accept': 'application/json', 'api-key': 'test_i'})
    count_tweet_after = len(db.session.query(Tweets).all())
    assert count_tweet_before == count_tweet_after
    assert resp_delete.json["result"] is False


def test_add_likes_myself(client, db) -> None:
    client_data = {
        "tweet_data": "My tweet",
    }
    resp_add_tweet = client.post("/api/tweets", data=json.dumps(client_data),
                                 headers={'Content-Type': 'application/json',
                                          'Accept': 'application/json',
                                          'api-key': 'test'})
    resp_add_like = client.post("/api/tweets/3/likes",
                                headers={'Content-Type': 'application/json',
                                         'Accept': 'application/json',
                                         'api-key': 'test'})
    result_tweet = db.session.query(Tweets).where(Tweets.id == 3).one_or_none()
    assert result_tweet.likes == [] or result_tweet.likes is None
    assert resp_add_like.json["result"] is False
    assert resp_add_like.status_code == 400


def test_delete_like(client, db) -> None:
    client_data = {
        "tweet_data": "I like this tweet",
    }
    resp_add = client.post("/api/tweets", data=json.dumps(client_data), headers={'Content-Type': 'application/json',
                                                                             'Accept': 'application/json',
                                                                             'api-key': 'test'})
    resp_add_like = client.post("/api/tweets/3/likes",
                                headers={'Content-Type': 'application/json',
                                         'Accept': 'application/json',
                                         'api-key': 'test_i'})
    result_add_like = db.session.query(Tweets).where(Tweets.id == 3).one_or_none()
    count_like_before = len(result_add_like.likes)
    resp_delete = client.delete("/api/tweets/3/likes", headers={'Content-Type': 'application/json',
                                                          'Accept': 'application/json', 'api-key': 'test_i'})
    result_del_like = db.session.query(Tweets).where(Tweets.id == 3).one_or_none()
    count_like_after = len(result_del_like.likes)
    assert count_like_before - count_like_after == 1
    assert resp_delete.json["result"] is True


def test_delete_like_alien(client, db) -> None:
    client_data = {
        "tweet_data": "I like this tweet",
    }
    resp_add = client.post("/api/tweets", data=json.dumps(client_data), headers={'Content-Type': 'application/json',
                                                                             'Accept': 'application/json',
                                                                             'api-key': 'test'})
    resp_add_like = client.post("/api/tweets/3/likes",
                                headers={'Content-Type': 'application/json',
                                         'Accept': 'application/json',
                                         'api-key': 'test_i'})
    result_add_like = db.session.query(Tweets).where(Tweets.id == 3).one_or_none()
    count_like_before = len(result_add_like.likes)
    resp_delete = client.delete("/api/tweets/3/likes", headers={'Content-Type': 'application/json',
                                                          'Accept': 'application/json', 'api-key': 'test'})
    result_del_like = db.session.query(Tweets).where(Tweets.id == 3).one_or_none()
    count_like_after = len(result_del_like.likes)
    assert count_like_before == count_like_after
    assert resp_delete.json["result"] is False
    assert resp_delete.status_code == 400


def test_add_user_follow(client, db) -> None:
    resp_add_follow = client.post("/api/users/2/follow",
                                headers={'Content-Type': 'application/json',
                                         'Accept': 'application/json',
                                         'api-key': 'test'})
    result_user_test = db.session.query(Users).where(Users.api_key == 'test').one_or_none()
    result_user_test_i = db.session.query(Users).where(Users.id == 2).one_or_none()
    assert 2 in result_user_test.following
    assert 1 in result_user_test_i.followers
    assert resp_add_follow.json["result"] is True
    assert resp_add_follow.status_code == 200


def test_add_user_follow_myself(client, db) -> None:
    result_user_test_before = db.session.query(Users).where(Users.api_key == 'test').one_or_none()
    resp_add_follow = client.post("/api/users/1/follow",
                                headers={'Content-Type': 'application/json',
                                         'Accept': 'application/json',
                                         'api-key': 'test'})
    result_user_test_after = db.session.query(Users).where(Users.api_key == 'test').one_or_none()
    assert result_user_test_before == result_user_test_after
    assert resp_add_follow.json == {"result": False, "error_type": "ValueError", "error_message": "Incorrect id"}
    assert resp_add_follow.status_code == 400


def test_delete_user_follow(client, db) -> None:
    count_user_test_following_after, count_user2_followers_after = 0, 0
    resp_add_follow = client.post("/api/users/2/follow",
                                  headers={'Content-Type': 'application/json',
                                           'Accept': 'application/json',
                                           'api-key': 'test'})
    result_user_test_before = db.session.query(Users).where(Users.api_key == 'test').one_or_none()
    count_user_test_following_before = len(result_user_test_before.following)
    result_user2_before = db.session.query(Users).where(Users.id == 2).one_or_none()
    count_user2_followers_before = len(result_user2_before.followers)
    resp_del_follow = client.delete("/api/users/2/follow",
                                  headers={'Content-Type': 'application/json',
                                           'Accept': 'application/json',
                                           'api-key': 'test'})
    result_user_test_after = db.session.query(Users).where(Users.api_key == 'test').one_or_none()
    result_user2_after = db.session.query(Users).where(Users.id == 2).one_or_none()
    if result_user_test_after.following:
        count_user_test_following_after = len(result_user_test_after.following)
    if result_user_test_after.followers:
        count_user2_followers_after = len(result_user2_after.followers)
    assert count_user_test_following_before - count_user_test_following_after == 1
    assert count_user2_followers_before - count_user2_followers_after == 1
    assert resp_del_follow.json["result"] is True
    assert resp_del_follow.status_code == 200


def test_get_tweets(client, db) -> None:
    result_user_test = db.session.query(Users).where(Users.api_key == 'test').one_or_none()
    client_data = {
        "tweet_data": "Good luck",
    }
    resp_add_tweet_user_test = client.post("/api/tweets", data=json.dumps(client_data), headers={'Content-Type': 'application/json',
                                                                             'Accept': 'application/json',
                                                                             'api-key': 'test'})
    resp_add_follow = client.post("/api/users/2/follow",
                                  headers={'Content-Type': 'application/json',
                                           'Accept': 'application/json',
                                           'api-key': 'test'})
    client_data = {
        "tweet_data": "Good bye",
    }
    resp_add_tweet_user2 = client.post("/api/tweets", data=json.dumps(client_data),
                                           headers={'Content-Type': 'application/json',
                                                    'Accept': 'application/json',
                                                    'api-key': 'test_i'})
    res_tweets = client.get("/api/tweets", headers={'Content-Type': 'application/json',
                                                        'Accept': 'application/json',
                                                        'api-key': 'test'})

    assert res_tweets.json['result'] is True
    assert len(res_tweets.json['tweets']) == 4
    assert res_tweets.json['tweets'][2]['content'] in ['Good luck', 'Good bye']
    assert res_tweets.json['tweets'][3]['content'] in ['Good luck', 'Good bye']
    assert res_tweets.json['tweets'][2]['author']['id'] in [2, 1]
    assert res_tweets.json['tweets'][3]['author']['id'] in [2, 1]


def test_get_my_profile(client, db) -> None:
    res_user_test = db.session.query(Users).where(Users.api_key == 'test').one_or_none()
    resp_add_follow = client.post("/api/users/2/follow",
                                  headers={'Content-Type': 'application/json',
                                           'Accept': 'application/json',
                                           'api-key': 'test'})
    resp_my_profile = client.get('/api/users/me',
                                 headers={'Content-Type': 'application/json',
                                          'Accept': 'application/json',
                                          'api-key': 'test'})
    assert resp_my_profile.json['result'] is True
    assert resp_my_profile.status_code == 200
    assert resp_my_profile.json['user']['id'] == 1
    assert resp_my_profile.json['user']['name'] == 'Artem'
    assert resp_my_profile.json['user']['following'][0]['id'] in res_user_test.following


def test_get_user_profile(client, db) -> None:
    res_user_test = db.session.query(Users).where(Users.api_key == 'test').one_or_none()
    res_user_test_i = db.session.query(Users).where(Users.api_key == 'test_i').one_or_none()
    resp_add_follow = client.post("/api/users/1/follow",
                                  headers={'Content-Type': 'application/json',
                                           'Accept': 'application/json',
                                           'api-key': 'test_i'})
    resp_user_profile = client.get('/api/users/2',
                                 headers={'Content-Type': 'application/json',
                                          'Accept': 'application/json',
                                          'api-key': 'test'})
    assert resp_user_profile.json['result'] is True
    assert resp_user_profile.status_code == 200
    assert resp_user_profile.json['user']['id'] == 2
    assert resp_user_profile.json['user']['name'] == 'Ivan'
    assert resp_user_profile.json['user']['following'][0]['id'] in res_user_test_i.following
