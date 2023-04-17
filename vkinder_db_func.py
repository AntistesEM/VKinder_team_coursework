import os
import psycopg2
import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker
from config import login, password, db_name
from vkinder_db_models import Users, Parameters, Photos, UserPhoto

os.environ['DSN'] = f'postgresql://{login}:{password}@localhost:5432/{db_name}'
DSN = os.environ['DSN']
engine = sq.create_engine(DSN)
Session = sessionmaker(bind=engine)
session = Session()


def add_parameters(country, region, city, sex, age_from, age_to):
    new_user_params = Parameters(
        country=country,
        region=region,
        city=city,
        sex=sex,
        age_from=age_from,
        age_to=age_to
    )
    session.add(new_user_params)
    session.commit()
    id_parameter = new_user_params.parameter_id
    return id_parameter


def add_user(user_id, first_name, last_name, profile_link, favorite, block, id_parameter):
    new_user = Users(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        profile_link=profile_link,
        favorite=favorite,
        block=block,
        parameter_id=id_parameter
    )
    session.add(new_user)
    session.commit()
    id_u = new_user.user_id
    return id_u


def add_photo(id_u, photo_link, likes):
    new_photo = Photos(
        photo_link=photo_link,
        likes=likes
    )
    session.add(new_photo)
    session.commit()
    id_photo = new_photo.photo_id

    new_user_photo = UserPhoto(
        user_id=id_u,
        photo_id=id_photo
    )
    session.add_all(new_user_photo)
    session.commit()


session.close()

conn = psycopg2.connect(database=db_name, user=login, password=password)


def add_to_selected(user_id):
    with conn.cursor() as cur:
        cur.execute('''
        UPDATE "users" SET favorite=%s WHERE "user".user_id = %s;
        ''', (True, user_id))
        conn.commit()


def add_to_block(user_id):
    with conn.cursor() as cur:
        cur.execute('''
        UPDATE "users" SET block=%s WHERE "user".user_id = %s;
        ''', (True, user_id))
        conn.commit()


def favorite_list(parameter_id):
    with conn.cursor() as cur:
        cur.execute('''
            SELECT u.first_name, u.last_name, u.profile_link FROM "users" u
            JOIN "parameters" p ON u.parameter_id=p.parameter_id
            WHERE favorite = %s AND p.parameter_id = %s;
            ''', (True, parameter_id))
        favorites_list = cur.fetchall()
        return favorites_list


def block_list(parameter_id):
    with conn.cursor() as cur:
        cur.execute('''
            SELECT u.first_name, u.last_name, u.profile_link FROM "users" u
            JOIN "parameters" p ON u.parameter_id=p.parameter_id
            WHERE block = %s AND p.parameter_id = %s;
            ''', (True, parameter_id))
        blocked_list = cur.fetchall()
        return blocked_list
