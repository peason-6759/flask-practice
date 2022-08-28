from datetime import datetime
from xml.dom import ValidationErr
from flask import current_app,url_for
from itsdangerous.serializer import Serializer
from werkzeug.security import generate_password_hash,check_password_hash
#flask_login 主要用法是讓使用者登入後在其他頁面能夠進行、做紀錄為他是登入的狀況
#usermixin記錄四種方法 is_authenticated、is_active、is_anonymous、get_id()
from flask_login import UserMixin,AnonymousUserMixin
from . import login_manager
from . import db
import hashlib
from markdown import markdown
import bleach


class Follows(db.Model):
    __tablename__='follows'
    follower_id=db.Column(db.Integer,db.ForeignKey('clients.id'),primary_key=True)
    followed_id=db.Column(db.Integer,db.ForeignKey('clients.id'),primary_key=True)
    timestamp=db.Column(db.DateTime,default=datetime.utcnow())


class Clients(UserMixin,db.Model):

    __tablename__ ='clients'
    id=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(length=128),index=True,unique=True)
    password_hash = db.Column(db.String(length=128))
    first_name = db.Column(db.String(length=100))
    last_name = db.Column(db.String(length=100))
    student_id= db.Column(db.String(length=100))
    member_added_year=db.Column(db.Integer)
    member_id=db.Column(db.Integer)
    equip_id=db.Column(db.Integer,db.ForeignKey('equips.eid'),nullable=True)
    role=db.Column(db.Integer,db.ForeignKey('roles.rid'),nullable=True)
    active = db.Column(db.Boolean, default=True)
    date_added=db.Column(db.DateTime,default=datetime.utcnow())
    last_seen=db.Column(db.DateTime,default=datetime.utcnow())
    confirmed=db.Column(db.Boolean,default=False) #確定用戶是否已驗證註冊
    about_me=db.Column(db.Text())
    avatar_hash=db.Column(db.String(32))

    #backref用法ex Post.author.first_name 供給兩關係之間的實體化
    #也可 posts=clirntObj.posts.... for post in posts(因dynamic關係保留資料表)....
    posts=db.relationship('Post',backref='author',lazy='dynamic')
    
    comments=db.relationship('Comment',backref='author',lazy='dynamic')

    #關於兩個lazy joined dynnamic  https://shomy.top/2016/08/11/flask-sqlalchemy-relation-lazy/#disqus_thread
    #父資料表設置cascade 則會在父的子對象的關聯表也一併刪除紀錄(all意義不明，可能是指很多層的關聯都cascade，且orphan也刪除)
    #此時follower_id都是self的一個id followed是self(Follows.follower_id)我追蹤的對象
    followed=db.relationship('Follows',foreign_keys=[Follows.follower_id], backref=db.backref('follower',lazy='joined'),lazy='dynamic', cascade='all, delete-orphan')
    #此時followed_id都是self的一個id follower是self(Follows.followed_id)追蹤我的對象
    follower=db.relationship('Follows',foreign_keys=[Follows.followed_id], backref=db.backref('followed',lazy='joined'),lazy='dynamic', cascade='all, delete-orphan')

    def generate_comfirmation_token(self):
        #生成的此獨特token會放在寄出郵件的網址
        encoded_data=Serializer(current_app.config["SECRET_KEY"])#serializer方式導入儲存JSON WEB SIGNATURE的環境
        return encoded_data.dumps({'confirm':self.id}) #DUMPS儲存用戶(JSON格式且加密後的token)
    
    def confirm(self,token):
        encoded_data=Serializer(current_app.config["SECRET_KEY"]) 
        try:
            data=encoded_data.loads(token) #data為token的decoded，為dict
        except:
            return False

        if data.get('confirm')!=self.id:        #順便檢測是否這個用戶有無修改其他用戶的資料
            return False
        self.confirmed=True
        #self.followed(self) 錯誤，改寫!!
        return True

    def generate_auth_token(self,expiration):
        s=Serializer(current_app.config['SECERT_KEY'],expires_in=expiration)
        return s.dumps({'id':self.id}).decode('utf-8')
    
    @staticmethod
    def verify_auth_token(token):
        s=Serializer(current_app.config['SECERT_KEY'])
        try:
            data=s.load(token)
        except:
            return None
        return Clients.query.get(data["id"])

    def to_json(self):
        json_client={
            'url':url_for('api.get_user',id=self.id),
            'first_name':self.first_name,
            'last_name':self.last_name,
            'last_seen':self.last_seen,
            'posts_url':url_for('api.get_client_posts',id=self.id),
            'followed_posts_url':url_for('api.get_client',id=self.id),
            'post_count':self.posts.count()
        }
        return json_client

    def ping(self):
        self.last_seen=datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    @property #當呼叫這個類別，只能讀取不得修改
    def password(self):
        raise AttributeError("password is not a readable attribute")
    @password.setter  #setter、getter 和 deleter，(我想設置原因是安全問題，不讓呼叫函式直接查)
    def password(self,password): #x.password="cat" 這個是setter的方式，此時password就直接送給sha256_hash
        self.password_hash=generate_password_hash(password)
    def verify_password(self,password):
        return check_password_hash(self.password_hash,password) #查看這個用戶輸入的密碼的hash是否對的上資料庫的hash
        #important:不同的用戶，使用同密碼也會產生不同hash

    @login_manager.user_loader #這裝飾器負責註冊給flask_login
    def load_user(Clients_id): #獲取已登入的用戶訊息 以primary key為主，因為是獨特的
        return Clients.query.get(int(Clients_id)) #用戶標籤無效返回none
    

    def __init__(self,**kwargs): #這樣的做法也能處理舊用戶
        super().__init__(**kwargs)
        if  self.role is None:
            #指定為某功能的EMAIL在創帳號時能獲得不同權限，先在CONFIG設定
            #也許可增加其他條件等
            if self.email==current_app.config['PEASON_ADMIN']:
                self.role=Roles.query.filter_by(name='Administrator').first().rid

            if self.role is None:
                #不直接叫User,因為可能會改，就改一邊(Roles)
                self.role=Roles.query.filter_by(default=True).first().rid
        #gravatar
        if self.avatar_hash is None:
            self.generate_gravater_hash()
        #self.followed(self)

    #當在藍圖需要區分用戶可行功能時，就先用can驗證
    def can(self,perm):
        role_obj=Roles.query.filter_by(rid=self.role).first()
        return self.role is not None and role_obj.has_permission(perm)
    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def generate_gravater_hash(self):
        self.avatar_hash=hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()
        return self.avatar_hash

    #gravater預設頭像取得
    def gravatar(self,size=100,default="retro",rating="g"):
        gravater_url='https://secure.gravatar.com/avatar'
        hash=self.avatar_hash or self.generate_gravater_hash()
        return "{url}/{hash}?s={size}&d={default}&r={rating}".format(url=gravater_url,hash=hash,size=size,default=default,rating=rating)

    #follow
    def follow(self,client):
        if not self.is_following(client):
            now_follow=Follows(follower=self,followed=client)
            db.session.add(now_follow)
    def unfollow(self,client):
        now_unfollow=self.followed.filter_by(followed_id=client.id).first()
        if now_unfollow:
            db.session.delete(now_unfollow)
    def is_following(self,client):
        if client.id is None:
            return False
        return self.followed.filter_by(followed_id=client.id).first() is not None
    def is_followed_by(self,client):    
        if client.id is None:
            return False
        #follower的父(self在目前類別)對子對象(self在Follows)的fk為followed_id固定self，
        #這個filterby的lazy方式是dynamic，但backref自己id 用(left outer)join方法
        return self.follower.filter_by(follower_id=client.id).first() is not None
    
    @property #這樣就能保有Client db model 的特色，才能query...
    def followed_posts(self):
        #SELECT * FROM posts join follows ON follows.followed_id=posts.author_id WHERE follows.follower_id=1;
        #join寒士第二項參數就是ON.....
        return Post.query.join(Follows,Follows.followed_id==Post.author_id).filter(Follows.follower_id==self.id)
    
    @staticmethod
    def add_self_follows():
        #用在shell，用腳本更新數據庫
        for client in Clients.query.all():
            if not client.is_following(client):
                client.follow(client)
                db.session.add(client)
                db.session.commit()

class AnoymousUser(AnonymousUserMixin):
    #有無登入都給can、is_admin函數，這樣current_user可以在藍圖一次處理兩種
    def can(self,perm):
        return False
    def is_administrator(self):
        return False
#匿名者current_uesr本身沒有實例化AnoymousUser，所以加上AnoymousUser實例告訴flask-login的匿名用戶類別
login_manager.anonymous_user=AnoymousUser


class Equips(db.Model):
    __tablename__ ='equips'

    eid = db.Column(db.Integer, primary_key=True)
    equipname = db.Column(db.String(64), unique=True)
    
    clients=db.relationship("Clients",backref="equips")

    #def __repr__(self):        
        #return '<Role %r>' % self.equipname

class Roles(db.Model):
    __tablename__ ='roles'
    rid=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(64),unique=True)
    default=db.Column(db.Boolean,default=False,index=True)
    permissions=db.Column(db.Integer)
    #lazy有三種模式，整體用法差不多 要查
    user=db.relationship('Clients',backref='roles',lazy='dynamic')

    def __init__(self,**kwargs): 
        super().__init__(**kwargs)  #python 2.x用法 super(Roles,self)...
        if self.permissions is None: 
            self.permissions=0 #預設的新註冊用戶
    def add_permission(self,perm):
        if not self.has_permission(perm):
            self.permissions+=perm
    def remove_permission(self,perm):
        if self.has_permission(perm):
            self.permissions-=perm
    def reset_permission(self):
        self.permissions=0
        
    def has_permission(self,perm):
        return self.permissions&perm==perm #class permission有註解

    #用staticmethod無須建立實例即可調用可直接寫Role.insert_roles，若想在無創建roles的狀態下向current_user啥的給權限，就直接叫
    @staticmethod
    def insert_roles():
        roles={
            'User':[Permission.FOLLOW,Permission.COMMET,Permission.WRITE],
            'Moderator':[Permission.FOLLOW,Permission.COMMET,Permission.WRITE,Permission.MODERATE],
            'Administrator':[Permission.FOLLOW,Permission.COMMET,Permission.WRITE,Permission.MODERATE,Permission.ADMIN],
            }
        default_role='User'

        #初次對roles資料表更新role原則
        for r in roles:
            role=Roles.query.filter_by(name=r).first()
            if role==None:
                role=Roles(name=r) #若此項原則沒被手動創立過，就新增一個
            role.reset_permission() #就算有創立過的也可能是同模式 但不同的授權內容
            for perm in roles[r]:
                role.add_permission(perm)
            role.default=(role.name==default_role)#一個tuple會直接回傳數值
            db.session.add(role)
        db.session.commit()

class Permission():
    #用次方好處:每種組合加總的直都是唯一數字，想開放某幾項功能能用?
    #因為二進制能剛好將每隔一Bit就能判斷，利用(&運算每個bit是否都相符)就可以曾測是否開啟某功能
    #也可用list 但這樣做更好
    FOLLOW=1
    COMMET=2
    WRITE=4
    MODERATE=8
    ADMIN=16


class Post(db.Model):
    __tablename__='posts'
    id=db.Column(db.Integer,primary_key=True)
    body=db.Column(db.Text) #用text不限制長度
    body_html = db.Column(db.Text)
    timestamp=db.Column(db.DateTime,index=True,default=datetime.utcnow())
    author_id=db.Column(db.Integer,db.ForeignKey('clients.id'))

    comments=db.relationship('Comment',backref='post',lazy='dynamic')
    

    #?????????????????????????????????????????????????????????????????????????????????????????
    @staticmethod
    def on_changed_body(target,value,old_value,initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code','em', 'i', 'li'\
                    ,'ol', 'pre', 'strong', 'ul','h1', 'h2', 'h3', 'p']      
        #clean刪除所有不在allowed的標籤  
        target.body_html = bleach.linkify(bleach.clean(markdown(value, output_format='html')\
                                            ,tags=allowed_tags, strip=True))
        db.event.listen(Post.body, 'set', Post.on_changed_body)
    
    @staticmethod
    def from_json(json_post):
        body=json_post.get('body')
        if body is None or body=='':
            raise ValidationErr('post dose not have a body')
        return Post(body=body)

# m:m relationship (follower id liked by followed id)

class Comment(db.Model):
    __tablename__='comments'
    id=db.Column(db.Integer,primary_key=True)
    body=db.Column(db.Text) #用text不限制長度
    body_html = db.Column(db.Text)
    timestamp=db.Column(db.DateTime,index=True,default=datetime.utcnow())
    disabled=db.Column(db.Boolean,default=False)
    post_id=db.Column(db.Integer,db.ForeignKey('posts.id'))
    author_id=db.Column(db.Integer,db.ForeignKey('clients.id'))
    

    @staticmethod
    def on_changed_body(target,value,old_value,initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code','em', 'i',\
                    'strong']      
        #clean刪除所有不在allowed的標籤  
        target.body_html = bleach.linkify(bleach.clean(markdown(value, output_format='html')\
                                            ,tags=allowed_tags, strip=True))
        db.event.listen(Comment.body, 'set', Comment.on_changed_body)