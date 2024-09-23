from marshmallow import Schema, fields


class ResponseTweetTrue(Schema):
    result = fields.Boolean(metadata={'result': True})
    tweet_id = fields.Integer()


class ResponseMediaTrue(Schema):
    result = fields.Boolean(metadata={'result': True})
    media_id = fields.Integer()


class ResponseTrue(Schema):
    result = fields.Boolean(metadata={'result': True})


class ResponseFalse(Schema):
    result = fields.Boolean(metadata={'result': False})
    error_type = fields.String()
    error_message = fields.String()


class ProfileUserAdditional(Schema):
    id = fields.Integer()
    name = fields.String()


class ParamUser(Schema):
    id = fields.Integer()
    name = fields.String()
    followers = fields.List(fields.Nested(ProfileUserAdditional()))
    following = fields.List(fields.Nested(ProfileUserAdditional()))


class ParamTweet(Schema):
    id = fields.Integer(dump_only=True)
    content = fields.String()
    attachments = fields.List(fields.String())
    author = fields.Nested(ProfileUserAdditional())
    likes = fields.List(fields.Nested(ProfileUserAdditional()))


class ResponseUser(Schema):
    result = fields.Boolean(metadata={'result': True})
    user = fields.Nested(ParamUser())


class ResponseTweets(Schema):
    result = fields.Boolean(metadata={'result': True})
    tweets = fields.List(fields.Nested(ParamTweet()))
