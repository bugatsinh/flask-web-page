import math
from flask import Flask, render_template, request, session, redirect
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import json
from flask_mail import Mail
import os


with open("config.json", "r")as f:
    param = json.load(f)["params"]

local_server = True
app = Flask(__name__)
app.secret_key = 'Super-secrate-key'
app.config['uplode_folder'] = param["uplode_location"]
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=param['GMAIL-USER'],
    MAIL_PASSWORD=param['GMAIL-PASWORD'])
mail = Mail(app)
if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = param['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = param['prod_uri']

db = SQLAlchemy(app)


class Contacts(db.Model):
    '''sno, name, email_add, phone_no, mas, date'''
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email_add = db.Column(db.String(20), nullable=False)
    phone_no = db.Column(db.String(12), nullable=False)
    mas = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)


class Posts(db.Model):
    "sno, name, eamil_add, phone_no, mas, date"
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    teg_line = db.Column(db.String(12), nullable=True)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(20), nullable=False)
    img_file = db.Column(db.String(12), nullable=True)
    date = db.Column(db.String(12), nullable=True)


@app.route("/", methods=["GET"])
def home():
    posts = Posts.query.filter_by().all()
    # [0:param['number_of_posts']]
    last = math.ceil(len(posts)/int(param['number_of_posts']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(param['number_of_posts']): (page-1) *
                  int(param['number_of_posts']) + int(param['number_of_posts'])]
    # pagination logic
    # first
    if page == 1:
        priv = "#"
        next = "/?page="+str(page + 1)
    elif page == last:
        priv = "/?page="+str(page - 1)
        next = "#"
    else:
        priv = "/?page="+str(page - 1)
        next = "/?page="+str(page + 1)
    # mid
    # priv = page-1
    # next = page + 1
    # last
    # priv = page-1
    # next = "#"

    return render_template('index.html', params=param, posts=posts, priv=priv, next=next)


@app.route("/post/<string:post_slug>", methods=["GET"])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=param, post=post)


@app.route("/about")
def about():
    return render_template('about.html', params=param)


@app.route("/delete/<string:sno>", methods=["GET", "POST"])
def delete(sno):
    if 'user' in session and session['user'] == param['admin_user']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/dashbord")


@app.route("/logout")
def logout():
    session.pop['user']
    return redirect("/dashbord")


@app.route("/uploder", methods=["GET", "POST"])
def uploder():
    if 'user' in session and session['user'] == param['admin_user']:
        if request.method == "POST":
            f = request.files["file1"]
            f.save(os.path.join(
                app.config['uplode_folder'], secure_filename(f.filename)))
            return "uploded succesfuly"


@app.route("/dashbord", methods=["GET", "POST"])
def dashbord():

    if 'user' in session and session['user'] == param['admin_user']:
        posts = Posts.query.all()
        return render_template('deshbord.html', params=param, posts=posts)

    if request.method == "POST":
        username = request.form.get('uname')
        userpass = request.form.get('Pass')

        if username == param['admin_user'] and userpass == param['admin_pass']:
            # set the sation variable
            session['user'] = username
            posts = Posts.query.all()
            return render_template('deshbord.html', params=param, posts=posts)

    return render_template('login.html', params=param)


@app.route("/edit/<string:sno>", methods=["GET", "POST"])
def edit(sno):
    if 'user' in session and session['user'] == param['admin_user']:
        if request.method == "POST":
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if sno == "0":
                post = Posts(title=box_title, teg_line=tline,
                             slug=slug, content=content, img_file=img_file, date=date)

                db.session.add(post)
                db.session.commit()

            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.teg_line = tline
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/'+sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=param, post=post)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        "adding entryu to the database"
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        '''sno, name, email_add, phone_no, mas, date'''
        entry = Contacts(name=name, email_add=email,
                         phone_no=phone, mas=message, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message("New messag from " + name,
                          sender=email,
                          recipients=[param['GMAIL-USER']],
                          body=phone + " \n" + message)
    return render_template('contact.html', params=param)


app.run(debug=True)
