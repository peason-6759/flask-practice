from flask import Blueprint
main=Blueprint('main',__name__)
from . import views,errors # .是當前的意思，意思是外部register後 藍圖開啟後 告知有view、errors的存在

