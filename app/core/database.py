from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

#engine = create_engine(settings.DB_URL, pool_size=30, max_overflow=30, pool_timeout=30, echo=settings.DB_ECHO, future=True)
engine = create_engine(
    settings.DB_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    # This helps reclaim connections that have been sitting idle too long
    pool_recycle=3600,
    # This checks if a connection is still alive before giving it to you
    pool_pre_ping=True,
    echo=settings.DB_ECHO,
    future=True
    )

SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_db():
    #with SessionLocal() as session:
    #    yield session
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close() # Explicitly ensure it returns to the pool


def get_old_data(sql):
    ## This part is just to copy old data to the new db
    import pymysql.cursors

    # Connection settings
    conn = pymysql.connect(
        host=settings.DB_URL_HOST_OLD,
        port=settings.DB_URL_PORT_OLD,
        user=settings.DB_URL_USER_OLD,
        password=settings.DB_URL_PASS_OLD,
        database=settings.DB_URL_DB_OLD,
        cursorclass=pymysql.cursors.DictCursor,  # optional: return rows as dicts
        autocommit=True                         # optional: enable autocommit
    )


    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            return rows
    finally:
        pass
    #    conn.close()
