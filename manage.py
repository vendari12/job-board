from fastapi import FastAPI,  Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_jwt_auth.exceptions import AuthJWTException
from app.blueprints import router
from app.config.config import settings
import typer
from pathlib import Path
from app.db.base import init_models, engine
from app.utils.dep import db, redis_conn, redis_q
from app.models.user import User, Role
import uvicorn
from fastapi_sqlalchemy import DBSessionMiddleware
from fastapi.staticfiles import StaticFiles
from rq import Worker,Connection
from fastapi.templating import Jinja2Templates
import time


app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f'{settings.API_V1_STR}/openapi.json'
)

from starlette_prometheus import metrics, PrometheusMiddleware

#Metrics endpoint
app.add_route('/metrics', metrics)

#Static route
app.mount("/static/", StaticFiles(directory="app/static"), name="static")
app.add_middleware(PrometheusMiddleware)


BASE_PATH = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_PATH / "app/templates"))

#Database Midleware session
app.add_middleware(DBSessionMiddleware, db_url=settings.DATABASE_URL)

app.include_router(
    router, prefix=settings.API_V1_STR
)


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)




if settings.otel_trace == True:  # pragma: no cover
    from opentelemetry import trace
   
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.resources import Resource

    from opentelemetry.sdk.trace import TracerProvider
    #from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource(attributes={"service.name": "JobBoard"})
    trace.set_tracer_provider(TracerProvider(resource=resource))
    tracer = trace.get_tracer(__name__)

   

    #span_processor = BatchSpanProcessor(otlp_exporter)

    #trace.get_tracer_provider().add_span_processor(span_processor)

    FastAPIInstrumentor.instrument_app(app)

    SQLAlchemyInstrumentor().instrument(engine=engine)
else:
    pass













cli = typer.Typer()


@cli.command()
def test_temp():
    if TEMPLATES.get_template('/account/login.html'):
        print('template found')
    print('template not found')    
    

@cli.command()
def db_init_models():
    init_models()
    print("Done")


@cli.command()
def setup_dev():
    """Runs the set-up needed for local development."""
    setup_general()


@cli.command()
def setup_prod():
    """Runs the set-up needed for production."""
    setup_general()


def setup_general():
    """Runs the set-up needed for both local development and production.
       Also sets up first admin user."""
    with db():
        Role.insert_roles()
        admin_query = db.session.query(Role).filter_by(name='Administrator')
        if admin_query.first() is not None:
            if db.session.query(User).filter_by(email=settings.ADMIN_EMAIL).first() is None:
                user = User(
                    first_name='Aniekan',
                    last_name='Okono',
            mobile_phone=settings.ADMIN_MOBILE_PHONE,
            area_code=settings.ADMIN_AREA_CODE,
                password_hash=settings.ADMIN_PASSWORD,
                confirmed=True,
                email=settings.ADMIN_EMAIL)
                db.session.add(user)
                db.session.commit()
                print('Added administrator {}'.format(user.full_name))

@cli.command()
def setup_admin():
    """Runs the set-up needed for both local development and production.
       Also sets up first admin user."""
    with db():
        Role.insert_roles()
        role = db.session.query(Role).filter_by(name='Administrator').first()
        from app.utils.security import get_password_hash
        password = get_password_hash("password")
        user = User(
                    first_name='Aniekan',
                    role=role,
                    last_name='Okono',
            mobile_phone="8143002800",
            area_code=settings.ADMIN_AREA_CODE,
                password_hash=password,
                confirmed=True,
                email="www.test@gmail.com")
        db.session.add(user)
        db.session.commit()
        print('Added administrator {}'.format(user.full_name))

@cli.command()
def runserver():
    uvicorn.run("manage:app", host="127.0.0.1", port=5000, reload=True, debug=True,log_level="info")




@cli.command()
def add_fake_data():
    """
    Adds fake data to the database.
    """
    with db():
        start = time.time()
        User.generate_fake(count=500)
        end = time.time() - start
        print(end)


@cli.command()
def run_worker():
    """Initializes a slim rq task queue."""
    with Connection(redis_conn):
        worker = Worker(redis_q)
        worker.work()

if __name__ == "__main__":
    cli()
