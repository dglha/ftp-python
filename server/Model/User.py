from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    # Fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    is_write = Column(Integer, nullable=False)
    is_delete = Column(Integer, nullable=False)

    def __repr__(self):
        return f"[USER] {self.username}"
