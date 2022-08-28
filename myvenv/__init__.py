from flask import Flask
from flask_bootstrap import Bootstrap
from flask_moment import Moment 
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import configModel  #在這就設定了參數配置config
from flask_pagedown import PageDown
bootstrap=Bootstrap()

moment=Moment()
db=SQLAlchemy()
login_manager=LoginManager()

# To create PageDownField instead of textareafield to statisfy RTF.
pagedown=PageDown()

def create_app(config_name):
    app=Flask(__name__)
    app.config.from_object(configModel[config_name]) #直接將config參數導入(第一個config是flask的)
    configModel[config_name].init_app(app) #初始設置 (app.config全部)
    
    bootstrap.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)
    
    if app.config['SSL_REDIRECT']:        
        from flask_sslify import SSLify        
        sslify = SSLify(app)
        
    from .main import main as main_blueprint #當前的main資料夾進__init__
    from .auth import auth as auth_blueprint #避免與檔名搞混?
    app.register_blueprint(main_blueprint) 
    app.register_blueprint(auth_blueprint)

    #from.api import api as api_blueprint
    #app.register_blueprint(api_blueprint,url_prefix='api/v1') #路由的URL都将以/api/v1开头

    return app
    
