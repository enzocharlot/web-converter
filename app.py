from flask import Flask, render_template, request, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import yt_dlp
import os
import zipfile

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def download_youtube_audio(url, output_path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_path,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'Pas de fichier'
        file = request.files['file']
        if file.filename == '':
            return 'Pas de fichier sélectionné'
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Créer un dossier temporaire pour stocker les MP3
            output_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'downloads')
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            # Télécharger chaque lien du fichier texte
            with open(filepath, 'r') as f:
                urls = f.readlines()
                for url in urls:
                    url = url.strip()
                    if url:
                        output_path = os.path.join(output_folder, '%(title)s.%(ext)s')
                        download_youtube_audio(url, output_path)

            # Créer un fichier zip contenant tous les MP3
            zip_path = os.path.join(app.config['UPLOAD_FOLDER'], 'downloads.zip')
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for root, dirs, files in os.walk(output_folder):
                    for file in files:
                        zipf.write(os.path.join(root, file),
                                   os.path.relpath(os.path.join(root, file),
                                   output_folder))

            # Nettoyer les fichiers temporaires
            os.remove(filepath)
            for file in os.listdir(output_folder):
                os.remove(os.path.join(output_folder, file))
            os.rmdir(output_folder)

            return send_file(zip_path, as_attachment=True)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
