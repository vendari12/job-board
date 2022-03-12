
from sqlalchemy.orm import sessionmaker
from app.config.config import settings
from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import as_declarative, declarative_base

Model = declarative_base()

DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL, echo=True)



@as_declarative()
class Base():
    def _asdict(self):
        return {c.key: getattr(self, c.key)
                for c in inspect(self).mapper.column_attrs}

session = sessionmaker(
    engine, expire_on_commit=False, autoflush=False,
)


def init_models():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database inintialized")
    return None


def get_session():
    db = session(bind=engine)
    try:
        yield db
    finally:
        db.close()
