from sqlalchemy import select
from models.blog import *
from schemas.blogschema import * 
from utils.dep import db, paginate
from config.config import settings


async def get_all_posts(* , page: int = 1, page_size: int = settings.PAGE_SIZE) -> List[BlogSchemaPag]:
    return paginate(db.session.query(BlogPost), page, page_size)


async def get_post(post_id: int):
    post = db.session.query(BlogPost).filter(BlogPost.id == post_id).first()
    return post


"""async def delete_contact(contact: _models.Contact, db: "Session"):
    db.delete(contact)
    db.commit()"""

"""
async def update_contact(
    contact_data: _schemas.CreateContact, contact: _models.Contact, db: "Session"
) -> _schemas.Contact:
    contact.first_name = contact_data.first_name
    contact.last_name = contact_data.last_name
    contact.email = contact_data.email
    contact.phone_number = contact_data.phone_number

    db.commit()
    db.refresh(contact)

    return _schemas.Contact.from_orm(contact)
"""