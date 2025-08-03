import os
import subprocess
from flask import Flask, request, redirect, render_template, flash, url_for
from werkzeug.utils import secure_filename

# --- Konfiguracja ---
UPLOAD_FOLDER = 'uploads'
# Dozwolone rozszerzenia plików (można dodać więcej, np. 'xls', 'xlsx')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
# WAŻNE: Wpisz tu DOKŁADNĄ nazwę swojej drukarki z interfejsu CUPS!
# Możesz ją sprawdzić w terminalu komendą: lpstat -p
PRINTER_NAME = 'HP_LaserJet_1320_series' 

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Klucz jest potrzebny do wyświetlania wiadomości (flash)
app.secret_key = 'twoj_super_tajny_klucz_moze_byc_dowolny'

# Funkcja sprawdzająca, czy rozszerzenie pliku jest dozwolone
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Główna strona aplikacji
@app.route('/', methods=['GET', 'POST'])
def upload_and_print():
    # Jeśli użytkownik wysłał formularz (plik)
    if request.method == 'POST':
        # Sprawdzenie, czy plik został dołączony
        if 'file' not in request.files:
            flash('Błąd: Nie wybrano żadnego pliku.')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('Błąd: Nie wybrano żadnego pliku.')
            return redirect(request.url)

        # Jeśli plik istnieje i ma dozwolone rozszerzenie
        if file and allowed_file(file.filename):
            # Zabezpieczenie nazwy pliku (usuwa znaki specjalne, np. ../)
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # --- INTELIGENTNA KONWERSJA I DRUKOWANIE ---
            try:
                # Domyślnie drukujemy oryginalny plik
                file_to_print = filepath
                file_extension = filename.rsplit('.', 1)[1].lower()
                
                # Jeśli to plik Worda, konwertujemy go do PDF za pomocą LibreOffice
                if file_extension in ['doc', 'docx']:
                    print(f"Wykryto plik Worda. Konwertowanie {filename} do PDF...")
                    # Uruchamiamy komendę systemową. Timeout zapobiega zawieszeniu się serwera.
                    subprocess.run(
                        ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', app.config['UPLOAD_FOLDER'], filepath],
                        check=True, timeout=60
                    )
                    # Po konwersji, plikiem do druku staje się nowo utworzony PDF
                    pdf_filename = filename.rsplit('.', 1)[0] + '.pdf'
                    file_to_print = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
                    print(f"Konwersja ukończona. Plik do druku: {file_to_print}")

                # Wysyłamy plik do druku (oryginalny lub skonwertowany PDF)
                print(f"Wysyłanie pliku {file_to_print} do drukarki '{PRINTER_NAME}'...")
                subprocess.run(['lp', '-d', PRINTER_NAME, file_to_print], check=True)
                
                flash(f'Sukces! Plik "{filename}" został wysłany do drukarki.')

            except subprocess.CalledProcessError as e:
                flash(f'Błąd podczas przetwarzania lub drukowania pliku: {e}')
            except subprocess.TimeoutExpired:
                flash('Błąd: Konwersja pliku trwała zbyt długo i została przerwana.')

            return redirect(request.url)

    # Jeśli użytkownik tylko wszedł na stronę (metoda GET)
    return render_template('index.html')

# Uruchomienie aplikacji
if __name__ == '__main__':
    # host='0.0.0.0' sprawia, że serwer jest widoczny w sieci
    # port=80 to standardowy port HTTP (nie trzeba go wpisywać w przeglądarce)
    app.run(host='0.0.0.0', port=80, debug=True)
    