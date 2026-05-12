from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FileField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
import requests
import os
from datetime import datetime
from database import db, init_db
from models import User, UserImage

YANDEX_API_GEOCODE_KEY = ""
YANDEX_API_STATIC_KEY = ""

app = Flask(__name__)
app.config['SECRET_KEY'] = '88005553535'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bd.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

init_db(app)


class Register(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


class Login(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class Upload(FlaskForm):
    image = FileField('Выберите картинку', validators=[DataRequired()])
    submit = SubmitField('Загрузить')


class City(FlaskForm):
    city = StringField('Название города', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Показать на карте')


def get_city_coords(city_name):
    geocode_url = "https://geocode-maps.yandex.ru/v1"
    params = {
        'geocode': city_name,
        'format': 'json',
        'results': 1,
        'apikey': YANDEX_API_GEOCODE_KEY
    }

    try:
        response = requests.get(geocode_url, params=params, timeout=10)
        print(f"Геокодера {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            try:
                point_str = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
                lon, lat = point_str.split()
                return float(lat), float(lon)
            except (KeyError, IndexError):
                return None
        return None
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

@app.route('/')
def home():
    return render_template('base.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('profile'))

    form = Register()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Такой логин уже есть', 'error')
            return render_template('register.html', form=form)

        new_user = User(username=form.username.data, password=form.password.data, avatar=None)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('profile'))

    form = Login()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data, password=form.password.data).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Приветствуем тебя, {user.username}', 'success')
            return redirect(url_for('profile'))
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    images = UserImage.query.filter_by(user_id=user.id).all()
    return render_template('profile.html', user=user, images=images)


@app.route('/upload', methods=['GET', 'POST'])
def upload_image():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    form = Upload()
    if form.validate_on_submit():
        file = form.image.data
        if file and file.filename:
            ftype = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
            newfile = f"user_{session['user_id']}_{datetime.now().strftime('%H_%M_%S"')}.{ftype}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], newfile))

            img = UserImage(filename=newfile, user_id=session['user_id'])
            db.session.add(img)
            db.session.commit()

            user = User.query.get(session['user_id'])
            if not user.avatar:
                user.avatar = newfile
                db.session.commit()

            return redirect(url_for('profile'))
    return render_template('upload.html', form=form)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


def get_city_coords(city_name):
    geocode_url = "https://geocode-maps.yandex.ru/v1"
    params = {
        'geocode': city_name,
        'format': 'json',
        'results': 1,
        'apikey': YANDEX_API_GEOCODE_KEY
    }

    try:
        response = requests.get(geocode_url, params=params, timeout=30)
        print(f"Геокодера {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            try:
                point_str = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
                lon, lat = point_str.split()
                return float(lat), float(lon)
            except (KeyError, IndexError):
                return None
        return None
    except Exception as e:
        print(f"Ошибка: {e}")
        return None


@app.route('/map', methods=['GET', 'POST'])
def yandex_map():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    form = City()
    map_url = None
    yandex_link = None
    city_name = None

    if form.validate_on_submit():
        city_name = form.city.data
        coords = get_city_coords(city_name)

        if coords:
            lat, lon = coords
            map_url = f"https://static-maps.yandex.ru/v1?ll={lon},{lat}&z=12&l=map&pt={lon},{lat},pm2rdm&size=600,400&apikey={YANDEX_API_STATIC_KEY}"
            response1 = requests.get(map_url, timeout=30)
            print(f"Static: {response1.status_code}")
            yandex_link = f"https://yandex.ru/maps/?text={city_name}&ll={lon},{lat}&z=12"
        else:
            print(f"{city_name} не найден или его не существует")

    return render_template('map.html', form=form, map_url=map_url, yandex_link=yandex_link, city_name=city_name)


if __name__ == '__main__':
    app.run()