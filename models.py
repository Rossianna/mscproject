# coding: utf-8
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_required, current_user
from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView, AdminIndexView, expose
from flask_admin.form import Select2Widget
from flask import render_template, redirect, url_for
from wtforms import SelectField
from wtforms.fields import SelectField, HiddenField
from werkzeug.security import check_password_hash

db = SQLAlchemy()


class ApprovedData(db.Model):
    __tablename__ = 'approveddata'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    content = db.Column(db.String(255))


class PendingData(db.Model):
    __tablename__ = 'pendingdata'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    content = db.Column(db.String(255))


class Permission(db.Model):
    __tablename__ = 'permission'

    id = db.Column(db.Integer, primary_key=True)
    permission_name = db.Column(db.String(80), nullable=False, unique=True)
    description = db.Column(db.String(255))

    roles = db.relationship('Role', secondary='role_permission', backref='permissions')


class Role(db.Model):
    __tablename__ = 'role'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    description = db.Column(db.String(255))

    users = db.relationship('User', secondary='user_role', backref='roles')


t_role_permission = db.Table(
    'role_permission',
    db.Column('role_id', db.ForeignKey('role.id'), primary_key=True, nullable=False),
    db.Column('permission_id', db.ForeignKey('permission.id'), primary_key=True, nullable=False, index=True)
)


class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(255), nullable=False)

    def get_roles(self):
        return Role.query.join(t_user_role).filter(t_user_role.c.user_id == self.id).all()

    def has_role(self, role_name):
        return any(role.name == role_name for role in self.get_roles())


t_user_role = db.Table(
    'user_role',
    db.Column('user_id', db.ForeignKey('user.id'), primary_key=True, nullable=False),
    db.Column('role_id', db.ForeignKey('role.id'), primary_key=True, nullable=False, index=True)
)


class UserView(ModelView):
    can_create = True
    can_delete = False
    can_edit = False

    form_columns = ['username', 'password', 'role']

    form_overrides = {
        'password': HiddenField,
    }

    form_args = {
        'role': {
            'readonly': True
        }
    }

    @login_required
    def is_accessible(self):
        return current_user.role == 'admin'

    @login_required
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('home'))


class RoleView(ModelView):
    can_create = True
    can_delete = True
    can_edit = True

    @login_required
    def is_accessible(self):
        return current_user.role == 'admin'

    @login_required
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('home'))


class PermissionView(ModelView):
    can_create = True
    can_delete = False
    can_edit = True

    @login_required
    def is_accessible(self):
        return current_user.role == 'admin'

    @login_required
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('home'))


# class UserRoleInlineModelAdmin(ModelView):
#     can_delete = True
#     form_widget_args = {
#         'role': {
#             'widget': Select2Widget()
#         }
#     }


class RolePermissionInlineModelAdmin(ModelView):
    can_delete = True
    form_widget_args = {
        'permission': {
            'widget': Select2Widget()
        }
    }


# class UserAdmin(ModelView):
#     inline_models = [(t_user_role, {
#         'form_columns': ['role_id'],
#         'form_args': {'role_id': {'widget': Select2Widget()}}
#     })]


# class RoleAdmin(ModelView):
#     inline_models = [(t_user_role, {
#         'form_columns': ['user_id'],
#         'form_args': {'user_id': {'widget': Select2Widget()}}
#     })]
#
#
# # ????
# class PermissionAdmin(ModelView):
#     inline_models = [(t_role_permission, {
#         'form_columns': ['permission_id'],
#         'form_args': {'permission_id': {'widget': Select2Widget()}}
#     })]


# 创建管理员视图
class AdminView(AdminIndexView):
    @expose('/')
    @login_required
    def index(self):
        if current_user.role != 'admin':
            return redirect(url_for('home'))
        else:
            return self.render('admin/new_index.html')


# class PermissionAssignment(BaseView):
#     @expose('/')
#     @login_required
#     def index(self):
#         if current_user.role != 'admin':
#             return redirect(url_for('home'))
#         roles = Role.query.all()
#         permission = Permission.query.all()
#         return self.render('admin/permission_assignment.html', roles=roles, permission=permission)

