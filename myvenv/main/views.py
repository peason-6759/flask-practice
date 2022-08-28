from datetime import datetime
from flask import current_app, flash, make_response, render_template,url_for,redirect,request,abort
from flask_login import current_user, login_required
from . import main
from .forms import EditProfile,EditProfileAdmin,PostForm,CommentForm
from myvenv.models import Clients,Permission,Post,Comment
from ..decorators import admin_required,permission_required
from .. import db
from sqlalchemy import desc,asc
from flask_sqlalchemy import get_debug_queries
@main.route('/',methods=['GET','POST'])  #拿到資料重整
def index():
    form=PostForm()
    if form.validate_on_submit() and current_user.can(Permission.COMMET):  #這是輸入完資料才能(validate....=true)送進來處理，為"post重定量、get模式，在submit之前，可對上一次輸入的資料做想做的事(ex存進資料庫...)
        #關於current_user._get_current_object() 在thread有用過一樣的方式，current_user本身為localproxy, 加上之後才是object
        #此用backref為author來代表author_id的fk
        post=Post(body=form.body.data,
                    author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit() 
        return redirect(url_for('.index')) #也是重定向
        
    show_followed=False #顯示所有(false) 或是 僅關注(true)
    if current_user.is_authenticated:
        show_followed=bool(request.cookies.get('show_followed'))

    if show_followed:
        query=current_user.followed_posts
    else:
        query=Post.query

    page=request.args.get('page',1,type=int) #default=page1
    #所有資料庫內文章分頁化為Pagination物件。desc為sqlalchemy方法
    pagination=query.order_by(desc(Post.timestamp)).paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    #posts=Post.query.order_by(Post.timestamp.desc())  #???
    #posts=Post.query.order_by(desc(Post.timestamp))
    posts=pagination.items
    return render_template('index.html',current_time=datetime.utcnow(),form=form,posts=posts,Permission=Permission,pagination=pagination) #第一次進網頁時validate為false，為get用法，他會判斷:(上一次)是否提交表單、(上一次)flaskform(wtf)堤供validate()方式是否觸發到datarequired()(line22)
    #the date and time as it would be in Coordinated Universal Time,and the form about the NameForm method will specify the data wihle name should show the next time when refreshing the page.

@main.route('/user/<int:user_id>')
@login_required
def profile(user_id):
    user=Clients.query.filter_by(id=user_id).first_or_404() #找不到就回404
    posts=user.posts.order_by(desc(Post.timestamp))
    return render_template('user.html',user=user,posts=posts,Permission=Permission)
    
@main.route('/edit-profile/',methods=['GET','POST'])
@login_required
def edit_profile():

    form=EditProfile()
    if form.validate_on_submit():
        current_user.student_id=form.student_id.data
        current_user.member_added_year=form.member_added_year.data
        current_user.member_id=form.member_id.data
        current_user.about_me=form.about_me.data
        db.session.commit()
        flash("Your profile have been changed! ")
        return redirect(url_for('main.profile',userfirstname=current_user.first_name))
    #預先在input顯示舊資料
    form.student_id.data=current_user.student_id
    form.member_added_year.data=current_user.member_added_year
    form.member_id.data=current_user.member_id
    form.about_me.data=current_user.about_me
    return render_template('edit_profile.html',form=form)

#還沒設計，要輸入網址id才能改該用戶，需要設計用戶表
#int:id 原本輸入string 改int
@main.route('/edit-profile/<int:id>',methods=['GET','POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    client=Clients.query.get_or_404(id)
    #初始預設client=client為了檢查validate email(在forms裡)
    form=EditProfileAdmin(client=client)
    if form.validate_on_submit():
        client.email=form.email.data
        client.first_name=form.first_name.data
        client.last_name=form.last_name.data
        client.student_id=form.student_id.data
        client.member_added_year=form.member_added_year.data
        client.member_id=form.member_id.data
        client.confirmed=form.confirmed.data
        client.role=form.role.data #因為client的Role的fk是int
        client.about_me=form.about_me.data
        flash('The profile has been updated.')
        return redirect(url_for('main.profile',user_id=client.id))

    form.email.data=client.email
    form.first_name.data=client.first_name
    form.last_name.data=client.last_name
    form.student_id.data=client.student_id
    form.member_added_year.data=client.member_added_year
    form.member_id.data=client.member_id
    form.confirmed.data=client.confirmed
    form.role.data=client.role #因為client的Role的fk是int
    form.about_me.data=client.about_me
    return render_template('edit_profile_admin.html',form=form,client=client)

    

@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE)
def for_modrate_only():
    return "This is the moderator"

#給每個post一個連結，可以分享啥的
@main.route('/post/<int:id>',methods=['GET','POST'])
def post(id):
    post=Post.query.get_or_404(id) #只有一個文章
    form=CommentForm()
    if form.validate_on_submit():
        comment=Comment(body=form.body.data,
                        post=post,
                        author=current_user._get_current_object()) #current_user.id不能用 因為relationship是傳入用戶的物件!
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been published.')
        return redirect(url_for('.post',id=post.id,page=-1)) #page:就算沒有要導入url路徑的值也能改，-1用意為傳入最後一頁
    
    page=request.args.get('page',1,type=int) #預設是一，但上面當comment傳送後rediect設定至最後(-1)
    pagination=post.comments.order_by(asc(Comment.timestamp)).paginate(page, per_page=current_app.config['FLASKY_COMMENT_PER_PAGE'],error_out=False)
    comments=pagination.items
    return render_template('post.html',posts=[post],form=form,comments=comments,pagination=pagination,Permission=Permission,id=post.id)

@main.route('/moderate/enable/<int:id>')
@permission_required(Permission.MODERATE)
@login_required
def moderate_enable(id):
    comment=Comment.query.filter_by(id=id).first()
    if comment.disabled:
        comment.disabled=False
        db.session.add(comment)
        db.session.commit()
    return redirect(url_for(".post",id=comment.post_id))

@main.route('/moderate/disable/<int:id>')
@permission_required(Permission.MODERATE)
@login_required
def moderate_disable(id):
    comment=Comment.query.filter_by(id=id).first()
    if not comment.disabled:
        comment.disabled=True
        db.session.add(comment)
        db.session.commit()
    return redirect(url_for(".post",id=comment.post_id))


@main.route('/editpost/<int:id>',methods=['GET','POST'])
@login_required
def edit_post(id):
    post=Post.query.get_or_404(id)
    if current_user!=post.author and not current_user.can(Permission.ADMIN):
        abort(403)
    form=PostForm()
    if form.validate_on_submit():
        post.body=form.body.data
        db.session.add(post)
        db.session.commit()
        flash("The post have been edited")
        return(redirect(url_for('main.post',id=post.id)))
    form.body.data=post.body
    return render_template('edit_post.html',form=form,Permission=Permission)

@main.route('/follow/<int:id>')
@login_required
def follow(id):
    user=Clients.query.filter_by(id=id).first()
    if user is None:
        flash("This user is temporary down, please try later.")
        return redirect(url_for('main.index'))
    #雖然有在模板寫條件，但還是為了安全起見。
    if current_user.is_following(user):
        flash("You're already following this user.")
        return redirect(url_for('main.profile',user_id=id))
    
    current_user.follow(user)
    db.session.commit()
    flash("You are now following %s." %user.first_name)
    return redirect(url_for('main.profile',user_id=id))

@main.route('/unfollow/<int:id>')
@login_required
def unfollow(id):
    user=Clients.query.filter_by(id=id).first()
    if user is None:
        flash("This user is temporary down, please try later.")
        return redirect(url_for('main.index'))
    #雖然有在模板寫條件，但還是為了安全起見。
    if not current_user.is_following(user):
        flash("You haven't following this user.")
        return redirect(url_for('main.profile',user_id=id))
    
    current_user.unfollow(user)
    db.session.commit()
    flash("You are now canceled following %s." %user.first_name)
    return redirect(url_for('main.profile',user_id=id))

@main.route('/followers/<int:id>')
@login_required
def followers(id):
    user=Clients.query.filter_by(id=id).first()
    page=request.args.get('page',1,type=int) #default=page1
    pagination=user.follower.paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    #posts=pagination.items
    follows=[{'user':item.follower,'timestamp':item.timestamp} for item in pagination.items]
    return render_template('followers.html',user=user,title="Followers of",endpoint='main.followers',pagination=pagination,follows=follows)

@main.route('/following/<int:id>')
@login_required
def following(id):
    user=Clients.query.filter_by(id=id).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('main.index'))
    page=request.args.get('page',1,type=int) #default=page1
    pagination=user.followed.paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    #posts=pagination.items
    followed=[{'user':item.followed,'timestamp':item.timestamp} for item in pagination.items]
    return render_template('followed.html',user=user,title="Following from ",endpoint='main.following',followed=followed)

@main.route('/all_resp')
@login_required
def show_all_resp():
    resp=make_response(redirect(url_for('main.index')))
    #expired 不是用秒的樣子所以用max age表示cookie被刪除時間，沒設定就是關broweser就刪。
    resp.set_cookie('show_followed',value='',max_age=60*60*24*30) #30days ，value設"0"會是True 無解
    return resp

@main.route('/followed_resp')
@login_required
def show_followed_resp():
    resp=make_response(redirect(url_for('main.index')))
    #expired 不是用秒的樣子所以用max age表示cookie被刪除時間，沒設定就是關broweser就刪。
    resp.set_cookie('show_followed',value='1',max_age=60*60*24*30) #30days
    return resp

@main.route('/shutdown')       #for selenium testing environ
def server_shutdown():
    if not current_app.testing: #應用於測試模式才可用，一般進入404
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown') #werkzeng內建旗幟關閉函數
    if not shutdown:
        abort(500)
    shutdown()
    return 'shutting down...'

@main.after_app_request
def after_request(response):  #若要保存日志，得另外搭配配置器
    for query in get_debug_queries():     #請求中的的sql語句紀錄
        if query.duration>=current_app.config['FLASK_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning('Slow query:%s\nDuration:%s\nContext:%s\n'\
                %(query.statement,query.parameters,query.context)) #that'll warning user on the terminal
    return response

