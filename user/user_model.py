import uuid

from flask_mongoengine import Document
from mongoengine import StringField

class User(Document):
    user_id = StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    email = StringField(require=True, unique=True)
    user_name = StringField(require=True, unique=True)
    password = StringField(required=True)
    role = StringField(default='user')

    meta = {
        'collection': 'users'
    }
