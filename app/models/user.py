import json
from time import time
from sqlalchemy import Column,String\
    , Integer, ForeignKey, Boolean, DateTime, Text, BigInteger, func, Float
from sqlalchemy.orm import relationship, backref
from app.db.base import Base
from app.models.profiles import *
from sqlalchemy import or_, and_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref
from app.config.config import settings, Templates
from itsdangerous import BadSignature, SignatureExpired
from itsdangerous import TimedSerializer as Serializer
from app.utils.dep import pretty_date, redis_q, db
from app.utils.email import send_email


class Permission:
    GENERAL = 'GENERAL'
    ADMINISTER = 'ADMINISTRATOR'
    MARKETERS = 'PROMOTER'
    EDITOR = 'EDITOR'
    CUSTOMERCARE = 'CUSTOMERCARE'


class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(64), unique=True)
    index = Column(String(64))
    default = Column(Boolean, default=False, index=True)
    permissions = Column(Integer)
    users = relationship('User', backref='role', lazy='dynamic')
    access_role = Column(String(70), unique=True)

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.GENERAL, 'main', True),
            'Promoter': (Permission.MARKETERS, 'marketer',False ),
            'Editor': (Permission.EDITOR, 'editor',False ),
            'CustomerCare': (Permission.CUSTOMERCARE, 'customercare',False ),
            'Administrator': (
                Permission.ADMINISTER,
                'admin',
                False  # grants all permissions
            )
        }
        for r in roles:
            role = db.session.query(Role).filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.access_role = roles[r][0]
            role.index = roles[r][1]
            role.default = roles[r][2]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role \'%s\'>' % self.name



# @whooshee.register_model('first_name', 'last_name', 'city', 'state', 'country', 'profession')
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    confirmed = Column(Boolean, default=False)
    first_name = Column(String(64), index=True)
    last_name = Column(String(64), index=True)
    email = Column(String(64), unique=True, index=True)
    gender = Column(String(64), index=True)
    profession = Column(String(64), index=True)
    area_code = Column(String(6), index=True)
    mobile_phone = Column(BigInteger, unique=True, index=True)
    summary_text = Column(Text)
    zip = Column(String(10), index=True)
    city = Column(String(64), index=True)
    state = Column(String(64), index=True)
    country = Column(String(64), index=True)
    password_hash = Column(String(128))
    role_id = Column(Integer, ForeignKey('roles.id', ondelete="CASCADE"))
    
    photos = relationship('Photo', backref='user',
                          lazy='dynamic')



    messages_received = relationship('Message',
                                     foreign_keys='Message.recipient_id',
                                     backref='recipient', lazy='dynamic')
    last_message_read_time = Column(DateTime)
    notifications = relationship('Notification', backref='user',
                                 lazy='dynamic')
    positions_created = relationship('Job', backref='user', lazy='subquery', cascade='all')
    
    user_applicants = relationship('Application', backref='user', lazy='joined')
    user_submissions = relationship('Submission', backref='user', lazy='joined')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
  

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == settings.ADMIN_EMAIL:
                self.role = db.session.query(Role).filter_by(
                    access_role=Permission.ADMINISTER).first()
            if self.role is None:
                self.role = db.session.query(Role).filter_by(default=True).first()

    @hybrid_property
    def full_name(self):
        return self.first_name + " " + self.last_name


    def can(self, access):
        return self.role is not None and self.role.access_role == access or self.role.access_role == Permission.ADMINISTER

    def is_admin(self):
        return self.can(Permission.ADMINISTER)

    def is_marketer(self):
        return self.can(Permission.MARKETER)

    @staticmethod
    def generate_fake(count=100, **kwargs):
        from sqlalchemy.exc import IntegrityError
        from random import seed, choice
        from faker import Faker

        fake = Faker()
        roles = db.session.query(Role).all()
        if len(roles) <= 0:
            Role.insert_roles()
            roles = db.session.query(Role).all()

        seed()
        for i in range(count):
            u = User(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.email(),
                profession=fake.job(),
                city=fake.city(),
                zip=fake.postcode(),
                state=fake.state(),
                summary_text=fake.text(),
                password_hash='password',
                confirmed=True,
                role=choice(roles),
                **kwargs)
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def generate_email_confirmation_token(self, expiration=604800):
        s = Serializer(settings.SECRET_KEY, expiration)
        return str(s.dumps({'confirm': self.id}).decode())

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(settings.SECRET_KEY, expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def generate_password_reset_token(self, expiration=3600):
        s = Serializer(settings.SECRET_KEY, expiration)
        return str(s.dumps({'reset': self.id}).decode())

    def confirm_account(self, token):
        s = Serializer(settings.SECRET_KEY)
        try:
            data = s.loads(token)
        except (BadSignature, SignatureExpired):
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        db.session.commit()
        return True

    def change_email(self, token):
        s = Serializer(settings.SECRET_KEY)
        try:
            data = s.loads(token)
        except (BadSignature, SignatureExpired):
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if db.session.query(User).filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        db.session.commit()
        return True

    def reset_password(self, token, new_password):
        s = Serializer(settings.SECRET_KEY)
        try:
            data = s.loads(token)
        except (BadSignature, SignatureExpired):
            return False
        if data.get('reset') != self.id:
            return False
        self.password_hash = self.get_password_hash(new_password)
        db.session.add(self)
        db.session.commit()
        return True

    def get_photo(self):
        photos = self.photos.all()
        if len(photos) > 0:
            return photos[0].image_url
        else:
            if self.gender == 'Female':
                return "https://1.semantic-ui.com/images/avatar/large/veronika.jpg"
            else:
                return "https://1.semantic-ui.com/images/avatar/large/jenny.jpg"


    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            return self

   

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            return self     


    def last_message(self, user_id):
        message = db.session.query(Message).order_by(Message.timestamp.desc()). \
            filter(or_(and_(Message.recipient_id == user_id, Message.user_id == self.id),
                       and_(Message.recipient_id == self.id, Message.user_id == user_id))).first()
        return message


    def history(self, user_id, unread=False):
        messages = db.session.query(Message).order_by(Message.timestamp.asc()). \
            filter(or_(and_(Message.recipient_id == user_id, Message.user_id == self.id),
                       and_(Message.recipient_id == self.id, Message.user_id == user_id))).all()
        return messages


    def new_messages(self, user_id=None):
        if not user_id:
            return db.session.query(Message).filter_by(recipient=self).filter(Message.read_at == None).distinct('user_id').count()
        else:
            return db.session.query(Message).filter_by(recipient=self).filter(Message.read_at == None).filter(
                Message.user_id == user_id).count()


    def add_notification(self, name, data, related_id, permanent=False):
        n = Notification(name=name, payload_json=data, user=self, related_id=related_id)
        db.session.add(n)
        db.session.commit()
        n = db.session.query(Notification).get(n.id)
        body = {
            'user': self.full_name,
            'link': 'main.notifications',
            'notification': n,
            'APP_NAME':settings.APP_NAME
        }
        template = Templates.get_template('/account/email/notification.jinja2')
        template_obj = template.render(**body)        
        redis_q.enqueue(
        send_email,
            recipient=self.email,
            subject='You Have a new notification on Networked',
            template=template_obj,
            body=body
            )
        
        return n

   






    def __repr__(self):
        return '<User \'%s\'>' % self.full_name




class PositionApplication(Base):
    __tablename__ = 'job_applications'
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey('applications.id', ondelete="CASCADE"))
    position_id = Column(Integer, ForeignKey('jobs.id', ondelete="CASCADE"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())




class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='cascade'))
    recipient_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))
    body = Column(Text)
    timestamp = Column(DateTime, index=True, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    read_at = Column(DateTime, default=None, nullable=True)

    user = relationship('User', primaryjoin="Message.user_id==User.id")

    def __repr__(self):
        return '<Message {}>'.format(self.body)







class Photo(Base):
    __tablename__ = 'photos'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    image_filename = Column(String, default=None, nullable=True)
    image_url = Column(String, default=None, nullable=True)
    user_id = Column(Integer(), ForeignKey(User.id, ondelete="CASCADE"))
    question_id = Column(Integer, ForeignKey('questions.id', ondelete="CASCADE"))
    answer_id = Column(Integer, ForeignKey('answers.id', ondelete="CASCADE"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return u'<{self.__class__.__name__}: {self.id}>'.format(self=self)


class Notification(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True)
    name = Column(String(128), index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))
    related_id = Column(Integer, default=0)
    timestamp = Column(Float, index=True, default=time)
    payload_json = Column(Text)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return '<Notification {}>'.format(self.name)


           
    def parsed(self):
        user = db.session.query(User).filter_by(id=self.related_id).first()
        if 'unread_message' in self.name:
            msg = db.session.query(Message).filter_by(id=self.payload_json).first()
            if user and msg:
                return {
                    "id":self.id,
                    "type": self.name,
                    "text": " {} sent you a message {} ...".format(
                        user.full_name, msg.body[:40].replace("\n", " ")),
                    "timestamp": pretty_date(self.created_at),
                    "time": self.timestamp,
                    #"user": user,
                    "read": self.read
                }
            else:
                self.read = True
                db.session.add(self)
                db.session.commit()
        elif 'unread_professional_message' in self.name:
            msg = db.session.query(ProfileMessage).filter_by(id=self.payload_json).first()
            if user and msg:
                return {
                    "id":self.id,
                    "type": self.name,
                    "text": "{} sent you a new professional message {} ...".format(
                        user.full_name, msg.body[:40].replace("\n", " ")),
                    "timestamp": pretty_date(self.created_at),
                    "time": self.timestamp,
                    #"user": user,
                    "read": self.read
                }
            else:
                self.read = True
                db.session.add(self)
                db.session.commit()

        
        elif 'new_job' in self.name:
            job = db.session.query(Job).filter_by(id=json.loads(self.payload_json)['job']).first()
            if user and job:
                return {
                    "id":self.id,
                    "type": self.name,
                    "title": "New Job vacancy",
                    "text": "{} Added a new job vacancy near you {} ...".format(
                        user.full_name, job.position_title[:20]),
                    "timestamp": pretty_date(self.created_at),
                    "time": self.timestamp,
                    #"user": user,
                    "read": self.read
                }
            else:
                self.read = True
                db.session.add(self)
                db.session.commit()
    
    

# @whooshee.register_model('org_name', 'org_description')
class Organisation(Base):
    __tablename__ = 'organisations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    image_filename = Column(String, default=None, nullable=True)
    image_url = Column(String, default=None, nullable=True)
    org_name = Column(String(255))
    org_city = Column(String(255))
    org_state = Column(String(255))
    company_registration_number = Column(String(70), default=None, nullable=True)
    org_country = Column(String(255))
    org_website = Column(String(255))
    org_industry = Column(String(255))
    archived = Column(Boolean, default=False)
    org_description = Column(Text)
    user = relationship('User', backref='organisations', cascade='all, delete')
    jobs = relationship('Job', backref='organisation')
    positions = relationship('Job', backref='organisation_positions',
                             primaryjoin="Organisation.id==Job.organisation_id")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return u'<{self.__class__.__name__}: {self.id}>'.format(self=self)

    def get_staff(self):
        ids = [user.user_id for user in self.staff]
        return User.query.filter(User.id.in_(ids)).all()

    def get_photo(self):
        if self.image_filename:
            return self.image_url
        else:
            return None

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    organisation_id = Column(Integer, ForeignKey('organisations.id', ondelete="CASCADE"), nullable=True)
    image_filename = Column(String, default=None, nullable=True)
    pub_date = Column(String, default=func.now(), nullable=False)
    end_date = Column(String, nullable=False)
    position_title = Column(String(255))
    position_city = Column(String(255))
    position_state = Column(String(255))
    position_country = Column(String(255))
    description = Column(Text)
    creator_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    applications = relationship("Application", secondary='job_applications',
                                backref=backref("positions", cascade='all'),
                                primaryjoin='Job.id==Application.position_id', cascade='all,delete')
    creator = relationship("User")
    created_at = Column(String, default=func.now())
    updated_at = Column(String, default=func.now(), onupdate=func.now())

    @property
    def org_name(self):
        return Organisation.get(self.organisation_id).org_name

    def __repr__(self):
        return u'<{self.__class__.__name__}: {self.id}>'.format(self=self)




