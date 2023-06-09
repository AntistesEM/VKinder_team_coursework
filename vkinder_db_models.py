import configparser
import os

import sqlalchemy as sq
from psycopg2 import Error
from sqlalchemy.orm import declarative_base, relationship, sessionmaker


def create_session():
    try:
        config = configparser.ConfigParser()
        config.read("settings.ini")
        os.environ["DSN"] = (
            f'{config["Database"]["sql_system"]}://'
            f'{config["Database"]["login"]}:'
            f'{config["Database"]["password"]}'
            f'@{config["Database"]["host"]}:'
            f'{config["Database"]["port"]}/'
            f'{config["Database"]["dbname"]}'
        )
        DSN = os.environ["DSN"]
        engine_ = sq.create_engine(DSN)
        Session = sessionmaker(bind=engine_)
        session_ = Session()
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
    return engine_, session_


Base = declarative_base()


class Parameters(Base):
    __tablename__ = 'Parameters'
    parameter_id = sq.Column(sq.Integer, primary_key=True)
    city = sq.Column(sq.String, nullable=True)
    sex = sq.Column(sq.String, nullable=True)
    age = sq.Column(sq.Integer, nullable=True)
    books = sq.Column(sq.String, nullable=True)
    music = sq.Column(sq.String, nullable=True)
    groups = sq.Column(sq.String, nullable=True)

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
    parameter_id = sq.Column(
        sq.Integer, sq.ForeignKey('Parameters.parameter_id'), nullable=False
    )

    parameters = relationship(Parameters, backref='users', cascade='all,delete')

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
    user_id = sq.Column(sq.Integer, sq.ForeignKey('Users.user_id'), nullable=True)
    photo_id = sq.Column(sq.Integer, sq.ForeignKey('Photos.photo_id'), nullable=True)

    user = relationship(
        Users,
        backref='user_photo',
        cascade='all,delete',
        single_parent=True
    )
    photo = relationship(
        Photos,
        backref='user_photo',
        cascade='all,delete',
        single_parent=True
    )

    def __str__(self):
        return f'''ID: {self.id} | User ID: {self.user_id} | Photo ID: {self.photo_id} | '''


def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


engine, session = create_session()

create_tables(engine)

query = (
    session.query(Users, Parameters, Photos)
    .join(Parameters)
    .join(UserPhoto)
    .join(Photos)
)

session.close()
