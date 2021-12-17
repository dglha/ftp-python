import sqlalchemy as db
from sqlalchemy.orm import sessionmaker
import bcrypt

from Model.User import User

engine = db.create_engine("sqlite:///fpt_implement.sqlite", echo=True, connect_args={'check_same_thread': False})
connection = engine.connect()
DBSession = sessionmaker(bind=engine)
session = DBSession()


def create_user(username, password, is_write, is_delete):
    pass_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(10))
    u = User(username=username, password=pass_hash, is_write=is_write, is_delete=is_delete)
    session.add(u)
    session.commit()
    return True


def check_user(username, password) -> (bool, User):
    user = session.query(User).filter_by(username=username).first()
    if not user:
        return False, None
    check = bcrypt.checkpw(password.encode(), user.password)
    if not check:
        return False, None
    return True, user


def get_user(user_id):
    # user = session.query(User).filter_by(id=user_id).first()
    user = session.query(User).filter_by(id=user_id).first()
    print(user)
    # if not user:
    #     return False, None
    return True, user


def update_user(id, is_write, is_delete):
    try:
        user = session.query(User).filter_by(id=id).first()
        user.is_write = is_write
        user.is_delete = is_delete
        # if password:
        #     user.password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        # session.add(user)
        session.commit()
    except Exception as e:
        print(e)
        return False
    return True


def delete_user(user_id):
    try:
        session.query(User).filter_by(id=user_id).delete()
    except Exception as e:
        session.rollback()
        return False

    session.commit()
    return True


def get_all_user():
    try:
        users = session.query(User).all()
    except Exception as e:
        print(e)
        return []
    return users


class UserWorker:
    pass
