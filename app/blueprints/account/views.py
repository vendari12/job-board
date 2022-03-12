from typing import Optional
import datetime
from fastapi import APIRouter, Depends, HTTPException, status,\
      File, UploadFile
from app.utils.security import authenticate, authenticate_email, get_password_hash, jwt_redis_blocklist
from .auth import TokenUser, UpdateAccount, Register,  ChangePassword, ForgotPassword,\
    ChangeEmailRequest, ChangeEmail, OTPToken, CreateProfile, UpdateProfile
from app.schemas.userschema import Login, UserSchema
from app.schemas.profileschema import ProfileSchema
from app.crud.account import create_user
import app.models.user as models
from app.utils.dep import DuplicatedEntryError,db, send_sms, redis_q, user_list
from app.utils.email import send_email
from app.utils.files_upload import FileUpload
from app.config.config import Templates, settings
from app.utils.decorators import AccessControl
from app.config.config import Templates


upload = FileUpload()

account = APIRouter()

@account.post('/login/', response_model=TokenUser)
async def login(user: Login, authorize: AccessControl = Depends()) -> TokenUser:
    user_auth = await authenticate(email=user.memail, password=user.password)
    if not user_auth:
        credential_type = 'email'
        raise HTTPException(
            status_code=400,
            detail=f'Incorrect {credential_type} or password'
        )
    access_token = authorize.create_access_token(user_auth.email)
    refresh_token = authorize.create_refresh_token(user_auth.email)

    authorize.set_access_cookies(access_token)
    authorize.set_refresh_cookies(refresh_token)    
    return Templates.TemplateResponse('index.html', {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'bearer',
        'role_name': user_auth.role.name if user_auth.role else None,
        'user_status': 'confirmed' if user_auth.confirmed else 'unconfirmed'
    })


@account.post('/register/', status_code=201 )
async def register(user_instance:Register,  authorize: AccessControl = Depends(),) -> TokenUser:
    user_obj = db.session.query(models.User).filter_by(mobile_phone = user_instance.mobile_phone).first()
    if user_obj is not None:
        raise DuplicatedEntryError(message="Phone number already exist")
    user_obj = db.session.query(models.User).filter_by(email = user_instance.email).first()
    if user_obj is not None:
        raise DuplicatedEntryError(message="Email already exist")
    user_instance.password_hash = get_password_hash(user_instance.password_hash)   
    user = await create_user(user_instance=user_instance)
    #token = user.generate_confirmation_token()
   
   
    #try:
    #    redis_q.enqueue(send_sms,to_phone=user_number, message=body)
    #except RuntimeError as e:
    #    print("\n\nAn Error Occurred:", e)
    #    raise HTTPException(status_code=400, detail="Couldn't send the otp")
    #else:
    access_token = authorize.create_access_token(user_instance.mobile_phone)
    refresh_token = authorize.create_refresh_token(user_instance.mobile_phone)

    authorize.set_access_cookies(access_token)
    authorize.set_refresh_cookies(refresh_token) 
    return        




@account.delete('/logout')
async def logout(Authorize: AccessControl = Depends()):
    """
    Because the JWT are stored in an httponly cookie now, we cannot
    log the user out by simply deleting the cookies in the frontend.
    We need the backend to send us a response to delete the cookies.
    """
    Authorize.jwt_required()
    Authorize.unset_jwt_cookies()
    jti = Authorize.get_raw_jwt()['jti']
    jwt_redis_blocklist.setex(jti, settings.ACCESS_TOKEN_EXPIRE_MINUTES,'true')
    return {"msg":"Successfully logout"}


@account.get("/user/current/", response_model=UserSchema)
async def read_users_me(Authorize: AccessControl = Depends()):
    Authorize.jwt_required()
    return user_list(Authorize.get_current_user())



@account.post("/professional/new/", status_code=201)#, response_model=ProfileSchema)
async def new_profile(
 profile:CreateProfile, Authorize:AccessControl=Depends()
):

    Authorize.jwt_required()
    current_user= Authorize.get_current_user()
    try:
        profile_instance = models.Profile(
            **profile.dict(), user=current_user, first_name=current_user.first_name, last_name=current_user.last_name
        )
        db.session.add(profile_instance)
        db.session.commit()
        db.session.refresh(profile_instance)
      
        return ProfileSchema.from_orm(profile_instance)
    except Exception as e:
        raise HTTPException(detail=f'something went wrong {e}', status_code=500)    



@account.get("/professional/{profile_id}/")#, response_model=ProfileSchema)
async def get_profile(
 profile_id:int, Authorize:AccessControl=Depends()
):
    Authorize.jwt_required()
    current_user=Authorize.get_current_user()    
    profile_instance = db.session.query(models.Profile).filter_by(id=profile_id).filter_by(user=current_user).first()
    if profile_instance is None:
        raise HTTPException(detail="Profile not found", status_code=404)
    return ProfileSchema.from_orm(profile_instance) 



@account.get("/professional/")#, response_model=ProfileSchema)
async def profiles(
  Authorize:AccessControl=Depends()
):
    Authorize.jwt_required()
    current_user = Authorize.get_current_user()     
    profile_instance = db.session.query(models.Profile).filter_by(user=current_user).all() 
    if profile_instance is None:
        raise HTTPException(detail="Profiles not found", status_code=404)
    return list(ProfileSchema.from_orm(i) for i in profile_instance)



@account.put("/professional/{profile_id}/edit/")#, response_model=ProfileSchema)
async def edit_profile(
 profile:UpdateProfile, profile_id:int, Authorize:AccessControl=Depends()
):
    Authorize.jwt_required()
    current_user = Authorize.get_current_user()    
    profile_instance = db.session.query(models.Profile).filter_by(id=profile_id).filter_by(user = current_user).first()
    if profile_instance is None:
        raise HTTPException(detail="Profile not found", status_code=404)
    if profile.commitment:    
        profile_instance.commitment = profile.commitment
    if profile.title:    
        profile_instance.title=profile.title
    if profile.header:    
        profile_instance.header = profile.header
    if profile.type_of_work:    
        profile_instance.type_of_work = profile.type_of_work    
    db.session.add(profile_instance)
    db.session.commit()
    db.session.refresh(profile_instance)

    return ProfileSchema.from_orm(profile_instance) 



@account.post("/professional/files/{profile_id}/", response_model=ProfileSchema, status_code=201)
async def new_profile_image(profile_id:int, cover: Optional[UploadFile] = File(...), image:UploadFile = File(...), Authorize:AccessControl=Depends()):
    Authorize.jwt_required()
    current_user = Authorize.get_current_user()
    profile_instance = db.session.query(models.Profile).filter_by(id=profile_id).filter_by(user=current_user).first()
    if profile_instance is None:
        raise HTTPException(detail="Profile instance not found", status_code=404)
    _filename = await upload.pass_file(file=image)
    image_url = _filename["url"]

    if cover:
        filename = await upload.pass_file(file=cover)
        cover_url = filename['url']

        profile_instance.cover = cover_url
    profile_instance.image = image_url
    db.session.add(profile_instance)
    db.session.commit()
    db.session.refresh(profile_instance)
    return ProfileSchema.from_orm(profile_instance)



@account.put("/professional/files/{profile_id}/edit/", response_model=ProfileSchema, status_code=201)
async def edit_profile_image(profile_id:int, cover: Optional[UploadFile] = File(...), image:Optional[UploadFile] = File(...), Authorize:AccessControl=Depends()):
    Authorize.jwt_required()
    current_user = Authorize.get_current_user()
    profile_instance = db.session.query(models.Profile).filter_by(id=profile_id).filter_by(user = current_user).first()
    if profile_instance is None:
        raise HTTPException(detail="Profile instance not found", status_code=404)
    if image:    
        _filename = await FileUpload.pass_file(image)
        image_url = _filename["url"]
        profile_instance.image = image_url
    if cover:
        filename = await FileUpload.pass_file(cover)
        cover_url = filename['url']
        profile_instance.cover = cover_url
    db.session.add(profile_instance)
    db.session.commit()
    db.session.refresh(profile_instance)
    return ProfileSchema.from_orm(profile_instance)



@account.delete("/professional/{profile_id}/delete/",  status_code=200)
async def delete_profile_object(profile_id:int,  Authorize:AccessControl=Depends()):
    Authorize.jwt_required()
    current_user = Authorize.get_current_user()
    profile_instance = db.session.query(models.Profile).filter_by(id=profile_id).filter_by(user=current_user).first()
    if profile_instance is None:
        raise HTTPException(detail="Profile instance not found", status_code=404)
    
    db.session.delete(profile_instance)
    db.session.commit()
    return dict(message='Profile deleted successfully', status=1)


@account.put('/update/details/', status_code=status.HTTP_201_CREATED)
async def change_profile_details(data:UpdateAccount, Authorize:AccessControl = Depends()):
    """Respond to existing user's request to change their Account details."""
    Authorize.jwt_required()
    current_user = Authorize.get_current_user()
    try:
        if data.last_name:
            current_user.last_name = data.last_name
        elif data.area_code:
            current_user.area_code = data.area_code
        elif data.gender:
            current_user.gender = data.gender
        elif data.summary:
            current_user.summary_text = data.summary
        elif data.profession:
            current_user.profession = data.profession    
        elif data.first_name:
            current_user.first_name = data.first_name  
        elif data.city:
            current_user.city = data.city
        elif data.state:
            current_user.state = data.state   
        elif data.country:
            current_user.country = data.country                   
        db.session.add(current_user)            
        db.session.commit()
        return UserSchema.from_orm(current_user)
    except Exception as e:
        raise HTTPException(detail=f'Unsuccessful, this occured{e}.', status_code=400)


@account.post('/reset-password', status_code=status.HTTP_201_CREATED)
async def reset_password_request(data:ForgotPassword):
    """Respond to existing user's request to reset their password."""
    user = db.session.query(models.User).filter_by(mobile_phone=data.mobile_phone).first()
    if user:
        token = user.generate_password_reset_token()
        reset_link = f" Please visit this link {data.url} and your token {token}"
        area_code = str(user.area_code)
        area_code = area_code.replace(' ', '')
        phone_number = str(user.mobile_phone)
        phone_number = phone_number.replace(' ', '')
        if str(area_code)[0] != '+':
            area_code = '+' + str(area_code)
        body=f'Your confirmation link is: {reset_link}'
        redis_q.enqueue(send_sms, to_phone=str(area_code) + str(phone_number), message=body)
        return dict(message='A password reset link has been sent to {}.'.format(str(area_code) + str(phone_number)), status='warning')
    else:
        raise HTTPException(status_code=400, detail='User does not exist, try registering instead')
        



@account.post('/manage/change-email', status_code=status.HTTP_200_OK)
async def change_email_request(data:ChangeEmailRequest, authorize: AccessControl=Depends(use_cache=True)):
    """Respond to existing user's request to change their email."""
    authorize.jwt_required()
    current_user = authorize.get_current_user()
    if await authenticate_email(password=data.password, user=current_user, email=data.email):
        new_email = data.email
        token = authorize.get_current_user().generate_email_change_token(new_email)
        change_email_link = f"{data.link}/{token}"
        data = {'change_email_link': change_email_link,
                    'user': authorize.get_current_user()
                    } 
        template = Templates.get_template('/account/email/change_email.jinja2')
        template_obj = template.render(**data)            
        redis_q.enqueue(
                send_email,
                recipient=new_email,
                subject='Confirm Your New Email',
                template=template_obj,
                body=data)
        return dict(message='A confirmation link has been sent to {}.'.format(new_email),
                  status='warning')
    else:
        raise HTTPException(status_code=400, detail="Invalid email or password")


@account.post('/manage/reset-email/{token}/', status_code=status.HTTP_200_OK)
def change_email(token: str, authorize: AccessControl= Depends(use_cache=True)):
    """Change existing user's email with provided token."""
    authorize.jwt_required()
    current_user = authorize.get_current_user()
    if current_user.change_email(token):
        return dict(message='Your email address has been updated.', status='success')
    else:
        raise HTTPException(status_code=400, detail='The confirmation link is invalid or has expired.')

@account.get('/resend/otp', status_code=status.HTTP_200_OK)
async def confirm_request(authorize: AccessControl=Depends(use_cache=True)):
    """Respond to new user's request to confirm their account."""
    authorize.jwt_required()
    current_user = authorize.get_current_user()
    otp = current_user.generate_confirmation_token()
    area_code = str(authorize.get_current_user().area_code)
    area_code = area_code.replace(' ', '')
    phone_number = str(current_user.mobile_phone)
    phone_number = phone_number.replace(' ', '')
    if str(area_code)[0] != '+':
        area_code = '+' + str(area_code)
    message = 'Hello {} your otp is {}'.format(current_user.full_name, str(otp))
    r= redis_q.enqueue(send_sms,to_phone=(area_code) + (phone_number), message=message)
    print(r)      
    return dict(message='An otp has been sent to {}.'.format(str(area_code) + str(phone_number)) , status='success')



                     
@account.post('/confirm/token', status_code=status.HTTP_201_CREATED)
def confirm(data:OTPToken,authorize:AccessControl=Depends(use_cache=True)):
    authorize.jwt_required()
    current_user = authorize.get_current_user()
    user = int(current_user.otp_secret)
    token = int(data.token)
    if user == token:
        current = datetime.datetime.now()
        if current > authorize.get_current_user().otp_created_time + datetime.timedelta(minutes=5):
            raise HTTPException(status_code=400, detail='The confirmation token has expired.')
        else:
            current_user.confirmed = True
            db.session.add(current_user)
            db.session.commit()
            return dict(message="Success, your account has been created successfully", status="success")
    else:
        raise HTTPException(detail='Error! invalid token.', status_code=400)                 
   
"""@account.route(
    '/join-from-invite/<int:user_id>/<token>', methods=['GET', 'POST'])
def join_from_invite(user_id, token):"""
    
    #Confirm new user's account with provided token and prompt them to set
    #a password.
"""if authorize.get_current_user() is not None and authorize.get_current_user().is_authenticated:
        flash('You are already logged in.', 'error')
        return redirect(url_for('post.post_create'))

    new_user = User.query.get(user_id)
    if new_user is None:
        return redirect(404)

    if new_user.password_hash is not None:
        flash('You have already joined.', 'error')
        return redirect(url_for('post.post_create'))

    if new_user.confirm_account(token):
        form = CreatePasswordForm()
        if form.validate_on_submit():
            new_user.password = form.password.data
            db.session.add(new_user)
            db.session.commit()
            flash('Your password has been set. After you log in, you can '
                  'go to the "Your Account" page to review your account '
                  'information and settings.', 'success')
            return redirect(url_for('account.login'))
        return render_template('account/join_invite.html', form=form)
    else:
        flash('The confirmation link is invalid or has expired. Another '
              'invite email with a new link has been sent to you.', 'error')
        token = new_user.generate_email_confirmation_token()
        invite_link = url_for(
            'account.join_from_invite',
            user_id=user_id,
            token=token,
            _external=True)
        get_queue().enqueue(
            send_email,
            recipient=new_user.email,
            subject='You Are Invited To Join',
            template='account/email/invite',
            body={'user':new_user,
            'body':invite_link})
    return redirect(url_for('account.login'))"""




