
#import logging
#from threading import Thread
#from logging.handlers import SMTPHandler, RotatingFileHandler
import requests
from app.config.config import settings

def send_email(recipient, subject, template, body):
    if settings.MAIL_AUTH_TYPE == 'mailgun':
        kwargs = body
        data = {
                "from": settings.MAIL_DEFAULT_SENDER,
                "to": recipient,
                "subject" : subject,
                "html" : template,
                "text" : (kwargs)}
        try:    
            r = requests.post("https://api.mailgun.net/v3/mg.networked.com.ng/messages", auth=("api", settings.MAILGUN_KEY),
                        data=data)
            print(r.status_code)          
        except Exception as e:
            print(e)                          
        

    


"""def send_error_message():
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    if not app.debug and not app.testing:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'],
                        app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'], subject='Networked Failure',
                credentials=auth, secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)
            if app.config['LOG_TO_STDOUT']:
                stream_handler = logging.StreamHandler()
                stream_handler.setLevel(logging.INFO)
                app.logger.addHandler(stream_handler)
            else:
                if not os.path.exists('logs'):
                    os.mkdir('logs')
                file_handler = RotatingFileHandler('logs/networked',
                                                   maxBytes=10240, backupCount=10)
                file_handler.setFormatter(logging.Formatter(
                    '%(asctime)s %(levelname)s: %(message)s '
                    '[in %(pathname)s:%(lineno)d]'))
                file_handler.setLevel(logging.INFO)
                app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('Networked startup')
"""