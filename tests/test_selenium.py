import threading
import unittest
import re
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from myvenv import create_app,db,fake
from myvenv.models import Roles,Clients
class SeleniumTestCase(unittest.TestCase): #an web driver API
    client=None 

    @classmethod
    def setUpClass(cls): #cls referred to the class, bound to a class instead of staticmethod that only related to function itself.
        options=webdriver.EdgeOptions()
        #options.add_argument('headless') #不顯示視窗，效率高
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        try:
            cls.client=webdriver.Edge('tests/webdriver/msedgedriver.exe',options=options)
        except:
            pass

        if cls.client:
            cls.app=create_app('testing')
            cls.app_context=cls.app.app_context()
            cls.app_context.push()

            import logging
            logger=logging.getLogger('werkzeug')
            logger.setLevel("ERROR")

            db.create_all()
            Roles.insert_roles()
            fake.Users_fake(10)
            fake.posts(10)
            admin_role=Roles.query.filter_by(permissions=0xff).first() #permission=11111111  為Roles的admin
            admin=Clients(email='peason6759@gmail.com',\
                    first_name='peason',\
                    last_name='lee',\
                    password='peason5825',\
                    role=admin_role,\
                    confirmed=True)
            db.session.add(admin)
            db.session.commit()

            os.environ.pop("FLASK_RUN_FROM_CLI")
            cls.server_thread=threading.Thread(
                target=cls.app.run, kwargs={'debug':False,
                'use_reloader':False,
                'use_debugger':False}
            )
            cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        if cls.client:
            cls.client.get('http://localhost:5000/shutdown')
            cls.client.quit()
            cls.server_thread.join

            db.drop_all()
            db.session.remove()

            cls.app_context.pop()
    
    def setUp(self):
        if not self.client:
            self.skipTest('web browser not available') #self->unittest.TestCase

    def tearDown(self):
        pass
        
    def test_admin_home_page(self):
        self.client.get('http://localhost:5000/')
        self.assertTrue(re.search('Hello, please log in',self.client.page_source))
        #self.client.find_element_by_link_text('Log In').click()  #deprecated
        self.client.find_element(By.LINK_TEXT,'Log In').click()
        self.assertIn('Log In', self.client.page_source)
        #self.client.find_element_by_name('email').send_keys('peason6759@gmail.com')
        self.client.find_element(By.NAME,'email').send_keys('peason6759@gmail.com')
        #self.client.find_element_by_name('password').send_keys('peason5825')
        self.client.find_element(By.NAME,'password').send_keys('peason5825')
        #self.client.find_element_by_name('submit').click()
        self.client.find_element(By.NAME,'submit').click()
        self.assertTrue(re.search('peason',self.client.page_source))   
        #self.client.find_element_by_link_text('Profile').click()
        self.client.find_element(By.LINK_TEXT,'Profile').click()
        self.assertIn('<h1>lee peason</h1>', self.client.page_source)
