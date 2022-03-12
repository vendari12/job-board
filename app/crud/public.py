#from sqlalchemy import select
from app.models.user import ContactMessage
from app.utils.dep import db
#from typing import  List
from app.schemas.userschema import ContactSchema
from app.models.extra import EditableHTML
from app.utils.dep import db




async def add_contact_message(
    contact: ContactSchema
 )-> ContactSchema:
    contact_message = ContactMessage(**contact.dict())
    db.session.add(contact_message)
    db.session.commit()
    db.session.refresh(contact_message)
    return ContactSchema.from_orm(contact)



async def get_editableobj(editor_name):
    editable_html_obj = db.session.query(EditableHTML).filter_by(editor_name=editor_name).first()
    return editable_html_obj


"""async def get_all_contacts(db: session) -> List[_schemas.Contact]:
    contacts = db.query(_models.Contact).all()
    return list(map(_schemas.Contact.from_orm, contacts))"""


"""async def get_contact(contact_id: int, db: "Session"):
    contact = db.query(_models.Contact).filter(_models.Contact.id == contact_id).first()
    return contact"""


async def delete_contact(contact: ContactMessage):
    db.delete(contact)
    db.commit()


"""async def update_contact(
    contact_data: _schemas.CreateContact, contact: _models.Contact, db: "Session"
) -> _schemas.Contact:
    contact.first_name = contact_data.first_name
    contact.last_name = contact_data.last_name
    contact.email = contact_data.email
    contact.phone_number = contact_data.phone_number

    db.commit()
    db.refresh(contact)

    return _schemas.Contact.from_orm(contact)"""



