from xml.dom import ValidationErr
from flask_wtf import FlaskForm
from wtforms import StringField,IntegerField,SubmitField,BooleanField,SelectField,TextAreaField
from wtforms.validators import DataRequired,Length,Regexp
from ..models import Roles,Clients
from flask_pagedown.fields import PageDownField
class EditProfile(FlaskForm):
    student_id=StringField('student_ID')
    member_added_year=IntegerField('Year')
    member_id=IntegerField('Number')
    about_me=TextAreaField('About me')
    submit=SubmitField('Submit')

class EditProfileAdmin(FlaskForm):
    email=StringField('Email',validators=[DataRequired(),Length(1,64)])
    first_name = StringField('FirstName',validators=[ DataRequired(), Length(1, 64), 
                Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'usernames must have only letters, numbers, dots or ' 'underscores')])
    last_name = StringField('LameNane',validators=[ DataRequired(), Length(1, 64), 
                Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'usernames must have only letters, numbers, dots or ' 'underscores')])
    student_id=StringField('student_ID')
    member_added_year=IntegerField('Year')
    member_id=IntegerField('Number')
    confirmed=BooleanField('Confirmed')
    role=SelectField("Role",coerce=int)
    about_me=TextAreaField('About me')
    submit=SubmitField('Submit')
    
    def __init__(self,client,*args,**kwargs):
        super().__init__(*args,**kwargs)
        #回應該給selectfield下拉的值，以list包tuple 通常寫在selectfield(choices=[(),()])裡
        self.role.choices=[(Role.rid,Role.name) for Role in Roles.query.order_by(Roles.name).all()]
        self.client=client #在difinition就先實例化某人，給validate_emai用

    #寫給bootstrap的? if form.validate_email(form.email)==true
    def validate_email(self,field):
        #檢查字段有改變但還是跟其他人重複時，就錯誤
        if field.data!=self.client.email and Clients.query.filter_by(email=field.data).first():
            raise ValidationErr('Email already registered.')

'''
class PostForm(FlaskForm):
    body=TextAreaField("Whats' on your mind?",validators=[DataRequired()])
    submit=SubmitField('Submit')
'''
class PostForm(FlaskForm):
    #flask的富文本格式
    body=PageDownField("Whats' on your mind?",validators=[DataRequired()])
    submit=SubmitField('Submit')

class CommentForm(FlaskForm):
    body=PageDownField("Enter Your Comment",validators=[DataRequired()])
    submit=SubmitField('Submit')