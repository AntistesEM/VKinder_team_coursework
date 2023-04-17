import sqlalchemy as sq
import os
from sqlalchemy.orm import declarative_base, relationship
from config import login, password, db_name

os.environ['DSN'] = f'postgresql://{login}:{password}@localhost:5432/{db_name}'
DSN = os.environ['DSN']
engine = sq.create_engine(DSN)

Base = declarative_base()


class Parameters(Base):
    __tablename__ = 'Parameters'
    parameter_id = sq.Column(sq.Integer, primary_key=True)
    country = sq.Column(sq.String, nullable=False)
    region = sq.Column(sq.String, nullable=False)
    city = sq.Column(sq.String, nullable=False)
    sex = sq.Column(sq.String, nullable=False)
    age_from = sq.Column(sq.Integer, nullable=False)
    age_to = sq.Column(sq.Integer, nullable=False)

    def __str__(self):
        return f'''Рarameter ID: {self.parameter_id} | Сountry: {self.country} | Region: {self.region} |  City: {self.city} | Sex: {self.sex} | Age from: {self.age_from} | Age to: {self.age_to} | '''


class Users(Base):
    __tablename__ = 'Users'
    user_id = sq.Column(sq.Integer, primary_key=True)
    first_name = sq.Column(sq.String, nullable=False)
    last_name = sq.Column(sq.String, nullable=False)
    profile_link = sq.Column(sq.String, nullable=False)
    favorite = sq.Column(sq.Boolean, default=False)
    block = sq.Column(sq.Boolean, default=False)
    parameter_id = sq.Column(sq.Integer, sq.ForeignKey('Parameters.parameter_id'), nullable=False)

    parameters = relationship(Parameters, backref='users', cascade='save-update, merge, delete')

    def __str__(self):
        return f'''User ID: {self.user_id} | Name: {self.first_name} | Surname: {self.last_name} |  Link: {self.profile_link} | Favorite: {self.favorite} | Block: {self.block} | Parameter ID: {self.parameter_id} | '''


class Photos(Base):
    __tablename__ = 'Photos'
    photo_id = sq.Column(sq.Integer, primary_key=True)
    photo_link = sq.Column(sq.String, nullable=False)
    likes = sq.Column(sq.Integer)

    def __str__(self):
        return f'''Photo ID: {self.photo_id} | Photo link: {self.photo_link} | Likes: {self.likes} | '''


class UserPhoto(Base):
    __tablename__ = 'User_Photo'
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey('Users.user_id'), nullable=False)
    photo_id = sq.Column(sq.Integer, sq.ForeignKey('Photos.photo_id'), nullable=False)

    user = relationship(Users, backref='user_photo', cascade='save-update, merge, delete')
    photo = relationship(Photos, backref='user_photo', cascade='save-update, merge, delete')

    def __str__(self):
        return f'''ID: {self.id} | User ID: {self.user_id} | Photo ID: {self.photo_id} | '''


def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
