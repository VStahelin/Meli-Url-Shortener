from sqlalchemy import Column, Integer, String
from app.core.database import Base


class UrlShorted(Base):
    __tablename__ = "url_shortened"

    id = Column(String, primary_key=True, index=True)
    url = Column(String, index=False)
