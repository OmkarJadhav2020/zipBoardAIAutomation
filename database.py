from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import config

Base = declarative_base()

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String) # Not unique, URL is the identifier
    url = Column(String, unique=True)
    article_count = Column(Integer, default=0)
    articles = relationship("Article", back_populates="category")

class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    url = Column(String, unique=True)
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship("Category", back_populates="articles")
    content_text = Column(Text) # Full text content
    word_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # New Fields
    article_custom_id = Column(String) # Extracted identifier (e.g. 63)
    has_screenshots = Column(Boolean, default=False)
    
    # Analysis fields
    gap_analysis = Column(Text) # "Gaps Identified"
    suggested_topics = Column(Text) # "Suggestions" (or repurposed)
    topics_covered = Column(Text) # New AI field
    content_type = Column(String) # New AI field ("How-to", "FAQ", etc)

class GapInsight(Base):
    __tablename__ = 'gap_insights'
    id = Column(Integer, primary_key=True)
    gap_id = Column(String) # GAP-001
    category = Column(String)
    description = Column(Text)
    priority = Column(String) # High/Medium/Low
    suggested_title = Column(String)
    rationale = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    engine = create_engine(f'sqlite:///{config.DB_NAME}')
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
