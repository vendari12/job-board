from http.client import HTTPException
from app.config.config import settings
from app.crud.account import get_user_by_field
from app.models.user import User
from fastapi_jwt_auth import AuthJWT


def verify_password(plain_password: str, hashed_password: str) -> bool:
        return settings.PWD_CONTEXT.verify(plain_password, hashed_password)    

async def authenticate(
    *, password: str, mobile_phone: int = None
):
    user = await get_user_by_field(
        model=User, field='mobile_phone', value=mobile_phone
    ) 
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user



async def authenticate_email(
    *, password: str, email: str = None, user
):
    email = await get_user_by_field(
        model=User, field='email', value=email
    )
    if email is None:
        user_obj = await get_user_by_field(
            model=User, field='mobile_phone', value=user.mobile_phone
        )
        if not verify_password(password, user_obj.password_hash):
            raise HTTPException(detail="Invalid password for account{}".format(user_obj.full_name), status_code=400)
        else:
            return True
    else:
        raise HTTPException(detail="Email belongs to a user on this platform", status_code=400)            


    


def get_password_hash(password: str) -> str:
    return settings.PWD_CONTEXT.hash(password)    


import redis

jwt_redis_blocklist = redis.StrictRedis(
        host=settings.RQ_DEFAULT_HOST, port=settings.RQ_DEFAULT_PORT, db=0, decode_responses=True)




@AuthJWT.token_in_denylist_loader
def check_if_token_in_denylist(decrypted_token):
    jti = decrypted_token['jti']
    entry = jwt_redis_blocklist.get(jti)
    return entry and entry == 'true'