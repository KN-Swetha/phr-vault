import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime
from config import Config

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[-1].lower() in Config.ALLOWED_EXTENSIONS

def make_upload_folder(app):
    folder = app.config["UPLOAD_FOLDER"]
    # If there's a file with this name, error clearly
    if os.path.isfile(folder):
        raise RuntimeError(f"UPLOAD_FOLDER path '{folder}' is a file, not a directory.")
    os.makedirs(folder, exist_ok=True)
    return folder

def save_uploaded_file(file_storage, upload_folder):
    if not file_storage:
        return None
    filename = secure_filename(file_storage.filename)
    ext = filename.rsplit(".", 1)[-1]
    unique_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}.{ext}"
    path = os.path.join(upload_folder, unique_name)
    file_storage.save(path)
    return unique_name

