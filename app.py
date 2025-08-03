import os
import subprocess
from flask import Flask, request, redirect, render_template, flash, url_for
from werkzeug.utils import secure_filename

# --- Konfiguracja ---
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
PRINTER_NAME = 'HP_LaserJet_1320_series' 
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'twoj_super_tajny_klucz_moze_byc_dowolny'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_and_print():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Błąd: Nie wybrano żadnego pliku.', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('Błąd: Nie wybrano żadnego pliku.', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                file_to_print = filepath
                file_extension = filename.rsplit('.', 1)[1].lower()
                
                if file_extension in ['doc', 'docx']:
                    print(f"Konwertowanie pliku {filename} do PDF...")
                    subprocess.run(
                        ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', app.config['UPLOAD_FOLDER'], filepath],
                        check=True, timeout=60
                    )
                    pdf_filename = filename.rsplit('.', 1)[0] + '.pdf'
                    file_to_print = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
                    print(f"Konwersja ukończona. Plik do druku: {file_to_print}")

                # --- BUDOWANIE KOMENDY DRUKOWANIA ---
                # Zaczynamy od podstawowej komendy
                print_command = ['lp', '-d', PRINTER_NAME]

                # 1. Odczytaj liczbę kopii z formularza
                copies = request.form.get('copies', '1')
                if copies.isdigit() and int(copies) > 0:
                    print_command.extend(['-n', copies])

                # 2. Odczytaj opcję druku dwustronnego
                # Checkbox, jeśli jest zaznaczony, będzie miał wartość 'on'
                if request.form.get('duplex'):
                    # Domyślny duplex dla dokumentów pionowych
                    print_command.extend(['-o', 'sides=two-sided-long-edge'])
                else:
                    print_command.extend(['-o', 'sides=one-sided'])
                
                # 3. Odczytaj orientację strony
                orientation = request.form.get('orientation', 'portrait')
                if orientation == 'landscape':
                    print_command.extend(['-o', 'orientation-requested=4'])
                else: # portrait
                    print_command.extend(['-o', 'orientation-requested=3'])

                # Dodajemy ścieżkę do pliku na samym końcu
                print_command.append(file_to_print)

                print(f"Finalna komenda drukowania: {' '.join(print_command)}")
                
                # Uruchamiamy zbudowaną komendę
                subprocess.run(print_command, check=True)
                
                flash(f'Sukces! Plik "{filename}" został wysłany do drukarki z wybranymi opcjami.', 'success')

            except subprocess.CalledProcessError as e:
                flash(f'Błąd podczas przetwarzania lub drukowania pliku: {e}', 'error')
            except subprocess.TimeoutExpired:
                flash('Błąd: Konwersja pliku trwała zbyt długo i została przerwana.', 'error')

            return redirect(request.url)

    return render_template('index.html')

# Ta sekcja jest teraz tylko do testów ręcznych.
# W produkcji używamy Gunicorna, który jej nie wykonuje.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)