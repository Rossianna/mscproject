import json
import requests
from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_admin import Admin, AdminIndexView, expose, BaseView
from models import PendingData, ApprovedData, User, Role, Permission, AdminView, db, UserView,\
    RoleView, PermissionView


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://mengyuan:ym97-yyz63@msc-database.mysql.database.azure.com:3306/staff_info?charset=utf8"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'abc%123'
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)


admin = Admin(app, index_view=AdminView(), template_mode='bootstrap3')
admin.add_view(UserView(User, db.session, endpoint='user_db'))
admin.add_view(RoleView(Role, db.session, endpoint='role_db'))
admin.add_view(PermissionView(Permission, db.session, endpoint='permission_db'))
# admin.add_view(PermissionAssignment(name='Permission Assignment'))


# used to load user
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    print('aaa')
    return redirect(url_for('login'))


@app.route('/')
def home():
    blog_content = ApprovedData.query.all()
    if current_user.is_authenticated:
        return render_template('home.html', blog_content=blog_content, current_user=current_user.username, role=current_user.role)
    else:
        return render_template('home.html', blog_content=blog_content, current_user=None)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            print(current_user)
            return redirect(url_for('home'))
        else:
            return render_template('login.html', status='fail')
    return render_template('login.html', status=None)


@app.route('/post_a_blog', methods=['POST', 'GET'])
@login_required
def post_a_blog():
    if request.method == 'POST':
        mode = request.form.get('mode')
        if mode == 'edit':
            blog_index = request.form.get('blog_index')
            print(blog_index)
            blog = PendingData.query.get(blog_index)
            blog_content = blog.content
            print(blog_content)
            return render_template('post_a_blog.html', blog_index=blog_index, blog_content=blog_content)
    elif request.method == 'GET':
        blog_index = request.args.get('blog_index')
        if blog_index is not None:
            blog = PendingData.query.get(blog_index)
            blog_content = blog.content
            return render_template('post_a_blog.html', blog_index=blog_index, blog_content=blog_content, role=current_user.role)
        else:
            return render_template('post_a_blog.html', blog_index=None, role=current_user.role)


@app.route('/edit_a_blog', methods=['POST'])
@login_required
def edit_a_blog():
    blog_index = request.form.get('blog_index')
    print(blog_index)
    if blog_index is None:
        blog_content = request.form.get('blog_content')
        pending_data = PendingData(username=current_user.username, content=blog_content)
        db.session.add(pending_data)
        db.session.commit()
        return redirect(url_for('home'))
    else:
        blog_content = request.form.get('blog_content')
        blog = PendingData.query.get(blog_index)
        blog.content = blog_content
        db.session.commit()
    return 'success'


@app.route('/approve_a_blog')
@login_required
def approve_a_blog():
    blog_content = PendingData.query.all()
    return render_template('approve.html', blog_content=blog_content, current_user=current_user.username)


@app.route('/review_a_blog')
@login_required
def review_a_blog():
    blog_content = PendingData.query.filter_by(username=current_user.username).all()
    return render_template('review.html', blog_content=blog_content, current_user=current_user.username)


@app.route('/approve', methods=['POST'])
@login_required
def approve():
    blog_index = request.form.get('blog_index')
    print(blog_index)
    blog_username = request.form.get('blog_username')
    blog_content = request.form.get('blog_content')
    approved_data = ApprovedData(username=blog_username, content=blog_content)
    db.session.add(approved_data)
    pending_data = PendingData.query.get(blog_index)
    print(pending_data)
    db.session.delete(pending_data)
    db.session.commit()
    return 'success'


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8000)


