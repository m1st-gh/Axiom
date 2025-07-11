from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from .models import Base
from typing import Generator
from axiom import logger


class _Database:
    def __init__(self, db_path: str = "axiom.db") -> None:
        self.engine: Engine = create_engine(f"sqlite:///{db_path}")
        self.Session: sessionmaker[Session] = sessionmaker(bind=self.engine)
        logger.info(f"Database engine initialized for {db_path}")

    def ensure_schema(self) -> None:
        Base.metadata.create_all(self.engine)
        logger.info("Database schema ensured.")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        session: Session = self.Session()
        logger.debug("Database session opened.")
        try:
            yield session
            session.commit()
            logger.debug("Database session committed.")
        except Exception as e:
            logger.error(f"Database session rolled back due to error: {e}")
            session.rollback()
            raise
        finally:
            session.close()
            logger.debug("Database session closed.")


# Create a single, global instance of the Database
db = _Database()
