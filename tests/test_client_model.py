import unittest
from myvenv.models import Clients,Roles#不得直接摳model 會沒有實例
from myvenv import db,create_app
                       
class UserModelTestCase(unittest.TestCase):
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

    def test_no_password_getter(self):
        Roles.insert_roles()
        c=Clients(email="example@example.com.tw",password="cat")
        #當在c.password後你斷定她會跑出attributeerror
        with self.assertRaises(AttributeError):c.password
