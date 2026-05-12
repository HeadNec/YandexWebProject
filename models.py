from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import db


class User(db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    avatar = Column(String(200), nullable=True)

    images = relationship('UserImage', backref='owner', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'


class UserImage(db.Model):
    __tablename__ = 'user_images'

    id = Column(Integer, primary_key=True)
    filename = Column(String(200), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<Image {self.filename}>'