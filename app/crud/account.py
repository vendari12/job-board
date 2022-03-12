from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
from app.api.account.auth import Register
import app.models.user as models
from app.utils.dep import db, paginate


async def create_user(
    user_instance:Register):  
    user = models.User(**user_instance.dict())
    db.session.add(user)
    db.session.commit()
    db.session.refresh(user)
    return user

"""
async def get_all_contacts(db: "Session") -> List[_schemas.Contact]:
    contacts = db.query(_models.Contact).all()
    return list(map(_schemas.Contact.from_orm, contacts))"""


async def get_user_by_field(model:Any, field:str, value: Any):
    return db.session.query(model).filter(
            getattr(model, field) == value
        ).first()






"""async def delete_contact(contact: _models.Contact, db: "Session"):
    db.delete(contact)
    db.commit()


async def update_contact(
    contact_data: _schemas.CreateContact, contact: _models.Contact, db: "Session"
) -> _schemas.Contact:
    contact.first_name = contact_data.first_name
    contact.last_name = contact_data.last_name
    contact.email = contact_data.email
    contact.phone_number = contact_data.phone_number

    db.commit()
    db.refresh(contact)

    return _schemas.Contact.from_orm(contact)"""








