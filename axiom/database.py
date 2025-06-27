
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from .models import Base
from typing import Generator

class _Database:
    def __init__(self, db_path: str = "axiom.db") -> None:
        self.engine: Engine = create_engine(f"sqlite:///{db_path}")
        self.Session: sessionmaker[Session] = sessionmaker(bind=self.engine)

    def ensure_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        session: Session = self.Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

# Create a single, global instance of the Database
db = _Database()
