from flask import app, request, flash, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from app.utils import simpanGambar
import os
from app.models import Berita  
from app import db


def BacaDataBerita():
    news = Berita.query.order_by(Berita.tanggal.desc()).all()  
    total_berita = len(news)
    return render_template('/admin/pages/Berita/berita.html', news=news, total_berita=total_berita)
def get_news():
    return Berita.query.order_by(Berita.tanggal.desc()).all()
def tambahBerita():
    if request.method == 'POST':
        title = request.form.get('title')
        date = request.form.get('date')
        image = request.files.get('image')
        content = request.form.get('content')

        konten_html = "<p>" + content.replace("\n", "</p><p>") + "</p>"

        filename = None
        if image:
            filename = simpanGambar(image)  

        new_berita = Berita(judul=title, tanggal=date, gambar=filename, konten=konten_html)
        db.session.add(new_berita)
        db.session.commit()
        flash('Berita berhasil ditambahkan!', 'success')
        return redirect(url_for('Berita'))

    return render_template('admin/pages/Berita/create.html')

def updateBerita(berita_id):
    berita = Berita.query.get_or_404(berita_id)

    if request.method == 'POST':
        title = request.form.get('title')
        date = request.form.get('date')
        image = request.files.get('image')
        content = request.form.get('content')

        konten_html = "<p>" + content.replace("\n", "</p><p>") + "</p>"

        berita.judul = title
        berita.tanggal = date
        berita.konten = konten_html  

        if image:
            filename = simpanGambar(image)  
            berita.gambar = filename

        db.session.commit()

        flash('Berita berhasil diperbarui!', 'success')
        return redirect(url_for('Berita'))

    return render_template('admin/pages/Berita/update.html', berita=berita)

def detailBerita(id):
    berita = Berita.query.filter_by(id=id).first()
    
    if berita is None:
        flash('Berita tidak ditemukan', 'error')
        return redirect(url_for('home'))  
    
    # URL gambar berita
    url_gambar = url_for('static', filename='gambarUser/' + berita.gambar) if berita.gambar else None
    
    return render_template('HalamanBerita.html', berita=berita, url_gambar=url_gambar)