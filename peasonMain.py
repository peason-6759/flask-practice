import os
import sys
import click
COV=None
#因為設置環境變量時若只在test函數啟動已經來不及啟動coveage整個寫進去會太肥大，
# 因此當commend : flask test --coverage 第一個if會先獲取FLASK_COVERAGE
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    #coverage.coverage() 函 数 启 动 覆 盖 度 检 测 引 擎 。 branch=True 选 项 开 启 分 支 覆 盖 度 分 析
    #include 选 项 限 制 检 测 的 文 件 在 应 用 包 内，不指定就是整個虛擬環境。
    COV=coverage.coverage(branch=True,include='myvenv/*',omit='myvenv/Lib/*') 
    COV.start()
    
from myvenv import create_app,db
from myvenv.models import Clients,Equips,Roles,Permission
from flask_migrate import Migrate,upgrade

app=create_app(os.getenv('PEASON_CONFIG') or 'default')

#若想新增資料庫的變數時，避免直接使用dropall、creatall，所以用migrate
#flask db upgrade 命令能把改动应用到数据库中 ， 且 不 影 响 其 中 保 存 的 数 据 。
#數據庫更新方法
#(1) 对 数 据 库 模 型(class) 做 必 要 的 修 改 。
#(2) 执 行 flask db migrate 命 令 ， 生 成 迁 移 脚 本 。
#(3) 检 查 自 动 生 成 的 脚 本 ， 改 正 不 准 确 的 地 方 。
#(4) 执 行 flask db upgrade 命 令 ， 把 改 动 应 用 到 数 据 库 中 。
migrate=Migrate(app,db)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db,Clients=Clients,\
                Equips=Equips,\
                Roles=Roles,\
                Permission=Permission)

@app.cli.command() #命令列介面
@click.option('--coverage/--no-coverage',default=False,help='Run test under code coverage. ')
def test(coverage):  #unittest
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        os.environ['FLASK_COVERAGE']='1' #設定coverage值
        #sys.excutable:A string giving the absolute path of the executable binary for the Python interpreter, on systems where this makes sense.
        #sys.argv:a abs path for the python scrip
        os.execv(sys.executable,[sys.executable]+[sys.argv[0]+'.exe']+sys.argv[1:])#設定完後直接重跑目前的腳本一次(execvp(current path + sys.argv 通常用於遞迴等))，
        #在COV.start()(上面就開始跑測試了)

    import unittest
    tests=unittest.TestLoader().discover('tests') #單元測試以這個資料夾為主
    unittest.TextTestRunner(verbosity=2).run(tests) #flask test
    
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summray:')
        COV.report()
        basedir=os.path.abspath(os.path.dirname(__file__))
        covdir=os.path.join(basedir,'tmp/coverage') #basedir加上tmp/coverage目錄
        COV.html_report(directory=covdir)
        print('HTML version:file://%s/index.html'%covdir)
        COV.erase()

@app.cli.command()
@click.option('--length',default=25,help='Number of functions to include in the profiler report.')#運行最慢的25個函數
@click.option('--profile-dir',default=None,help='Directory where profiler data files are saved.') #每条请求的分析数据会保存到指定目录下的一个文件 中
def profile(length,profile_dir): #監視資源測試(正常下應是放create_app，當flask run 運作時，因為app run 不能透過commend...)
    from werkzeug.middleware.profiler import ProfilerMiddleware #wsgi的資源監視
    app.wsgi_app=ProfilerMiddleware(app.wsgi_app,restrictions=[length],profile_dir=profile_dir)
    app.run(debug=False) #暫時寫這


@app.cli.command()
def deploy():
    """Run deployment tasks."""
    #一指令 更新最新版本的migrate
    upgrade()
    Roles.insert_roles()
    Clients.add_self_follows()


