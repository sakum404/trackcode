@app.route('/admin/<int:id>/trackcode', methods=['GET', 'POST'])
def update(id):
    piar = Piar.query.get(id)
    if request.method == 'POST':
        for update, row in data.iterrows():
            trackcode = row['track-code']
            point = request.form['point']
            piar = Piar(trackcode=trackcode, point=point, article_id=id)

        try:
            db.session.add(piar)
            db.session.commit()
        except:
            return EOFError
        return redirect(url_for('admin'))
    else:
        return render_template('trackcode.html')


class Article(db.Model):
    __tablename__ = 'article'
    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    date = Column(DateTime, default=datetime.utcnow)
    piar = relationship('Piar', backref='piar', lazy="dynamic")



class Piar(db.Model):
    __tablename__ = 'piar'
    id = Column(Integer, primary_key=True)
    trackcode = Column(String(100))
    point = Column(String(100))
    article_id = Column(Integer, ForeignKey('article.id'))


@app.route('/admin/<int:id>/point_change', methods=['GET', 'POST'])
def point_change(id):
    piar = Piar.query.get(id)
    if request.method == 'POST':
        piar.point = request.form['point']

        try:
            db.session.commit()
            return redirect(url_for('admin'))
        except:
            return 'Error'
    return render_template('point_change.html', piar=piar)