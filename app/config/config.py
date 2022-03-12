
import os
from typing import Union, List
from pydantic import BaseSettings,validator, AnyHttpUrl
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates
import urllib.parse
from pathlib import Path

REDIS_URL = os.getenv('REDISTOGO_URL') or 'http://localhost:6379'
# Parse the REDIS_URL to set RQ config variables
urllib.parse.uses_netloc.append('redis')
url = urllib.parse.urlparse(REDIS_URL)


    

BASE_PATH = Path(__file__).resolve().parent.parent
Templates = Jinja2Templates(directory=str(BASE_PATH / "templates"))


class Settings(BaseSettings):
    API_V1_STR: str
    ALGORITHM: str
    APP_NAME: str
    PAGE_SIZE: int
    SECRET_KEY: str

    #ADMIN DETAILS
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str
    ADMIN_AREA_CODE: str
    ADMIN_MOBILE_PHONE: int
    

    otel_trace: bool

    #REDIS QUEUE
    RQ_DEFAULT_HOST = url.hostname
    RQ_DEFAULT_PORT:int = url.port
    RQ_DEFAULT_PASSWORD: str = url.password
    RQ_DEFAULT_DB : int = 0

    #JWT AUTH

    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    authjwt_secret_key: str
    # Configure application to store and get JWT from cookies
    authjwt_token_location: set = {"cookies", "headers"}
    # Disable CSRF Protection for this example. default is True
    authjwt_cookie_csrf_protect: bool = False

    #PASSWORD ENCRYPTION
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
    PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")
    

    authjwt_denylist_enabled: bool = True
    authjwt_denylist_token_checks: set = {"access","refresh"}

    # Email
    MAILGUN_KEY: str 
    MAIL_AUTH_TYPE: str
    MAIL_DEFAULT_SENDER: str

    #FILE UPLOAD PATH
    UploadPath:str = os.path.abspath(os.getcwd())+"/app/static/uploads/"

    
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    DATABASE_URL : str 

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()