''''''
import re
import unittest
from myvenv import create_app,db
from myvenv.models import Roles,Clients
class FlaskClientTestCase(unittest.TestCase):
    #setUp、tearDown不需自行呼叫 
    # 會在整個有unittest環境的test資料夾開始跟結束自己跑
    # (與init.py有關 不過似乎不需設置) 
    def setUp(self): #激活上下文，創立環境
        self.app=create_app('testing')
        self.app_context=self.app.app_context()
        self.app_context.push()

        db.create_all()
        Roles.insert_roles()
        self.client=self.app.test_client(use_cookies=True) #flask內建測試客戶端對象

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        #當使用get方式獲取主頁時回200(正常get方法)
        response=self.client.get('/')  #response is the testresponse
        self.assertEqual(response.status_code,200)
        self.assertTrue( 'please log in' in response.get_data(as_text=True))

    def test_register_and_login(self):
        response=self.client.post('/register',\
            data={
                'email':'peasonunittest@example.com',
                'firstname':'unittestfirstname',
                'lastname':'unittestlastname',
                'password':'unittestpassword',
                'repassword':'unittestpassword',
            }) #輸入帳密為post方式
        self.assertEqual(response.status_code,302) #status:redirect 因為已經註冊帳號了
        response=self.client.post('/login',\
            data={
                'email':'peasonunittest@example.com',
                'password':'unittestpassword'
            }
            #遇到 302 状态码时，如果开启了 「 跟随重定向(Follow Redirects) 」 就会获取重定向地址并继续跳转，如果不开启就是直接返回结果.
            , follow_redirects=True) 
            
        self.assertEqual(response.status_code,200) #因此200應該就是redirect後的status了
        self.assertTrue(re.search('unittestfirstname',response.get_data(as_text=True))) #re.search 
        self.assertTrue(re.search('A confrimation email has been sent to you',response.get_data(as_text=True)))

        user=Clients.query.filter_by(email='peasonunittest@example.com').first()
        token=user.generate_comfirmation_token()
        response=self.client.get('/confirm/{}'.format(token),follow_redirects=True)
        user.confirm(token)
        self.assertEqual(response.status_code,200)
        self.assertTrue('You have confirmed your account, Thanks!',response.get_data(as_text=True))

        response=self.client.get('/logout',follow_redirects=True)
        self.assertEqual(response.status_code,200)
        self.assertTrue('You have been logged out!' in response.get_data(as_text=True))
        
        