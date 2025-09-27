from flask import Flask, render_template, request, redirect, url_for, flash, Response
import pyodbc
from markupsafe import Markup
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Required for flash messages

# SQL Server connection setup
conn = pyodbc.connect(
    'Driver={ODBC Driver 17 for SQL Server};'
    'Server=localhost\\SQLEXPRESS;'
    'Database=CrudApp;'
    'Trusted_Connection=yes;'
)
cursor = conn.cursor()

@app.route('/')
def index():
    cursor.execute("SELECT id, filename FROM FileUploads WHERE Deleted IS NULL OR Deleted = 'N'")
    files = [dict(id=row[0], filename=row[1]) for row in cursor.fetchall()]
    return render_template('upload.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    filename = file.filename
    file_data = file.read()

    try:
        cursor.execute(
            "INSERT INTO FileUploads (filename, filedata, Deleted) VALUES (?, ?, ?)",
            (filename, pyodbc.Binary(file_data), 'N')
        )
        conn.commit()
        flash(Markup(f"✅ <strong>{filename}</strong> uploaded successfully!"), 'success')
    except Exception as e:
        flash(f"❌ Upload failed: {str(e)}", 'error')

    return redirect(url_for('index'))

# @app.route('/view/<int:file_id>')
# def view_image(file_id):
#     try:
#         cursor.execute("SELECT filedata FROM FileUploads WHERE id = ? AND (Deleted IS NULL OR Deleted = 'N')", (file_id,))
#         row = cursor.fetchone()
#         if row:
#             return Response(row.filedata, mimetype='image/jpeg')  # Adjust mimetype if needed
#         else:
#             return "Image not found", 404
#     except Exception as e:
#         return f"Error: {str(e)}", 500

@app.route('/view/<int:file_id>')
def view_image(file_id):
    try:
        cursor.execute("SELECT filename, filedata FROM FileUploads WHERE id = ? AND (Deleted IS NULL OR Deleted = 'N')", (file_id,))
        row = cursor.fetchone()
        if row:
            filename, filedata = row
            ext = os.path.splitext(filename)[1].lower()

            # Set correct MIME type
            if ext == '.pdf':
                mimetype = 'application/pdf'
            elif ext in ['.jpg', '.jpeg', '.png', '.gif']:
                mimetype = f'image/{ext.strip(".")}'
            else:
                mimetype = 'application/octet-stream'  # fallback

            return Response(filedata, mimetype=mimetype)
        else:
            return "File not found", 404
    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route('/download/<int:file_id>')
def download_file(file_id):
    try:
        cursor.execute("SELECT filename, filedata FROM FileUploads WHERE id = ? AND (Deleted IS NULL OR Deleted = 'N')", (file_id,))
        row = cursor.fetchone()
        if row:
            filename, file_data = row
            flash(Markup(f"⬇️ <strong>{filename}</strong> downloaded successfully!"), 'info')
            return Response(
                file_data,
                mimetype='application/octet-stream',
                headers={"Content-Disposition": f"attachment;filename={filename}"}
            )
        else:
            flash("❌ File not found.", 'error')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f"❌ Download failed: {str(e)}", 'error')
        return redirect(url_for('index'))

@app.route('/delete/<int:file_id>')
def delete_file(file_id):
    try:
        cursor.execute("UPDATE FileUploads SET Deleted = 'Y' WHERE id = ?", (file_id,))
        conn.commit()
        flash("🗑️ File deleted successfully.", 'success')
    except Exception as e:
        flash(f"❌ Delete failed: {str(e)}", 'error')
    return redirect(url_for('index'))

@app.route('/update/<int:file_id>', methods=['GET', 'POST'])
def update_file(file_id):
    if request.method == 'POST':
        file = request.files['file']
        filename = file.filename
        file_data = file.read()

        try:
            cursor.execute("UPDATE FileUploads SET filename = ?, filedata = ? WHERE id = ?", (filename, pyodbc.Binary(file_data), file_id))
            conn.commit()
            flash(f"✏️ File updated successfully!", 'success')
        except Exception as e:
            flash(f"❌ Update failed: {str(e)}", 'error')
        return redirect(url_for('index'))

    else:
        cursor.execute("SELECT filename FROM FileUploads WHERE id = ?", (file_id,))
        row = cursor.fetchone()
        if row:
            return render_template('update.html', file_id=file_id, filename=row[0])
        else:
            flash("❌ File not found.", 'error')
            return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)










