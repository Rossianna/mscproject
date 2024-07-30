import os
import random
import string
import json
import requests
from flask import Flask, render_template, redirect, url_for, request, after_this_request, make_response
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

def generate_nonce(length=16):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def add_csp_header(response, nonce):
    csp = (
        f"default-src 'self';"
        f"script-src 'self' 'nonce-{nonce}';"
        f"style-src 'self' 'nonce-{nonce}';"
        f"img-src 'self';"
    )
    response.headers['Content-Security-Policy'] = csp
    response.set_cookie('csp_nonce', nonce)
    return response

@app.route('/')
def home():   
    nonce = generate_nonce()
    blog_content = ApprovedData.query.all()
    if current_user.is_authenticated:
        response = make_response(render_template('home.html', blog_content=blog_content, current_user=current_user.username, role=current_user.role, nonce=nonce))
        return add_csp_header(response, nonce)
    else:
        response = make_response(render_template('home.html', blog_content=blog_content, current_user=None, nonce=nonce))
        return add_csp_header(response, nonce)


@app.route('/login', methods=['POST', 'GET'])
def login():
    nonce = generate_nonce()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            response = redirect(url_for('home'))
            return add_csp_header(response, nonce)
        else:
            response = make_response(render_template('login.html', status='fail', nonce=nonce))
            return add_csp_header(response, nonce)
            
    response = make_response(render_template('login.html', status=None, nonce=nonce))
    return add_csp_header(response, nonce)


@app.route('/post_a_blog', methods=['POST', 'GET'])
@login_required
def post_a_blog():
    nonce = generate_nonce()  
    if request.method == 'POST':
        mode = request.form.get('mode')
        if mode == 'edit':
            blog_index = request.form.get('blog_index')
            blog = PendingData.query.get(blog_index)
            blog_content = blog.content
            response = make_response(render_template('post_a_blog.html', blog_index=blog_index, blog_content=blog_content, nonce=nonce))
            return add_csp_header(response, nonce)
    elif request.method == 'GET':
        blog_index = request.args.get('blog_index')
        if blog_index is not None:
            blog = PendingData.query.get(blog_index)
            blog_content = blog.content
            response = make_response(render_template('post_a_blog.html', blog_index=blog_index, blog_content=blog_content, role=current_user.role, nonce=nonce))
            return add_csp_header(response, nonce)
        else:
            response = make_response(render_template('post_a_blog.html', blog_index=None, role=current_user.role, nonce=nonce))
            return add_csp_header(response, nonce)


@app.route('/edit_a_blog', methods=['POST'])
@login_required
def edit_a_blog():
    nonce = generate_nonce()
    blog_index = request.form.get('blog_index')
    if blog_index is None:
        blog_content = request.form.get('blog_content')
        pending_data = PendingData(username=current_user.username, content=blog_content)
        db.session.add(pending_data)
        db.session.commit()
        response = make_response(redirect(url_for('home')))
        return add_csp_header(response, nonce)
    else:
        blog_content = request.form.get('blog_content')
        blog = PendingData.query.get(blog_index)
        blog.content = blog_content
        db.session.commit()
    response = make_response('success')
    return add_csp_header(response, nonce)


@app.route('/approve_a_blog')
@login_required
def approve_a_blog():
    nonce = generate_nonce()
    blog_content = PendingData.query.all()
    response = make_response(render_template('approve.html', blog_content=blog_content, current_user=current_user.username, nonce=nonce))
    return add_csp_header(response, nonce)


@app.route('/review_a_blog')
@login_required
def review_a_blog():
    nonce = generate_nonce()
    blog_content = PendingData.query.filter_by(username=current_user.username).all()
    response = make_response(render_template('review.html', blog_content=blog_content, current_user=current_user.username, nonce=nonce))
    return add_csp_header(response, nonce)


@app.route('/approve', methods=['POST'])
@login_required
def approve():
    nonce = generate_nonce()
    blog_index = request.form.get('blog_index')
    blog_username = request.form.get('blog_username')
    blog_content = request.form.get('blog_content')
    approved_data = ApprovedData(username=blog_username, content=blog_content)
    db.session.add(approved_data)
    pending_data = PendingData.query.get(blog_index)
    print(pending_data)
    db.session.delete(pending_data)
    db.session.commit()
    response = make_response('success')
    return add_csp_header(response, nonce)


@app.route('/logout')
def logout():
    nonce = generate_nonce()
    logout_user()
    response = make_response(redirect(url_for('home')))
    return add_csp_header(response, nonce)


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8000)


