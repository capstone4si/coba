from functools import wraps
from random import randint
from flask import render_template, request, redirect, url_for, flash, session, Blueprint, jsonify
from app import app, db, bcrypt, mail,cache
from app.utils import allowed_file, simpanGambar
from app.models import RoleEnum, User
from flask_mail import Message
import datetime
import jwt
from werkzeug.security import generate_password_hash

def role_required(allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
           
            if 'role' not in session or session['role'] not in allowed_roles:
                flash('Akses ditolak! Kamu tidak memiliki izin untuk mengakses halaman ini.', 'danger')
                return redirect(url_for('home'))  
            return func(*args, **kwargs)
        return wrapper
    return decorator

def loginF():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        users = User.query.filter_by(email=email).first()

        if users and users.check_password(password):
            session['user_id'] = users.id
            session['email'] = users.email
            session['role'] = users.role.name  # Menyimpan nama role di session
            session.permanent = True  # Set session agar persistent
            app.permanent_session_lifetime = datetime.timedelta(hours=3)  # Durasi session

            if users.role == RoleEnum.super_admin:
                flash('Selamat datang, Super Admin!', 'success')
                return redirect(url_for('admin'))
            elif users.role == RoleEnum.pihak_berwajib:
                flash('Selamat datang, Pihak Berwajib!', 'success')
                return redirect(url_for('home'))
            elif users.role == RoleEnum.user:
                flash('Selamat datang, User!', 'success')
                return redirect(url_for('home'))
        else:
            flash('Gagal login! Cek kembali email dan password.', 'danger')
            return redirect(url_for('login'))
    return render_template('auth/login.html')

def loginApi():
    dt = request.get_json()
    email = dt.get('email')
    password = dt.get('password')
    
    user = User.query.filter_by(email=email).first()

    if not email or not password:
        return jsonify({'message': 'Wajib Di Isi Semua', 'status': 'Perhatian'}), 400

    if user and user.check_password(password):
        session['users_id'] = user.id
        session['email'] = user.email

        return jsonify({
            "message": "Login Berhasil",
            "status": "success",
            "user": {
                "id": user.id,
                "email": user.email,
                "nama": user.nama,
                "no_telp": user.no_telp,
                "img_profil": user.img_profil,
            }
        }), 200

def registerApi():
    data = request.get_json()  
    email = data.get('email')
    nama = data.get('nama')
    no_telp = data.get('no_telp')
    password = data.get('password')

    if not email or not nama or not password:
        return jsonify({'message': 'Wajib Di Isi Semua', 'status': 'Perhatian'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email Sudah Ada!', 'status': 'danger'}), 400

    try:
        user = User(nama=nama, email=email, no_telp=no_telp)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        return jsonify({'message': 'Kamu berhasil Buat Akun!', 'status': 'success'}), 201
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}', 'status': 'danger'}), 500

def registerF():
    if request.method == 'POST':
        email = request.form.get('email')
        nama = request.form.get('nama')
        no_telp = request.form.get('no_telp')
        password = request.form.get('password')

        if not email or not nama or not password:
            flash('Wajib Di Isi Semua', 'Perhatian')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('Email Sudah Ada!', 'danger')
            return redirect(url_for('auth.register'))
        
        try:
            user = User(
                nama=nama, 
                email=email, 
                no_telp=no_telp, 
                password=password, 
                role='user'  
            )
            user.set_password(password)  
            db.session.add(user)  
            db.session.commit()  

            flash('Kamu berhasil Buat Akun!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()  
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('register'))

    return render_template('auth/register.html')

def profilF():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

        if request.method == 'POST':
            nama = request.form.get('nama')
            email = request.form.get('email')
            no_telp = request.form.get('no_telp')

            if 'img_profil' in request.files:
                picture_file = request.files['img_profil']
                if picture_file.filename != '':
                    picture_file = simpanGambar(picture_file)
                    user.img_profil = picture_file

            user.nama = nama
            user.email = email
            user.no_telp = no_telp

            db.session.commit()
            return redirect(url_for('profil'))

        img_profil = url_for('static', filename='gambarUser/' + (user.img_profil if user.img_profil else 'default.jpg'))

        return render_template('profil.html', user=user, img_profil=img_profil)

    return redirect(url_for('login'))

def bacaUser():
    users = User.query.all()
    return jsonify({"message": "berhasil"})

def request_reset_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            token = jwt.encode(
                {
                    "user_id": user.id,
                    "exp": datetime.utcnow() + datetime.timedelta(hours=1)
                },
                app.config['SECRET_KEY'], algorithm='HS256'
            )

            try:
                msg = Message(
                    subject="Reset Password SIPANDA",
                    sender=app.config['MAIL_DEFAULT_SENDER'],
                    recipients=[email]
                )

                # Memperbaiki URL untuk menggunakan endpoint yang benar
                reset_link = url_for('resetPassword', token=token, _external=True)
                msg.body = f"Klik tautan berikut untuk mereset password Anda: {reset_link}"

                # Kirim email
                mail.send(msg)

                flash('Email reset password telah dikirim.', 'success')
            except Exception as e:
                flash(f'Gagal mengirim email: {str(e)}', 'danger')
        else:
            flash('Email tidak ditemukan.', 'danger')

    return render_template('auth/request_reset_password.html')

def reset_password(token):
    try:
        # Dekode token untuk mendapatkan user_id
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user = User.query.get(data['user_id'])

        if not user:
            flash('Token tidak valid atau telah kadaluarsa.', 'danger')
            return redirect(url_for('auth.request_reset_password'))

        if request.method == 'POST':
            new_password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            # Validasi apakah password baru dan konfirmasi cocok
            if not new_password or new_password != confirm_password:
                flash('Password tidak cocok atau kosong.', 'danger')
                return redirect(url_for('auth.reset_password', token=token))

            user.set_password(new_password)
            db.session.commit()

            flash('Password berhasil diubah. Silakan login.', 'success')
            return redirect(url_for('login'))

        return render_template('auth/reset_password.html', token=token)

    except jwt.ExpiredSignatureError:
        flash('Token telah kadaluarsa.', 'danger')
        return redirect(url_for('auth.request_reset_password'))
    except jwt.InvalidTokenError:
        flash('Token tidak valid.', 'danger')
        return redirect(url_for('auth.request_reset_password'))
    


def req_api_pass():
    email = request.json.get('email')  # Mengambil data dari JSON
    user = User.query.filter_by(email=email).first()

    if user:
        # Generate token numerik (6 digit)
        token = str(randint(100000, 999999))

        # Simpan token di cache
        cache_key = f"reset_token_{email}"
        cache.set(cache_key, token)

        try:
            msg = Message(
                subject="Reset Password SIPANDA",
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[email]
            )
            msg.body = f"Token reset password Anda: {token}. Token berlaku selama 15 menit."
            mail.send(msg)

            return jsonify({"message": "Email reset password telah dikirim."}), 200
        except Exception as e:
            return jsonify({"error": f"Gagal mengirim email: {str(e)}"}), 500
    else:
        return jsonify({"error": "Email tidak ditemukan."}), 404

def reset_password_api():
    data = request.json
    email = data.get('email')
    token = data.get('token')  # Token dari user
    new_password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not new_password or new_password != confirm_password:
        return jsonify({"error": "Password tidak cocok atau kosong."}), 400

    # Ambil token dari cache
    cache_key = f"reset_token_{email}"
    cached_token = cache.get(cache_key)

    if not cached_token or cached_token != token:
        return jsonify({"error": "Token tidak valid atau telah kadaluarsa."}), 400

    # Reset password
    user = User.query.filter_by(email=email).first()
    if user:
        user.set_password(new_password)
        db.session.commit()

        # Hapus token dari cache setelah digunakan
        cache.delete(cache_key)

        return jsonify({"message": "Password berhasil diubah. Silakan login."}), 200
    else:
        return jsonify({"error": "Email tidak ditemukan."}), 404


def updateProfilApi():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"msg": "No input data provided"}), 400

        user_id = data.get('id')
        email = data.get('email')
        nama = data.get('nama')
        no_telp = data.get('no_telp')

        if not user_id or not isinstance(user_id, int):
            return jsonify({"msg": "Invalid or missing user ID"}), 400

        if not email or '@' not in email:
            return jsonify({"msg": "Invalid email address"}), 400

        if not nama or len(nama) < 3:
            return jsonify({"msg": "Name must be at least 3 characters"}), 400

      

        user = User.query.get(user_id)
        if not user:
            return jsonify({"msg": "User not found"}), 404

        user.email = email
        user.nama = nama
        user.no_telp = no_telp

        db.session.commit()

        return jsonify({
            "msg": "Profile updated successfully",
            "status": "success",
            "user": {
                "id": user.id,
                "email": user.email,
                "nama": user.nama,
                "no_telp": user.no_telp,
                "img_profil": user.img_profil,
            }
        }), 200

    except Exception as e:
        return jsonify({"msg": f"An error occurred: {str(e)}"}), 500
    
def data_user():
    # Mengambil data total pengguna berdasarkan role
    total_super_admin = User.query.filter_by(role=RoleEnum.super_admin).count()
    total_admin = User.query.filter_by(role=RoleEnum.pihak_berwajib).count()
    total_user = User.query.filter_by(role=RoleEnum.user).count()

    # Mengambil semua data pengguna
    users = User.query.all()

    # Me-render template pengguna.html dengan data
    return render_template(
        '/admin/pages/Pengguna/pengguna.html',
        total_super_admin=total_super_admin,
        total_admin=total_admin,
        total_user=total_user,
        users=users
    )

def edit_pengguna(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        # Ambil data dari form
        nama = request.form['nama']
        email = request.form['email']
        no_telp = request.form['no_telp']
        role = request.form['role']
        
        # Proses gambar profil jika ada
        img_profil = request.files.get('img_profil')

        # Update data pengguna
        user.nama = nama
        user.email = email
        user.no_telp = no_telp
        user.role = role

        if img_profil and allowed_file(img_profil.filename):  # Pastikan file valid
            # Simpan gambar baru dan perbarui path gambar pengguna
            gambar_filename = simpanGambar(img_profil)
            user.img_profil = gambar_filename

        # Simpan perubahan ke database
        db.session.commit()

        flash('Data pengguna berhasil diperbarui!', 'success')
        return redirect(url_for('pengguna'))  # Ganti dengan rute yang sesuai untuk daftar pengguna

    return render_template('admin/pages/Pengguna/update.html', user=user)