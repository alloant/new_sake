from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.DB_URL, pool_size=30, max_overflow=30, pool_timeout=30, echo=settings.DB_ECHO, future=True)
SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_db():
    with SessionLocal() as session:
        yield session

## This part is just to copy old data to the new db
import pymysql.cursors

# Connection settings
conn = pymysql.connect(
    host='localhost',
    port=3306,
    user='root',
    password=settings.DB_URL_OLD_PASS,
    database='sake2',
    cursorclass=pymysql.cursors.DictCursor,  # optional: return rows as dicts
    autocommit=True                         # optional: enable autocommit
)


def get_old_data(sql):
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            return rows
    finally:
        pass
    #    conn.close()
