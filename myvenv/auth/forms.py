from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,BooleanField
from wtforms import ValidationError
from wtforms.validators import DataRequired,Length,Email,Regexp,EqualTo #文本預設了方式 例如Email的要求輸入格式等
from ..models import Clients

class loginForm(FlaskForm):
    #unsolved
    email=StringField('Email',validators=[DataRequired(),Length(1,64),Email(message='The invalid email input')]) #type為email??還是<email></email>?
    password=PasswordField('Password',validators=[DataRequired()]) #type為password的<input元素>
    remember_me=BooleanField('Keep me logged in') #勾的眶框
    submit=SubmitField('Login')

class registrationForm(FlaskForm):

    email=StringField('Email',validators=[DataRequired(),Length(1,64),Email(message='The invalid email input')]) #type為email??還是<email></email>?
    #正規表達式
    firstname = StringField('FirstName',validators=[ DataRequired(), Length(1, 64), 
                Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'usernames must have only letters, numbers, dots or ' 'underscores')])
    lastname = StringField('LameNane',validators=[ DataRequired(), Length(1, 64), 
                Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'usernames must have only letters, numbers, dots or ' 'underscores')])
    password=PasswordField('Password',validators=[DataRequired(),EqualTo('repassword',message='Password must match')])
    repassword=PasswordField('Confrim password',validators=[DataRequired()])
    submit=SubmitField('Register')
    
    #不確定wtfform 跟form的用法在這是否相同!
    def validate_email(self,field):
        if Clients.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered')

    def validate_username(self,field):
        if Clients.query.filter_by(first_name=field.data).first() and Clients.query.filter_by(last_name=field.data).first():
            raise ValidationError('This name is already registered')

class changePasswordField(FlaskForm):
    password=PasswordField('Password',validators=[DataRequired()]) #type為password的<input元素>
    newPassword=PasswordField('New Password',validators=[DataRequired(),EqualTo('renewPassword',message='Password must match')])
    renewPassword=PasswordField('Confrim New password',validators=[DataRequired()])
    submit=SubmitField('Confrim')
