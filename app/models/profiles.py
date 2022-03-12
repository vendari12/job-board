from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Column,String, Integer, ForeignKey,DateTime, Text, func, JSON
from sqlalchemy.orm import relationship, backref
from app.db.base import Base


    
class Profile(Base):
    __tablename__ = 'profiles'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    first_name = Column(String(64), index=True)
    last_name = Column(String(64), index=True)
    title = Column(String(256), index=True)
    header = Column(String(512), index=True)
    commitment = Column(String)
    type_of_work = Column(String)
    image = Column(String, default=None, nullable=True)
    cover = Column(String, default=None, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='cascade'))

    user = relationship('User', backref='profiles')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


    def employer_can_download(self, employer_id):
        return self.messages.filter(ProfileMessage.recipient_id == employer_id).first()

    @hybrid_property
    def full_name(self):
        return self.first_name + " " + self.last_name

    @property
    def completeness(self):
        perc = 10
        if self.skills:
            perc += 18
        if self.education:
            perc += 18
        if self.jobs:
            perc += 18
        if self.projects:
            perc += 18
        if self.languages:
            perc += 18

        return perc

   
  

class ProfileSkill(Base):
    __tablename__ = 'profile_skills'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(256), index=True)
    description = Column(String(512), index=True)
    exp = Column(String)#(name='commitment', N='Nobie', I='Intermediate', E='Experienced', G='Guru'))
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='cascade'))

    profile = relationship('Profile', backref='skills')
    ##score = query_expression()




class ProfileEdu(Base):
    __tablename__ = 'profile_education'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    school = Column(String(256), index=True)
    degree = Column(String)#(name='commitment', A='Associate', B='Bachelor', M='Master', D='Doctoral'))
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, default=None, nullable=True)
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='cascade'))

    profile = relationship('Profile', backref='education')
    #score = query_expression()




class ProfileJob(Base):
    __tablename__ = 'profile_jobs'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    company = Column(String(256), index=True)
    title = Column(String(256), index=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, default=None, nullable=True)
    commitment = Column(String)
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='cascade'))

    profile = relationship('Profile', backref='jobs')
    #score = query_expression()


class ProfileLang(Base):
    __tablename__ = 'profile_langs'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    lang = Column(String(50), index=True)
    level = Column(String)
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='cascade'))

    profile = relationship('Profile', backref='languages')
    #score = query_expression()

   


class ProfileProject(Base):
    __tablename__ = 'profile_projects'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(256), index=True)
    description = Column(String(512), index=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, default=None, nullable=True)
    links = Column(JSON)
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='cascade'))

    profile = relationship('Profile', backref='projects')
    #score = query_expression()




class ProfileMessage(Base):
    __tablename__ = 'profile_messages'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='cascade'))
    recipient_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='cascade'))
    body = Column(Text)
    timestamp = Column(DateTime, index=True, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    read_at = Column(DateTime, default=None, nullable=True)

    user = relationship('User', primaryjoin="ProfileMessage.user_id==User.id")
    profile = relationship('Profile', backref=backref('messages', lazy='dynamic'))

    def __repr__(self):
        return '<Message {}>'.format(self.body)

     

      
