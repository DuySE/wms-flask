import uuid

from mongoengine import Document, StringField

class User(Document):
    user_id = StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    email = StringField(required=True, unique=True)
    user_name = StringField(required=True, unique=True)
    password = StringField(required=True)
    role = StringField(default='user')

    meta = {
        'collection': 'users'
    }