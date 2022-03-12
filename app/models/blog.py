from sqlalchemy.orm import backref, relationship
from sqlalchemy_mptt.mixins import BaseNestedSets
from app.db.base import Base
from sqlalchemy import Integer, String, DateTime, func, Boolean, Column, ForeignKey, Text


class BlogCategory(Base):
    __tablename__ = 'blog_categories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(), default=None, nullable=False)
    order = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class BlogTag(Base):
    __tablename__ = 'blog_tags'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(), default=None, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class BlogPostCategory(Base):
    __tablename__ = 'blog_post_categories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey('blog_categories.id', ondelete="CASCADE"))
    post_id = Column(Integer, ForeignKey('blog_posts.id', ondelete="CASCADE"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class BlogPostTag(Base):
    __tablename__ = 'blog_post_tags'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_id = Column(Integer, ForeignKey('blog_tags.id', ondelete="CASCADE"))
    post_id = Column(Integer, ForeignKey('blog_posts.id', ondelete="CASCADE"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class BlogPost(Base):
    __tablename__ = 'blog_posts'
    id = Column(Integer, primary_key=True)
    title = Column(String())
    image = Column(String(), default=None, nullable=False)
    text = Column(Text(), default=None)
    comments = relationship('BlogComment', backref=backref('post'), lazy='dynamic',
                               cascade="all, delete-orphan")
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))
    creator = relationship('User')
    categories = relationship("BlogCategory", secondary='blog_post_categories',
                                 backref=backref("posts"),
                                 primaryjoin=(BlogPostCategory.post_id == id),
                                 secondaryjoin=(BlogPostCategory.category_id == BlogCategory.id))
    tags = relationship("BlogTag", secondary='blog_post_tags',
                                 backref=backref("posts"),
                                 primaryjoin=(BlogPostTag.post_id == id),
                                 secondaryjoin=(BlogPostTag.tag_id == BlogTag.id))

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    

class BlogComment(Base, BaseNestedSets):
    __tablename__ = 'blog_post_comments'
    id = Column(Integer, primary_key=True)
    text = Column(String(), default=None)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))
    post_id = Column(Integer, ForeignKey('blog_posts.id', ondelete="CASCADE"))
    author = relationship('User')
    depth = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __init__(self, post_id, user_id, text, parent_id=None):
        self.post_id = post_id
        self.user_id = user_id
        self.text = text
        self.parent_id = parent_id


class BlogNewsLetter(Base):
    __tablename__ = 'blog_news_letters'
    id = Column(Integer, primary_key=True)
    email = Column(String(64), default=None, nullable=True, unique=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

