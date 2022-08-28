from random import randint
from sqlalchemy.exc import IntegrityError #exc:core exception
from . import db
from myvenv.models import Clients,Post,Permission
import faker

def Users_fake(count=100):
    fake=faker.Faker()
    for i in range(count):
        usernames=fake.name().split(" ")
        user=Clients(email=fake.email(),
                    password='password',
                    first_name=usernames[0],
                    last_name=usernames[1],
                    role=Permission.COMMET,
                    confirmed=True,
                    date_added=fake.past_date(),
                    about_me=fake.text())
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            print("fake data have been rollback")
            count+=1

def posts(count=100):
    fake=faker.Faker()
    total_user_count=Clients.query.count()
    
    for i in range(count):
        #offset,limit,slice 都是限制
        #offset:某數字後的所有資料
        this_user=Clients.query.offset(randint(0,total_user_count-1)).first()
        post_article=Post(body=fake.text(),
                        timestamp=fake.past_date(),
                            author=this_user)
        db.session.add(post_article)
        db.session.commit()



