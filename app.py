import os
from io import BytesIO
import zipfile
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory, abort, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from config import Config
from models import db, User, UserProfile, HealthRecord
from forms import RegisterForm, LoginForm, ProfileForm, UploadRecordForm
from utils import allowed_file, make_upload_folder, save_uploaded_file

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure upload folder exists
    make_upload_folder(app)

    # Initialize DB
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # Login manager
    login_manager = LoginManager(app)
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # -------------------------
    # Routes
    # -------------------------

    @app.route("/")
    def index():
        return render_template("index.html")

    # ---------- REGISTER ----------
    @app.route("/register", methods=["GET","POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        form = RegisterForm()
        if form.validate_on_submit():
            if User.query.filter_by(email=form.email.data.lower()).first():
                flash("Email already registered", "warning")
                return render_template("register.html", form=form)
            user = User(
                name=form.name.data,
                email=form.email.data.lower(),
                phone=form.phone.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()

            # Create empty profile
            profile = UserProfile(user_id=user.id)
            db.session.add(profile)
            db.session.commit()

            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        return render_template("register.html", form=form)

    # ---------- LOGIN ----------
    @app.route("/login", methods=["GET","POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data.lower()).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)
                flash("Logged in successfully.", "success")
                return redirect(url_for("dashboard"))
            flash("Invalid credentials", "danger")
        return render_template("login.html", form=form)

    # ---------- LOGOUT ----------
    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Logged out.", "info")
        return redirect(url_for("index"))

    # ---------- DASHBOARD ----------
    @app.route("/dashboard")
    @login_required
    def dashboard():
        records = HealthRecord.query.filter_by(user_id=current_user.id).order_by(HealthRecord.uploaded_at.desc()).limit(5).all()
        total_records = HealthRecord.query.filter_by(user_id=current_user.id).count()
        return render_template("dashboard.html", records=records, total_records=total_records)

    # ---------- PROFILE ----------
    @app.route("/profile", methods=["GET","POST"])
    @login_required
    def profile():
        form = ProfileForm()
        if form.validate_on_submit():
            profile = current_user.profile or UserProfile(user_id=current_user.id)
            profile.age = form.age.data
            profile.gender = form.gender.data
            profile.blood_group = form.blood_group.data
            profile.known_conditions = form.known_conditions.data
            profile.address = form.address.data
            db.session.add(profile)
            db.session.commit()
            flash("Profile updated", "success")
            return redirect(url_for("profile"))

        # Populate form with existing data
        if current_user.profile:
            form.age.data = current_user.profile.age
            form.gender.data = current_user.profile.gender
            form.blood_group.data = current_user.profile.blood_group
            form.known_conditions.data = current_user.profile.known_conditions
            form.address.data = current_user.profile.address

        return render_template("profile.html", form=form)

    # ---------- UPLOAD ----------
    @app.route("/upload", methods=["GET","POST"])
    @login_required
    def upload():
        form = UploadRecordForm()
        if request.method == "POST":
            file = request.files.get("file")
            if not file or file.filename == "":
                flash("Please select a file to upload", "warning")
                return render_template("upload.html", form=form)
            if not allowed_file(file.filename):
                flash("File type not allowed. Allowed: pdf, png, jpg, jpeg", "danger")
                return render_template("upload.html", form=form)

            filename = save_uploaded_file(file, app.config["UPLOAD_FOLDER"])
            if not filename:
                flash("Failed to save file", "danger")
                return render_template("upload.html", form=form)

            # Save DB record
            rec = HealthRecord(
                user_id=current_user.id,
                filename=filename,
                original_filename=file.filename,
                file_type=request.form.get("file_type"),
                doctor_name=request.form.get("doctor_name"),
                hospital_name=request.form.get("hospital_name"),
                notes=request.form.get("notes"),
                visit_date=request.form.get("visit_date") or None
            )
            if rec.visit_date:
                try:
                    rec.visit_date = datetime.strptime(rec.visit_date, "%Y-%m-%d").date()
                except:
                    rec.visit_date = None

            db.session.add(rec)
            db.session.commit()
            flash("File uploaded successfully", "success")
            return redirect(url_for("records"))
        return render_template("upload.html", form=form)

    # ---------- RECORDS ----------
    @app.route("/records")
    @login_required
    def records():
        q = HealthRecord.query.filter_by(user_id=current_user.id)

        # Filters
        file_type = request.args.get("type", "").strip()
        doctor = request.args.get("doctor", "").strip()
        hospital = request.args.get("hospital", "").strip()
        keyword = request.args.get("q", "").strip()
        date_from = request.args.get("from", "").strip()
        date_to = request.args.get("to", "").strip()

        if file_type:
            q = q.filter(HealthRecord.file_type.ilike(f"%{file_type}%"))
        if doctor:
            q = q.filter(HealthRecord.doctor_name.ilike(f"%{doctor}%"))
        if hospital:
            q = q.filter(HealthRecord.hospital_name.ilike(f"%{hospital}%"))
        if keyword:
            q = q.filter(HealthRecord.notes.ilike(f"%{keyword}%"))
        if date_from:
            try:
                df = datetime.strptime(date_from, "%Y-%m-%d").date()
                q = q.filter(HealthRecord.visit_date >= df)
            except: pass
        if date_to:
            try:
                dt = datetime.strptime(date_to, "%Y-%m-%d").date()
                q = q.filter(HealthRecord.visit_date <= dt)
            except: pass

        records = q.order_by(HealthRecord.uploaded_at.desc()).all()
        return render_template("records.html", records=records)

    # ---------- VIEW RECORD ----------
    @app.route("/record/<int:record_id>")
    @login_required
    def view_record(record_id):
        rec = HealthRecord.query.get_or_404(record_id)
        if rec.user_id != current_user.id and not current_user.is_admin:
            abort(403)
        return render_template("view_record.html", rec=rec)

    # ---------- DOWNLOAD ----------
    @app.route("/download/<int:record_id>")
    @login_required
    def download(record_id):
        rec = HealthRecord.query.get_or_404(record_id)
        if rec.user_id != current_user.id and not current_user.is_admin:
            abort(403)
        return send_from_directory(
            directory=app.config["UPLOAD_FOLDER"],
            path=rec.filename,
            as_attachment=True,
            download_name=rec.original_filename
        )

    # ---------- DELETE RECORD ----------
    @app.route("/delete/<int:record_id>", methods=["POST"])
    @login_required
    def delete_record(record_id):
        rec = HealthRecord.query.get_or_404(record_id)
        if rec.user_id != current_user.id and not current_user.is_admin:
            abort(403)
        try:
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], rec.filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass
        db.session.delete(rec)
        db.session.commit()
        flash("Record deleted", "info")
        return redirect(url_for("records"))

    # ---------- EXPORT ZIP ----------
    @app.route("/export_zip", methods=["POST"])
    @login_required
    def export_zip():
        ids = request.form.getlist("record_ids")
        if not ids:
            flash("No records selected for export", "warning")
            return redirect(url_for("records"))

        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
            for rid in ids:
                rec = HealthRecord.query.get(int(rid))
                if not rec: continue
                if rec.user_id != current_user.id and not current_user.is_admin:
                    continue
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], rec.filename)
                if os.path.exists(filepath):
                    zf.write(filepath, arcname=rec.original_filename)
        memory_file.seek(0)
        return send_file(memory_file, as_attachment=True, download_name=f"phr_records_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.zip", mimetype="application/zip")

    # ---------- ADMIN ----------
    @app.route("/admin")
    @login_required
    def admin():
        if not current_user.is_admin:
            abort(403)
        total_users = User.query.count()
        total_records = HealthRecord.query.count()
        return render_template("admin.html", total_users=total_users, total_records=total_records)

    return app

# -------------------------
# Run app
# -------------------------
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
