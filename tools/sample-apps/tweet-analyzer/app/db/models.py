from sqlalchemy import Integer, Column, DateTime, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
CONN = "postgresql://postgres@/pndb"


class PNScore(Base):
    __tablename__ = "pn_scores"
    id = Column(Integer, primary_key=True)
    start_datetime = Column(DateTime)
    end_datetime = Column(DateTime)
    avg_score = Column(Float)


def get_session():
    engine = create_engine(CONN)
    session = sessionmaker(bind=engine)
    return session()


def insert_score(values):
    session = get_session()
    pn_ref = PNScore(**values)
    session.add(pn_ref)
    session.commit()


def select_result(forms):
    session = get_session()
    pn_refs = session.query(PNScore)\
        .filter(PNScore.start_datetime > forms["start_datetime"])\
        .filter(PNScore.end_datetime < forms["end_datetime"])\
        .all()
    return pn_refs
