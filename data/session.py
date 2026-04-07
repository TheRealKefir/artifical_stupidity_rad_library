from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import DeclarativeBase


db_path = '../db/database.db'
DB_URL = f'sqlite:///{db_path}?check_same_thread=False'
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass



def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()
