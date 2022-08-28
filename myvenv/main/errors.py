from flask import render_template
from . import main #main指引的blueprint就是代替app_context

@main.app_errorhandler(404) #若不是app.errorhandler 則使用 app_errorhandler
def page_not_found(e):
    return render_template('404.html'),404

@main.app_errorhandler(500)     #若不是app.errorhandler 則使用 app_errorhandler
def page_not_found(e):
    return render_template('500.html'),500