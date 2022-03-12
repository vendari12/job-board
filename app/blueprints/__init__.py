"""from app.api.account.views import account 
from app.api.public.views import public
from app.api.blog.views import blog
from app.api.main.views import main
from app.api.jobs.views import jobs
from app.api.employer.views import employer
from app.api.posts.views import feeds
from app.api.organisations.views import organisations
from app.api.services.views import services
from app.api.directory.views import directory
from app.api.protected.views import protected"""
from fastapi import APIRouter



router = APIRouter()
"""router.include_router(protected, prefix='/admin', tags=['protected'])
router.include_router(account, prefix='/account', tags=['accounts'])
router.include_router(public, tags=['public'])
router.include_router(main, tags=['main'])
router.include_router(blog, prefix='/blog', tags=['blog'])
router.include_router(jobs, prefix='/jobs', tags=['jobs'])
router.include_router(employer, prefix='/employer', tags=['recruiters'])
router.include_router(feeds, prefix='/feed', tags=['feeds'])
router.include_router(organisations, prefix='/organisations', tags=['companies'])
router.include_router(services, prefix='/services', tags=['services'])
router.include_router(directory, prefix='/directory', tags=['directories'])"""





