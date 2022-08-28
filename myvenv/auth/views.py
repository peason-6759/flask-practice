from flask import redirect, render_template,request,flash, url_for
from flask_login import login_required, login_user, logout_user,current_user
from .forms import loginForm,registrationForm,changePasswordField
from ..models import Clients 
from . import auth
from .. import db
from ..sendMail import send_email


@auth.route('/login',methods=['GET','POST'])#拿到資料重整
def login(): 
    form=loginForm()
    if form.validate_on_submit():
        client=Clients.query.filter_by(email=form.email.data).first()
        if client is not None and client.verify_password(form.password.data):
            #第二項的remember_me應回傳boolean，決定使用者該不該儲存cookie，省去下次登入
            #login_user實體化登入使用者。
            login_user(client,form.remember_me.data)
            next=request.args.get('next') #相對網址後面變/next
            if next is None or not next.startswith('/'):#要是開發者忘記設計next html、或是不安全的設置絕對路徑，至少還有主頁
                return redirect(url_for('main.index')) #一定要用相對變數，防止被串改成惡意網址。(不是直接進index.html，無法動作)

            return render_template('auth/login.html')  #一定要用相對變數，防止被串改成惡意網址
        
        flash("Invalid USERNAME/PASSWORD")

    return render_template('auth/login.html',form=form)

@auth.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out!')
    return redirect(url_for('main.index'))

@auth.route('/register',methods=['GET','POST'])
def register():
    form=registrationForm()
    if form.validate_on_submit():
        client=Clients(email=form.email.data,
                        first_name=form.firstname.data,
                        last_name=form.lastname.data,
                        password=form.password.data)
        db.session.add(client)
        db.session.commit()     #即使用戶會先儲存至db 不過confrimed為false

        clientObject=Clients.query.filter_by(email=form.email.data).first()
        login_user(clientObject,True)

        token=client.generate_comfirmation_token()
        send_email(client.email,'Confrim Your Account','auth/mail/cofrim',client=client,token=token)#寄出去確認後會有後面有token的網址/confirm/<token>
        flash("A confrimation email has been sent to you")
        #flash("Your account now have registered")
        return redirect(url_for('main.index'))

    return render_template('auth/register.html',form=form)


@auth.route('/confirm/<token>') #給mail訊息裡的網址
@login_required
def confirm(token):
    if current_user.confirmed: #current_user就是_get_.user #confirmed寒士用self直接繼承current_user實體
        return redirect(url_for('main.index'))

    if current_user.confirm(token):
        db.session.commit()
        flash('You have confirmed your account, Thanks!')
    else:
        flash('the confirmation links os invalid or expired')

    return redirect(url_for('main.index'))

#auth.before_request 限定auth的blueprint有效
#before_app_request 全局有效
#無論每次要求甚麼，進藍圖就需要先跑過這(進行攔截)
@auth.before_app_request  
def before_request(): #在這函示結束前，request.blueprint都在main
    # static 避免靜態資源(js,css等檔案取用異常)
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed\
            and request.blueprint!='auth'\
            and request.endpoint!='static'\
            and request.endpoint not in ['logout','resend_confirmation','main.index']:
            return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
    #is_anonymous 為usermixin類別函數
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    
    return render_template('auth/unconfirmed.html',client=current_user)

@auth.route('/confirmed')
@login_required
def resend_confirmation():
    token=current_user.generate_comfirmation_token()
    send_email(current_user.email,'Again Confrim Your Account','auth/mail/cofrim',client=current_user,token=token)
    flash("A new confrimation email has been sent to you")
    return redirect(url_for('main.index'))

@auth.route('/changepassword',methods=['GET','POST'])
@login_required
def changepassword():
    form=changePasswordField()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            current_user.password=form.newPassword.data
            db.session.commit()
            logout_user()
            flash("Your Password have been change, please login in again.")
            return redirect(url_for('main.index'))

        flash("The original password you input was incorrect!")

    return render_template('auth/changepassword.html',form=form)
    
'''
@auth.route('/secert') #範例，如此一來加上疊加的裝飾器後，那個網頁就可以結定是否需要燈入才能取得
@login_required
def secert():
    return 'Only authenticated users are allowed!'
    #if current_user.is_active:...開始給有登入的人服務
'''
