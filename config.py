import os
from myvenv.gmailsender.OAUTHDEV import Create_Service

basedir=os.path.abspath(os.path.dirname(__file__))
class Config: #通用配置

    #app.config['SECRET_KEY'] = 'hard to guess string'
    #導入配置，加密 防跨站攻擊(csrf)
    SECRET_KEY=os.urandom(16).hex() or "hard to guess string"

    MAIL_SERVER=os.environ.get('MAIL_SEVER','smtp.googlemail.com')
    MAIL_PORT=int(os.environ.get('MAIL_PORT','587'))
    #MAIL_USE_TLS=os.environ.get('MAIL_USE_TLS','True').lower() in ['true','on','1']
    #MAIL_USERNAME=os.environ.get('MAIL_USERNAME')#不得直接於腳本寫帳密!!
    #MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD')#不得直接於腳本寫帳密!!
    #MAIL_SENDER= 'peasontestpy@gamil.com'
    #MAIL_ADMIN= os.environ.get("MAIL_ADMIN")#這裡暫時設計為收信的的人
    Peason_SUBJECT_PREFIX='Peason-test'

    #google oauth2 for gmail smtp
    CLIENT_SECRET_KEY='gmailsender/client_secret_998693832119-p1aev0h0lqrjd225nm2p9sv2c34cg5v9.apps.googleusercontent.com.json'
    API_NAME='gmail'
    API_VERSION='v1'
    SCOPES=['https://mail.google.com/']

    SERVICE= Create_Service(CLIENT_SECRET_KEY,\
            API_NAME,API_VERSION,SCOPES)
    
    #mariadb setting
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    #用戶類別授予權限 Roles
    PEASON_ADMIN='peason6759@gmail.com'
    PEASON_MAIL_SENDER='peasontestpy@gmail.com'
    PEASON_MAIL_SENDER_PASSWORD=os.environ.get('MAIL_PASSWORD')
    #pagination
    FLASKY_POSTS_PER_PAGE=10
    FLASKY_COMMENT_PER_PAGE=7

    #sql timeout debug
    SQLALCHEMY_RECORD_QUERIES=True
    FLASK_SLOW_DB_QUERY_TIME=0.5

    SSL_REDIRECT = False

    @staticmethod  #無需先呼叫config 要設定就直接叫staticmethod就好
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    #app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    SQLALCHEMY_DATABASE_URI=os.environ.get('DEV_DATABASE_URL') or \
        "postgresql://ustvaltavxjysr:0124fda4f9316eedf3bef570187af477e4a5c09a53fbad94855cfeee1abb7784@ec2-44-194-4-127.compute-1.amazonaws.com/d21c54embqm9mv"

class TestingConfig(Config):
    TESTING=True
    ANYWAYGIVEITATRY=False
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI=os.environ.get('TEST') or "mariadb+mariadbconnector://root:@127.0.0.1:3306/client_test"

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI=os.environ.get('DEV_DATABASE_URL') or \
        "postgresql://ustvaltavxjysr:0124fda4f9316eedf3bef570187af477e4a5c09a53fbad94855cfeee1abb7784@ec2-44-194-4-127.compute-1.amazonaws.com/d21c54embqm9mv"

    @classmethod
    def init_app(cls,app):
        import logging
        #import base64
        from logging.handlers import SMTPHandler
        credentials=None
        secure=None
        if getattr(cls,'PEASON_ADMIN',None) is not None: #有問題傳mail給admin 前提是要有maim這個變數
            credentials=(cls.PEASON_MAIL_SENDER,cls.PEASON_MAIL_SENDER_PASSWORD)
            if getattr(cls,'MAIL_USE_TLS',None):
                secure=()
            mail_hendler=SMTPHandler(
                            mailhost=(cls.MAIL_SERVER,cls.MAIL_PORT),
                            fromaddr=cls.PEASON_MAIL_SENDER,
                            toaddrs=[cls.PEASON_ADMIN],
                            subject=cls.Peason_SUBJECT_PREFIX + ' Application Error',
                            credentials=credentials,
                            secure=secure
                            )
        mail_hendler.setLevel(logging.ERROR) 
        app.logger.addHandler(mail_hendler)

class HerokuConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        import logging #配置先前製作的登入失敗重大敬告及數據庫超時日誌 
        from logging import StreamHandler        
        file_handler = StreamHandler()        
        file_handler.setLevel(logging.INFO)        
        app.logger.addHandler(file_handler)
        
        from werkzeug.middleware.proxy_fix import ProxyFix        
        app.wsgi_app = ProxyFix(app.wsgi_app)
        
    SSL_REDIRECT = True if os.environ.get('DYNO') else False

configModel={
    'development':DevelopmentConfig,
    'production':ProductionConfig,
    'testing':TestingConfig, 
    'default':DevelopmentConfig}

