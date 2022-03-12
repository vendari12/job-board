import datetime, math, os, logging, json
from math import floor, ceil
from html.parser import HTMLParser
from fastapi_sqlalchemy import db 
from app.config.config import settings
from fastapi import HTTPException
from fastapi_jwt_auth import AuthJWT
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from redis import Redis
from rq import Queue



if settings.otel_trace == True:
    from opentelemetry.instrumentation.redis import RedisInstrumentor

    # Instrument redis
    RedisInstrumentor().instrument()


redis_conn = Redis(host=settings.RQ_DEFAULT_HOST, port=settings.RQ_DEFAULT_PORT, db=0, password=settings.RQ_DEFAULT_PASSWORD)
redis_q = Queue('high', connection=redis_conn)


logging.basicConfig()


# Twilio variables

basedir = os.path.abspath(os.path.dirname(__file__))



@AuthJWT.load_config
def get_config():
    return settings


class ServerHTTPException(HTTPException):
    def __init__(self, error: str = None):
        super(ServerHTTPException, self).__init__(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=error
        )


class InvalidResource(ServerHTTPException):
    """
    raise when has invalid resource
    """


class NoSuchFieldFound(ServerHTTPException):
    """
    raise when no such field for the given
    """


class FileMaxSizeLimit(ServerHTTPException):
    """
    raise when the upload file exceeds the max size
    """


class FileExtNotAllowed(ServerHTTPException):
    """
    raise when the upload file ext not allowed
    """



class ObjectNotFound(HTTPException):
    def __init__(self, object:str) -> None:
        super().__init__(status_code=404, detail=f"{object} Object not found" ) 


class DuplicatedEntryError(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=422, detail=message)





def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    from datetime import datetime
    now = datetime.now()

    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time, datetime):
        diff = now - time
    elif not time:
        diff = now - now
    diff = map(int, diff)
    diff = floor(diff)
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(ceil(second_diff)) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(floor(second_diff / 60)) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(floor(second_diff / 3600)) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        #if d
        return str(floor(day_diff)) + " days ago"
    if day_diff < 31:
        day_diff = floor(day_diff/ 7)
        if day_diff == 1:
            return "a week ago"
        else:    
            return str(day_diff) + " weeks ago"
    if day_diff < 365:
        return str(floor(day_diff / 30)) + " months ago"
    return str(floor(day_diff / 365)) + " years ago"





class Page(object):

    def __init__(self, items, page, page_size, total):
        self.data = items
        self.previous_page = None
        self.next_page = None
        self.previous_page = page - 1 if page > 1 else None
        previous_items = (page - 1) * page_size
        has_next = previous_items + len(items) < total
        self.next_page = page + 1 if has_next else None
        self.total = total
        self.pages = int(math.ceil(total / float(page_size)))


def paginate(query, page, page_size=settings.PAGE_SIZE):
    if page <= 0:
        raise AttributeError('page needs to be >= 1')
    if page_size <= 0:
        raise AttributeError('page_size needs to be >= 1')
    if isinstance(query, list):
        items = query
        total = len(items)
        return Page(items, page, page_size, total)
    items = query.limit(page_size).offset((page - 1) * page_size).all()
    total = query.order_by(None).count()  
    return Page(items, page, page_size, total)  
  





async def get_lang_name(code):
    async with open(os.path.join(basedir, 'static', 'json', 'languages.json')) as f:
        data = json.load(f)
        try:
            return data[code]['name']
        except:
            return None


async def get_langs():
    languages = []
    async with open(os.path.join(basedir, 'static', 'json', 'languages.json'), encoding="utf8") as f:
        data = json.load(f)
        for e in data.keys():
            languages.append((e, data[e]['name']))
    return await languages










class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()



def jsonify_object(item, only_date=True):
    import time
    new_item = {}
    for item_attr in item._asdict():
        if not item_attr.startswith('_'):
            value = item.__dict__[item_attr] if type(item.__dict__[item_attr]) is not datetime.datetime else (str(
                item.__dict__[item_attr]) if not only_date else pretty_date(item.__dict__[item_attr]))
            new_item[item_attr] = value
    return new_item

def get_paginated_list(results):
    return_value = jsonify_object(results)
    items = []
    for item in results.items:
        items.append(jsonify_object(item))
    items.reverse()
    return_value['items'] = items
    del (return_value['query'])
    return return_value