from app.models import HewanModel, Kategori, CiriCiriModel
from flask import render_template, request, redirect, url_for, flash, session, Blueprint, jsonify
from app.utils import simpanGambar, saveHewan
from werkzeug.utils import secure_filename
import os
from app import app, db, bcrypt  
def bacaDataHewan():
    hewans = HewanModel.query.all()
    return render_template('/admin/pages/Hewan/DataHewan.html', hewans=hewans)

def halamanDataHewan():
    search_query = request.args.get('search', '').strip()  # Ambil parameter pencarian dari query string

    if search_query:
        # Filter berdasarkan nama hewan atau nama kategori
        hewans = HewanModel.query.join(Kategori).filter(
            db.or_(
                HewanModel.nama.ilike(f"%{search_query}%"), 
                Kategori.nama_kategori.ilike(f"%{search_query}%")
            )
        ).all()
    else:
        # Jika tidak ada pencarian, tampilkan semua data
        hewans = HewanModel.query.all()
    
    # Tentukan pesan jika tidak ada data ditemukan
    no_data_message = "Tidak ada data ditemukan" if not hewans else None

    # Render template dengan data yang ada
    return render_template(
        'HalamanDataHewan.html', 
        hewans=hewans, 
        no_data_message=no_data_message
    )


def detailHewans(id_hewan):
    hewans = HewanModel.query.get(id_hewan)
    return render_template('DetailHewan.html', hewans=hewans)

def bacaDataHewanApi():
    hewans = HewanModel.query.all()
    kategoris = Kategori.query.all()
    return jsonify({
    "message": "Data berhasil Dibaca", 
    "body": [hewan.to_dict() for hewan in hewans]
})


def ambilDataDariKategori(nama_kategori):
    kategoris = Kategori.query.filter_by(nama_kategori=nama_kategori).first()
    kumpulanHewan = HewanModel.query.filter_by(id_kategori=kategoris.id_kategori).all()
    hewanData = [hewan.to_dict() for hewan in kumpulanHewan]
    return jsonify({"message": "Berhasil", "body" : hewanData}), 200
 

def tambahDataHewan():
    kategoris = Kategori.query.all()
    if request.method == 'POST':
        data = request.form
        nama = data.get('nama')
        nama_latin = data.get('nama_latin')
        deskripsi = data.get('deskripsi')
        status = data.get('status')
        populasi = data.get('populasi')
        habitat = data.get('habitat')
        id_kategori = data.get('id_kategori')
        file_gambar = request.files['url_gambar']
        url_gambar = simpanGambar(file_gambar)

        dtHewan = HewanModel(
            nama=nama,
            nama_latin=nama_latin,
            deskripsi=deskripsi,
            status=status,
            populasi=populasi,
            habitat=habitat,
            id_kategori=id_kategori,
            url_gambar=url_gambar
        )
        db.session.add(dtHewan)
        db.session.commit()

        # Menambahkan ciri-ciri
        ciri_ciri_list = request.form.getlist('ciri_ciri[]')
        for ciri in ciri_ciri_list:
            ciri_obj = CiriCiriModel(id_hewan=dtHewan.id_hewan, ciri=ciri)
            db.session.add(ciri_obj)
        db.session.commit()

        return redirect(url_for('hewan'))

    return render_template('/admin/pages/Hewan/TambahData.html', kategoris=kategoris)



def tambahDataHewanApi():
    kategoris = Kategori.query.all()
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({"error": "Kesalahan Data "}), 404
        nama = data.get('nama')
        nama_latin = data.get('nama_latin')
        deskripsi = data.get('deskripsi')
        status = data.get('status')
        populasi = data.get('populasi')
        habitat = data.get('habitat')
        ciri_ciri = data.get('ciri_ciri')
        id_kategori = data.get('id_kategori')
        file_gambar = request.files['url_gambar']
        url_gambar = simpanGambar(file_gambar)
        if not all([nama,nama_latin,deskripsi,status,populasi,habitat,ciri_ciri,id_kategori,file_gambar]):
            return jsonify({"error": "Ada kesalahan Input, Silahkan Cek Kembali"})
        

        dtHewan = HewanModel(nama=nama, nama_latin=nama_latin, deskripsi=deskripsi, status=status, populasi=populasi, habitat=habitat, ciri_ciri=ciri_ciri, id_kategori=id_kategori, url_gambar=url_gambar)
        db.session.add(dtHewan)
        db.session.commit()


        return jsonify({
            'message': 'Data Hewan berhasil ditambahkan',
            'data': {
                'nama': nama,
                'nama_latin': nama_latin,
                'deskripsi': deskripsi,
                'status': status,
                'populasi': populasi,
                'habitat': habitat,
                'ciri_ciri': ciri_ciri,
                'id_kategori': id_kategori,
                'url_gambar': url_gambar
            }
        }), 201
    
    return render_template('/admin/pages/Hewan/TambahData.html', kategoris=kategoris)

def cariDataHewanApi():
    query = request.args.get('q', '')
    
    if query:
        hewans = HewanModel.query.filter(HewanModel.nama.contains(query)).all()
    else:
        hewans = HewanModel.query.all()

    return jsonify({
        "message": "Data berhasil Dibaca",
        "body": [hewan.to_dict() for hewan in hewans]
    })

def updateDataHewan(id_hewan):
    # Ambil data hewan berdasarkan id_hewan
    hewan = HewanModel.query.get_or_404(id_hewan)
    if not hewan:
        flash('Data hewan tidak ditemukan.', 'error')
        return redirect(url_for('hewan'))  # Redireksi jika data tidak ditemukan

    if request.method == 'POST':
        try:
            data = request.form

            # Perbarui data hewan
            hewan.nama = data.get('nama')
            hewan.nama_latin = data.get('nama_latin')
            hewan.deskripsi = data.get('deskripsi')
            hewan.status = data.get('status')
            hewan.populasi = data.get('populasi')
            hewan.habitat = data.get('habitat')
            hewan.id_kategori = data.get('id_kategori')

            # Cek apakah ada file gambar baru
            if 'url_gambar' in request.files and request.files['url_gambar']:
                file_gambar = request.files['url_gambar']
                if file_gambar:
                    # Simpan gambar baru
                    url_gambar = simpanGambar(file_gambar)
                    hewan.url_gambar = url_gambar

            # Perbarui ciri-ciri
            ciri_ciri_list = request.form.getlist('ciri_ciri[]')
            # Hapus ciri-ciri lama
            CiriCiriModel.query.filter_by(id_hewan=id_hewan).delete()
            # Tambahkan ciri-ciri baru
            for ciri in ciri_ciri_list:
                ciri_obj = CiriCiriModel(id_hewan=hewan.id_hewan, ciri=ciri)
                db.session.add(ciri_obj)

            db.session.commit()
            flash('Data hewan berhasil diperbarui.', 'success')
            return redirect(url_for('hewan'))  # Redireksi setelah berhasil update

        except Exception as e:
            db.session.rollback()  # Rollback jika ada kesalahan
            flash(f'Terjadi kesalahan: {str(e)}', 'error')

    # Ambil data kategori untuk dropdown
    kategoris = Kategori.query.all()

    return render_template('/admin/pages/Hewan/UpdateHewan.html', hewan=hewan, kategoris=kategoris)


def deleteDataHewan(id_hewan):
    hewan = HewanModel.query.get_or_404(id_hewan)
    
    if hewan.url_gambar:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], hewan.url_gambar))

    CiriCiriModel.query.filter_by(id_hewan=id_hewan).delete()

    db.session.delete(hewan)
    db.session.commit()

    flash("Data hewan berhasil dihapus", "success")
    return redirect(url_for('hewan')) 