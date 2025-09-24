import os
import io
import uuid
from datetime import datetime

from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from flask_cors import CORS
from rembg import remove
from PIL import Image
import requests

app = Flask(__name__)
CORS(app)  # ✅ فقط CORS اضافه شد
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

# API Key از environment variables
REM_BG_API_KEY = os.environ.get('REM_BG_API_KEY', 'b555c5ef-173d-45e7-8526-bd12490403f8')

# ایجاد پوشه آپلود
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_unique_filename(original_filename):
    ext = original_filename.rsplit('.', 1)[1].lower()
    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"image_{timestamp}_{unique_id}.{ext}"


def remove_background_api(input_image):
    """استفاده از API ریموت rembg"""
    try:
        img_byte_arr = io.BytesIO()
        input_image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        response = requests.post(
            'https://api.rembg.ai/remove',
            files={'image': img_byte_arr},
            data={'size': 'preview'},
            headers={'X-API-Key': REM_BG_API_KEY},
            timeout=30
        )

        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
        else:
            return remove(input_image)

    except Exception as e:
        print(f"API Error, using local method: {e}")
        return remove(input_image)


@app.route('/health')
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}, 200


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/remove-bg', methods=['POST'])
def remove_background():
    try:
        print("🔍 درخواست حذف بک‌گراند دریافت شد")

        if 'image' not in request.files:
            print("❌ فایل تصویر دریافت نشد")
            flash('لطفاً یک تصویر انتخاب کنید', 'error')
            return redirect(request.url)

        file = request.files['image']

        if file.filename == '':
            print("❌ نام فایل خالی است")
            flash('لطفاً یک تصویر انتخاب کنید', 'error')
            return redirect(request.url)

        if not allowed_file(file.filename):
            print(f"❌ فرمت فایل مجاز نیست: {file.filename}")
            flash('فرمت فایل مجاز نیست. لطفاً از فرمت‌های PNG, JPG, JPEG, WEBP استفاده کنید', 'error')
            return redirect(request.url)

        print(f"✅ فایل معتبر است: {file.filename}")

        # خواندن تصویر
        input_image = Image.open(file.stream)
        print(f"📊 ابعاد تصویر: {input_image.size}")

        # حذف بک‌گراند
        print("⏳ در حال حذف بک‌گراند...")
        output_image = remove_background_api(input_image)
        print("✅ بک‌گراند با موفقیت حذف شد")

        # ذخیره تصاویر
        original_filename = generate_unique_filename(file.filename)
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], f"original_{original_filename}")
        input_image.save(original_path)

        result_filename = f"result_{original_filename}"
        result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_filename)
        output_image.save(result_path, 'PNG')

        print(f"💾 تصاویر ذخیره شدند: {original_filename}")

        # حذف فایل‌های قدیمی
        cleanup_old_files()

        print("🎉 پردازش کامل شد")
        return render_template('result.html',
                               original_image=original_path,
                               result_image=result_path,
                               filename=original_filename)

    except Exception as e:
        print(f"❌ خطا در پردازش تصویر: {str(e)}")
        flash(f'خطا در پردازش تصویر: {str(e)}', 'error')
        return redirect(url_for('index'))


def cleanup_old_files():
    """حذف فایل‌های قدیمی تر از 1 ساعت"""
    try:
        current_time = datetime.now().timestamp()
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(file_path):
                if current_time - os.path.getctime(file_path) > 3600:
                    os.remove(file_path)
                    print(f"🗑️ فایل قدیمی حذف شد: {filename}")
    except Exception as e:
        print(f"⚠️ خطا در حذف فایل‌های قدیمی: {e}")


@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"result_{filename}")
        print(f"📥 درخواست دانلود: {filename}")
        return send_file(file_path, as_attachment=True, download_name=f"no-bg_{filename}")
    except Exception as e:
        print(f"❌ خطا در دانلود: {e}")
        return "خطا در دانلود فایل", 500


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    print("🚀 برنامه در حال راه‌اندازی...")
    print(f"📁 پوشه آپلود: {app.config['UPLOAD_FOLDER']}")
    app.run(debug=True, host='0.0.0.0', port=5000)
