from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
import os
from os.path import join, dirname, realpath
import pandas as pd
import openpyxl

flask_sqlalchemy = SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
engine = create_engine('sqlite:///database.db', echo=True)
Session = sessionmaker(bind=engine)
session = Session()

UPLOAD_FOLDER = 'static/files'
app.config['UPLOAD_FOLDER'] =  UPLOAD_FOLDER


data = pd.read_excel('orders.xlsx')
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
    # article = db.relationship('Article', back_populates='piar')

@app.route('/', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        # Получите значение, введенное пользователем в поле ввода поиска
        query = request.form['query']

        # Выполните поиск в базе данных
        # results = [item for item in piar if query.lower() in item.trackcode.lower()]
        results = db.session.query(Piar).filter(Piar.trackcode.ilike(f'%{query}%')).all()

        return render_template('index.html', results=results, query=query)

    return render_template('index.html', results=None)



@app.route('/create', methods=['GET', 'POST'])
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
def update(id):
    piar = Piar.query.get(id)
    if request.method == 'POST':
        try:
            file = request.files['trackcode']  # Получаем файл XLSX из формы
            if file:
                # Читаем данные из файла XLSX
                data = pd.read_excel(file)

                # Перебираем строки в данных и обновляем таблицу в базе данных
                for index, row in data.iterrows():
                    trackcode = row['track-code']
                    point = request.form['point']
                    piar = Piar(trackcode=trackcode, point=point, article_id=id)
                    db.session.add(piar)

                db.session.commit()
        except Exception as e:
            return str(e)  # Обработка ошибок загрузки файла или обновления базы данных

        return redirect(url_for('admin'))
    else:
        return render_template('trackcode.html')


@app.route('/view')
def view():
    return render_template('view.html')


@app.route('/admin/<int:id>/point_change', methods=['GET', 'POST'])
def point_change(id):
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

    return render_template('point_change.html')


def get_data(article_id):

    piar_data = Piar.query.filter_by(article_id=article_id).all()
    return render_template('point_change.html', piar_data=piar_data)


@app.route('/admin')
def admin():
    articles = Article.query.order_by(Article.date.desc()).all()
    return render_template('admin.html', articles=articles)

@app.route('/admin/<int:id>')
def post_detail(id):
    article=Article.query.get(id)
    return render_template('admin_detail.html', article=article)

@app.route('/admin/<int:id>/del')
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
    app.run(debug=True)
