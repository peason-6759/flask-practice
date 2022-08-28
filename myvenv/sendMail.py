import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from threading import Thread
from flask import render_template,current_app

def send_email(to,subject,template,**kwargs): #kwargs:可以處理各種型態的資料, jinja2常用#
    
    #Return the current object. 
    # This is useful if you want the real objet behind+ the proxy at a time for performance reasons or because you want to pass the object into a different context.
    #若非為了使用thread其實不用實體化current object的
    app=current_app._get_current_object()

    ###old flask mail, but google required oauth2 while flask mail is not available.
    #msg=Message(current_app.config['MAIL_SUBJECT_PREFIX']+subject,sender=current_app.config['MAIL_SENDER'],recipients=[to])
    #msg.body=render_template(template +'.txt',**kwargs) #一定要在從app route的地方才能寫進函式 不然flask不知道render_template是誰的 
    #msg.html=render_template(template+".html",**kwargs) 

    message=MIMEMultipart('alternative') ###MIMEMultipart的alternative種類，總有三種模式
    message["To"]=to
    message["From"]=current_app.config['PEASON_MAIL_SENDER']
    message["Subject"]=subject

    message.attach(MIMEText(render_template(template +'.txt',**kwargs) ,'txt'))
    message.attach(MIMEText(render_template(template+".html",**kwargs) ,'html'))

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()) \
            .decode()

    create_message={
        'raw':encoded_message
    }
    service=current_app.config['SERVICE']
    #with app.app_context()  #沒與@app_route連接時，得在send時加上
    thr=Thread(target=send_async_email, args=[app,create_message,service]) #with app.app_context需傳入flask app實例
    thr.start()
    return thr #return意義不明....

def send_async_email(app,msg,service):
    with app.app_context():
        send_message=(service.users().messages().send(userId="me",body=msg).execute())