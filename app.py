from flask import Flask, jsonify, Response
from flask.globals import request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_restplus import Resource, Api
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if os.getenv('DATABASE_URL') is None:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/db.sqlite'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL').replace("://", "ql://", 1)

CORS(app)
db = SQLAlchemy(app)
api = Api(app)


class Post(db.Model):

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    mobile = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(40), nullable=False)
    city = db.Column(db.String(20), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    vac = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return str(id)

    def asdict(self):
        return {
            'id': self.id,
            'username': self.username,
            'url': self.url,
            'content': self.content,
            'mobile': self.mobile,
            'city': self.city,
            'vac': self.vac
        }


class User(db.Model):
    username = db.Column(db.String(40), primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(500), nullable=False)
    email = db.Column(db.String(40), nullable=False)

    def __repr__(self):
        return str(self.username)

    def asdict(self):
        return {
            'username': self.username,
            'name': self.name,
            'password': self.password,
            'email': self.email
        }


@ api.route('/post')
class PostApi(Resource):

    def get(self):
        posts = Post.query.order_by(Post.id.desc()).limit(100).all()
        res = []
        for post in posts:
            res.append(post.asdict())
        return res

    def post(self):
        response = request.get_json() if request.is_json else request.form
        for arg in ['username', 'url', 'content', 'mobile', 'city', 'vac']:
            if not response.get(arg):
                api.abort(406)

        post = Post(username=response['username'],
                    url=response['url'],
                    content=response['content'],
                    mobile=response['mobile'],
                    city=response['city'],
                    vac=response['vac'])

        db.session.add(post)
        db.session.commit()
        return post.asdict()


@ api.route('/user/<string:username>')
class CheckUserApi(Resource):

    def post(self, username):
        response = request.get_json() if request.is_json else request.form
        if not response.get('password'):
            api.abort(406)

        user = User.query.filter_by(username=username).first()
        if user is None:
            api.abort(400)

        if check_password_hash(user.asdict()['password'], response.get('password')):
            res = user.asdict()
            res['password'] = 'hidden'
            return res
        else:
            api.abort(403)


@ api.route('/user')
class AddUserApi(Resource):

    def post(self):
        response = request.get_json() if request.is_json else request.form
        for arg in ['username', 'password', 'name', 'email']:
            if not response.get(arg):
                api.abort(406)

        if User.query.filter_by(username=response['username']).first() is not None:
            api.abort(400)

        user = User(username=response['username'],
                    password=generate_password_hash(
            response['password'], 'sha256'),
            name=response['name'],
            email=response['email'])

        db.session.add(user)
        db.session.commit()
        res = user.asdict()
        res['password'] = 'hidden'
        return res


if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=8081)
