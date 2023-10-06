from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_caching import Cache
import pandas as pd


flask_sqlalchemy = SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '1245678@22'
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

db = SQLAlchemy(app)
engine = create_engine('sqlite:///database.db', echo=True)
Session = sessionmaker(bind=engine)
session = Session()


UPLOAD_FOLDER = 'static/files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


data = pd.read_excel('orders.xlsx')

login_manager = LoginManager()
login_manager.login_view = 'login'  # Указываем функцию, которая обрабатывает вход пользователя


@login_manager.user_loader
def load_user(user_id):
    # Загрузка пользователя из базы данных по ID
    return User.query.get(int(user_id))

login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Article(db.Model):
    __tablename__ = 'article'
    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    date = Column(DateTime, default=datetime.utcnow)
    piar = relationship('Piar', backref='piar', lazy="dynamic")
    # piar = db.relationship('Piar', uselist=False, back_populates='piar')


class Piar(db.Model):
    __tablename__ = 'piar'
    id = Column(Integer, primary_key=True)
    trackcode = Column(String(100))
    point = Column(String(100))
    article_id = Column(Integer, ForeignKey('article.id'))
    item_name = Column(String(100))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('admin'))
        else:
            flash('Пароль или логин не правильно')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))



@app.route('/', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        # Извлеките запрос пользователя из данных формы
        query = request.form['query'].strip()  # Уберите начальные и конечные пробелы

        if query:
            results = db.session.query(Piar).filter(Piar.trackcode == query).all()


        else:
            # Если запрос пуст, верните пустой список результатов
            results = []

        # Передайте результаты поиска и историю поиска в шаблон
        return render_template('index.html', results=results, query=query)

    # Если это GET-запрос, просто отобразите страницу поиска
    return render_template('index.html', results=None)



@app.route('/item_name', methods=['GET', 'POST'])
def item_name():
    if request.method == 'POST':
        trackcode = request.form['trackcode']
        item_name = request.form['item_name']

        # Найдите запись в базе данных с соответствующим trackcode
        piar = Piar.query.filter_by(trackcode=trackcode).first()

        if piar:
            piar.item_name = item_name
            db.session.commit()

        return redirect(url_for('search'))
    return render_template('item_name.html')


@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        article = Article(title=title)
        db.session.add(article)
        db.session.commit()
        return redirect(url_for('update', id=article.id))
    else:
        return render_template('create.html')


@app.route('/admin/<int:id>/trackcode', methods=['GET', 'POST'])
@login_required
def update(id):
    piar = Piar.query.get(id)
    if request.method == 'POST':
        try:
            file = request.files['trackcode']  # Получаем файл XLSX из формы
            if file:
                # Читаем данные из файла XLSX
                data = pd.read_excel(file)

                # Определите начальную ячейку столбца, например, 'A2'
                start_column = 'B6'

                # Фильтруем столбцы, начиная с определенной ячейки
                data = data.loc[:, data.columns >= start_column]

                # Перебираем строки в данных и обновляем таблицу в базе данных
                for index, row in data.iterrows():
                    trackcode = row.iloc[0]  # Получаем значение из первого столбца (колонка начинается с start_column)

                    # Проверяем, что значение в ячейке не является пустым
                    if not pd.isnull(trackcode):
                        point = request.form['point']
                        piar = Piar(trackcode=trackcode, point=point, article_id=id)
                        db.session.add(piar)

                db.session.commit()
        except Exception as e:
            return str(e)  # Обработка ошибок загрузки файла или обновления базы данных

        return redirect(url_for('admin'))
    else:
        return render_template('trackcode.html')



@app.route('/admin/<int:id>/point_change', methods=['GET', 'POST'])
@login_required
def point_change(id):
    article = Article.query.get(id)
    if request.method == 'POST':
        new_point = request.form['point']

        try:
            piars_to_update = Piar.query.filter_by(article_id=id).all()

            for piar in piars_to_update:
                piar.point = new_point

            db.session.commit()
            return redirect(url_for('admin'))
        except Exception as e:
            return 'Error: {}'.format(str(e))
    piars = Piar.query.filter_by(article_id=id).all()
    return render_template('point_change.html',piars=piars, article=article)


def get_data(article_id):

    piar_data = Piar.query.filter_by(article_id=article_id).all()
    return render_template('point_change.html', piar_data=piar_data)


@app.route('/admin')
@login_required
def admin():
    articles = Article.query.order_by(Article.date.desc()).all()
    return render_template('admin.html', articles=articles)

@app.route('/admin/<int:id>')
@login_required
def post_detail(id):
    article=Article.query.get(id)
    return render_template('admin_detail.html', article=article)

@app.route('/admin/<int:id>/del')
@login_required
def post_delete(id):
    article = Article.query.get_or_404(id)

    # Удаление связанных данных из таблицы 'piar'
    piar_entries = Piar.query.filter_by(article_id=id).all()
    for piar_entry in piar_entries:
        db.session.delete(piar_entry)

    try:
        # Удаление данных из таблицы 'Article'
        db.session.delete(article)
        db.session.commit()
        return redirect('/admin')
    except:
        return 'error'


if __name__ == '__main__':
    app.run(debug=True, host='192.168.0.18')
