import vk_api
from vk_api.longpoll import VkLongPoll
from vk_config import group_token
from random import randrange
import sqlalchemy as sq
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, InvalidRequestError


Base = declarative_base()


engine = sq.create_engine('postgresql://user@localhost:5432/vkinder_db',
                          client_encoding='utf8')
Session = sessionmaker(bind=engine)


vk = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk)
session = Session()
connection = engine.connect()


class User(Base):
    __tablename__ = 'user'
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    vk_id = sq.Column(sq.Integer, unique=True)


class DatingUser(Base):
    __tablename__ = 'dating_user'
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    vk_id = sq.Column(sq.Integer, unique=True)
    id_user = sq.Column(sq.Integer, sq.ForeignKey('user.id', ondelete='CASCADE'))


class BlackList(Base):
    __tablename__ = 'black_list'
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    vk_id = sq.Column(sq.Integer, unique=True)
    id_user = sq.Column(sq.Integer, sq.ForeignKey('user.id', ondelete='CASCADE'))


""" 
ФУНКЦИИ РАБОТЫ С БД
"""


def delete_db_blacklist(ids):
    current_user = session.query(BlackList).filter_by(vk_id=ids).first()
    session.delete(current_user)
    session.commit()


def delete_db_favorites(ids):
    current_user = session.query(DatingUser).filter_by(vk_id=ids).first()
    session.delete(current_user)
    session.commit()


def check_db_master(ids):
    current_user_id = session.query(User).filter_by(vk_id=ids).first()
    return current_user_id


def check_db_user(ids):
    dating_user = session.query(DatingUser).filter_by(
        vk_id=ids).first()
    blocked_user = session.query(BlackList).filter_by(
        vk_id=ids).first()
    return dating_user, blocked_user


def check_db_black(ids):
    current_users_id = session.query(User).filter_by(vk_id=ids).first()
    all_users = session.query(BlackList).filter_by(id_user=current_users_id.id).all()
    return all_users


def check_db_favorites(ids):
    current_users_id = session.query(User).filter_by(vk_id=ids).first()
    alls_users = session.query(DatingUser).filter_by(id_user=current_users_id.id).all()
    return alls_users


def write_msg(user_id, message, attachment=None):
    vk.method('messages.send',
              {'user_id': user_id,
               'message': message,
               'random_id': randrange(10 ** 7),
               'attachment': attachment})


def register_user(vk_id):
    try:
        new_user = User(
            vk_id=vk_id
        )
        session.add(new_user)
        session.commit()
        return True
    except (IntegrityError, InvalidRequestError):
        return False


def add_user(event_id, vk_id, id_user):
    try:
        new_user = DatingUser(
            vk_id=vk_id,
            id_user=id_user
        )
        session.add(new_user)
        session.commit()
        write_msg(event_id,
                  'ПОЛЬЗОВАТЕЛЬ УСПЕШНО ДОБАВЛЕН В ИЗБРАННОЕ')
        return True
    except (IntegrityError, InvalidRequestError):
        write_msg(event_id,
                  'Пользователь уже в избранном.')
        return False


def add_to_black_list(event_id, vk_id, id_user):
    try:
        new_user = BlackList(
            vk_id=vk_id,
            id_user=id_user
        )
        session.add(new_user)
        session.commit()
        write_msg(event_id,
                  'Пользователь успешно заблокирован.')
        return True
    except (IntegrityError, InvalidRequestError):
        write_msg(event_id,
                  'Пользователь уже в черном списке.')
        return False


if __name__ == '__main__':
    Base.metadata.create_all(engine)