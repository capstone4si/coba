from flask import render_template, request, redirect, url_for, flash, session, Blueprint, jsonify
from app import app, db, bcrypt  
from app.models import Kategori
def buatKategori():
    if request.method == 'POST':
        
        data = request.form
        
        nama_kategori = data.get("nama_kategori")

        kategoriBaru = Kategori(nama_kategori=nama_kategori)
        db.session.add(kategoriBaru)
        db.session.commit() 

            # Dapatkan ID sebelum commit
       
        return redirect(url_for('kategori'))
    return render_template('./admin/pages/Kategori/tambah.html')
def buatKategoriApi():
    if request.method == 'POST':
       
        data = request.get_json()
       
        
        nama = data.get("nama_kategori")

        kategoriBaru = Kategori(nama_kategori=nama)
        db.session.add(kategoriBaru)
        db.session.flush() 

        kategori_id = kategoriBaru.id_kategori
        
        return jsonify({"message": "Kategori Berhasil di buat", "body":{
                "kategori_id":kategori_id,
                "nama_kategori":nama
        }}), 201
        
        
    return render_template('./admin/pages/Kategori/tambah.html')

def bacaDataApi():
    kategoriData = Kategori.query.all()
    return jsonify({
    "message": "Data berhasil Dibaca", 
    "body": [kategori.to_dict() for kategori in kategoriData]
})

def bacaData():
    kategoriData= Kategori.query.all()
    return render_template('./admin/pages/Kategori/index.html', kategoriData=kategoriData)


def updateData(id_kategori):
    datakategori = Kategori.query.get_or_404(id_kategori)
    if request.method == 'POST':
        datakategori.nama_kategori = request.form.get('nama_kategori')
        db.session.commit()
        return redirect(url_for('kategori'))
    return render_template('./admin/pages/Kategori/update.html', datakategori=datakategori)

def updateDataApi(id_kategori):
   
    data = request.get_json()
    datakategori = Kategori.query.get_or_404(id_kategori)
    if not datakategori:
        return jsonify({"error": "Kategori not found"}), 404
    datakategori.nama_kategori = data.get("nama_kategori", datakategori.nama_kategori)
    
    db.session.commit()  
    
    return jsonify({
        "message": "Kategori Berhasil di update", 
        "body": {
            "kategori_id": datakategori.id_kategori,
            "nama_kategori": datakategori.nama_kategori
        }
    }), 200


def deleteData(id_kategori):
    datakategori = Kategori.query.get_or_404(id_kategori)
    db.session.delete(datakategori)
    db.session.commit()
    return redirect(url_for('kategori'))
    
def deleteDataApi(id_kategori):
    datakategori = Kategori.query.get_or_404(id_kategori)
    if not datakategori:
        return jsonify({"error": "Kategori tidak ada"}), 404
    db.session.delete(datakategori)
    db.session.commit()
    return jsonify({
        "message": "Kategori Berhasil di Hapus"
    }), 200
    