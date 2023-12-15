from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session,json, jsonify
import os
import requests
import sqlite3
import pytz  
import random 
from werkzeug.security import generate_password_hash, check_password_hash  
from datetime import datetime, timedelta
from datetime import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__, template_folder=os.path.dirname(__file__))
app.secret_key = 'your_secret_key_here'
port = 3000

def connect_db():
    conn = sqlite3.connect('user.db')
    cursor = conn.cursor()
    return conn, cursor
def get_db_connection():
    conn = sqlite3.connect('user.db')
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    hashed_password = generate_password_hash(password)
    return hashed_password

def check_password(user_password, entered_password):
    return check_password_hash(user_password, entered_password)

@app.route('/<filename>')
def static_files(filename):
    return send_from_directory(os.path.dirname(__file__), filename)

DATA_FILE = "jk.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            data = json.load(file)
    else:
        data = {}
    return data

def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=2)


def create_users_table():
    with connect_db()[0] as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                email TEXT,
                password TEXT
            )
        ''')
        conn.commit()

def create_transaction_table():
    with connect_db()[0] as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS booktransaction (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                email TEXT NOT NULL,
                bookID INTEGER NOT NULL,
                book_title TEXT NOT NULL,
                author TEXT NOT NULL,
                issue_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                return_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                penalty INTEGER DEFAULT 0                                  
            )
        ''')
        conn.commit()
def create_book_table():
    with connect_db()[0] as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Book (
                id INTEGER PRIMARY KEY,
                bookID INTEGER,
                title TEXT,
                authors TEXT,
                average_rating REAL,
                isbn TEXT,
                isbn13 TEXT,
                language_code TEXT,
                publication_date TEXT,
                publisher TEXT,
                ratings_count INTEGER,
                text_reviews_count INTEGER,
                available_count INTEGER,
                remove_count INTEGER
            )
        ''')
        conn.commit()

create_users_table()
create_transaction_table()
create_book_table()

@app.route('/')
def front_page():
    return render_template('front.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user_id = request.form['user_id']
        email = request.form['email']
        password = request.form['password']
        if is_user_id_exists(user_id):
            return 'User ID already exists. Please choose a different one.'

        with connect_db()[0] as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (user_id, email, password) VALUES (?, ?, ?)', (user_id, email, password))
            conn.commit()

        return redirect(url_for('front'))

    return render_template('signup.html')

def is_user_id_exists(user_id):
    with connect_db()[0] as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone() is not None
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        entered_user_id = request.form.get('user_id')
        entered_password = request.form.get('password')
        if entered_user_id is not None and entered_password is not None:
            with connect_db()[0] as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT user_id, password FROM users WHERE user_id = ?', (entered_user_id,))
                user = cursor.fetchone()
            if user:
                stored_password = user[1]
                print(f"Stored Password: {stored_password}")
                print(f"Entered Password: {entered_password}")
                if stored_password == entered_password:
                    session['user_id'] = user[0]
                    print("Login successful. Redirecting to 'front' route.")
                    return redirect(url_for('front'))

    return render_template('ashu.html')

@app.route('/booksearch', methods=['GET', 'POST'])
def book_search():
    if request.method == 'POST':
        keyword = request.form['keyword']
        data = fetch_data(keyword)
        return render_template('index.html', book_data=data)  # Change 'data' to 'book_data'

    return render_template('simple.html')

def fetch_data(keyword):
    data_list = []

    if keyword.isdigit():
        num_books = int(keyword)
        print(num_books)
        for _ in range(num_books):
            page = random.randint(1, 35)
            url = f"https://frappe.io/api/method/frappe-library?page={page}"
            response = requests.get(url, verify=False)
            try:
                data = response.json()
                data_list.extend(data.get('message', []))
            except requests.exceptions.JSONDecodeError:
                pass
        data_list = data_list[:num_books]
    else:
        for page in range(1, 36):
            url = f"https://frappe.io/api/method/frappe-library?page={page}&title={keyword}&author={keyword}"
            response = requests.get(url, verify=False)
            try:
                data = response.json()
                data_list.extend(data.get('message', []))
            except requests.exceptions.JSONDecodeError:
                pass
    
    return data_list


@app.route('/front',methods=['GET', 'POST'])  
def front():
    user_id = session.get('user_id')
    return render_template('front.html', user_id=user_id)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/datatable')
def index():
    with connect_db()[0] as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, user_id, email FROM users')
        data = cursor.fetchall()

    return render_template('datatable.html', data=data)
@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/booktr')
def booktr():
    return render_template('booktr.html')
@app.route("/trbooks")
def trbooks():
    return render_template("trbooks.html")
@app.route('/index')
def display_book_data():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bookdata')  
        book_data = cursor.fetchall()
    return render_template('index.html', book_data=book_data)
@app.route('/book')
def book():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Book') 
        book_data = cursor.fetchall()
    return render_template('book.html', book_data=book_data)
  
@app.route('/transaction')
def transaction():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM booktransaction')
        book_transactions = cursor.fetchall()
    return render_template('transaction.html', book_transactions=book_transactions)


@app.route('/Issue', methods=['POST'])
def issue_book():
    if request.method == 'POST':
        if 'user_id' not in session:
            return 'User not logged in'

        user_id = session['user_id']
        email = request.form.get('email')
        book_title = request.form.get('book_title')
        author = request.form.get('author')
        issue_date = datetime.utcnow()

        with connect_db()[0] as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO Tansaction ( user_id, email, book_title, author, issue_date, return_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, email, book_title, author, issue_date, None))

        return 'Book Issued Successfully'

@app.route('/Return', methods=['POST'])
def return_book():
    if request.method == 'POST':
        if 'user_id' not in session:
            return 'User not logged in'

        user_id = session['user_id']
        email = request.form.get('email')
        book_title = request.form.get('book_title')
        author = request.form.get('author')
        return_date = datetime.utcnow()

        with connect_db()[0] as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE Transaction 
                SET return_date = ?
                WHERE user_id = ? AND email = ? AND book_title = ? AND author = ?  AND return_date IS NULL
            ''', (return_date, user_id, email, book_title, author))

        return 'Book Returned Successfully'
@app.route('/delete', methods=['POST'])
def delete_user():
    user_id = request.form.get('user_id')
    conn = sqlite3.connect("user.db")
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    return redirect('/')
@app.route('/update/<string:user_id>', methods=['GET'])
def update_user_form(user_id):
    connection = sqlite3.connect('user.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    connection.close()

    if user:
        return render_template('update.html', user_id=user[1], user_email=user[2], user_password=user[3])
    else:
        return "User not found", 404

@app.route('/update', methods=['POST'])
def update_user():
    user_id = request.form.get('user_id')
    new_email = request.form.get('email')
    new_password = request.form.get('password')

    connection = sqlite3.connect('user.db')
    cursor = connection.cursor()
    cursor.execute('UPDATE users SET email=?, password=? WHERE user_id=?', (new_email, new_password, user_id))
    connection.commit()
    connection.close()

    return redirect('/')
@app.route('/user/<user_email>')
def display_user_by_email(user_email):
    with connect_db()[0] as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (user_email,))
        user = cursor.fetchone()

    if user:
        with connect_db()[0] as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM booktransaction WHERE email = ?', (user_email,))
            books = cursor.fetchall()

        return render_template('user_profile.html', user=user, books=books)
    else:
        return "User not found", 404
    

@app.route('/updatebook/<int:book_id>', methods=['GET', 'POST'])
def edit_book_form(book_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Book WHERE bookID = ?', (book_id,))
    book = cursor.fetchone()
    connection.close()

    if request.method == 'POST':
        title = request.form['title']
        authors = request.form['authors']
        average_rating = request.form['average_rating']
        isbn = request.form['isbn']
        isbn13 = request.form['isbn13']
        language_code = request.form['language_code']
        publication_date = request.form['publication_date']
        publisher = request.form['publisher']
        ratings_count = request.form['ratings_count']
        text_reviews_count = request.form['text_reviews_count']
        available_count = request.form['available_count']

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute('UPDATE Book SET title=?, authors=?, average_rating=?, isbn=?, isbn13=?, '
                       'language_code=?, publication_date=?, publisher=?, ratings_count=?, '
                       'text_reviews_count=?, available_count=? WHERE bookID=?',
                       (title, authors, average_rating, isbn, isbn13, language_code,
                        publication_date, publisher, ratings_count, text_reviews_count,
                        available_count, book_id))

        connection.commit()
        connection.close()

        return redirect('/book')  

    if book:
        return render_template('updatebook.html', row=book)  
        return "Book not found", 404


@app.route("/add", methods=["POST"])
def add():
    data = load_data()  
    new_book = {
        "bookID": request.form["bookID"],
        "title": request.form["title"],
        "authors": request.form["authors"],
        "average_rating": float(request.form["average_rating"]),
        "isbn": request.form["isbn"],
        "isbn13": request.form["isbn13"],
        "language_code": request.form["language_code"],
        "publication_date": request.form["publication_date"],
        "publisher": request.form["publisher"],
        "ratings_count": int(request.form["ratings_count"]),
        "text_reviews_count": int(request.form["text_reviews_count"]),
        "available_count": 0,  
        "remove_count": 0,
    }
    
    with connect_db()[0] as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Book (
                bookID, title, authors, average_rating, isbn, isbn13, language_code,
                publication_date, publisher, ratings_count, text_reviews_count,
                available_count, remove_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            new_book["bookID"], new_book["title"], new_book["authors"],
            new_book["average_rating"], new_book["isbn"], new_book["isbn13"],
            new_book["language_code"], new_book["publication_date"],
            new_book["publisher"], new_book["ratings_count"],
            new_book["text_reviews_count"], new_book["available_count"],
            new_book["remove_count"]
        ))
        
        conn.commit()
    
    return redirect(url_for("trbooks"))
@app.route("/remove", methods=["POST"])
def remove():
    book_id_to_remove = request.form["bookIDToRemove"]    
    with connect_db()[0] as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Book WHERE bookID = ?', (book_id_to_remove,))
        existing_book = cursor.fetchone()
        
        if existing_book:
            cursor.execute('DELETE FROM Book WHERE bookID = ?', (book_id_to_remove,))
            conn.commit()
    
    return redirect(url_for("trbooks"))
@app.route('/search', methods=['GET'])
def search_books():
    conn = get_db_connection()
    query = request.args.get('query', '')
    cursor = conn.execute(
        'SELECT * FROM bookdata WHERE id LIKE ? OR title LIKE ? OR isbn LIKE ? OR authors LIKE ?',
        ('%' + query + '%', '%' + query + '%', '%' + query + '%', '%' + query + '%')
    )
    search_results = cursor.fetchall()
    conn.close()
    return render_template('index.html', book_data=search_results)

@app.route('/add_book', methods=['POST'])
def add_book():
    book_data = request.form.to_dict()

    with connect_db()[0] as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Book (bookID, title, authors, average_rating, isbn, isbn13, language_code,
                              publication_date, publisher, ratings_count, text_reviews_count,
                              available_count, remove_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (book_data.get('bookID', 'Unknown BookID'),
              book_data.get('title', 'Unknown Title'),
              book_data.get('authors', 'Unknown Authors'),
              float(book_data.get('average_rating', 0.0)),
              book_data.get('isbn', 'Unknown ISBN'),
              book_data.get('isbn13', 'Unknown ISBN13'),
              book_data.get('language_code', 'en'),
              book_data.get('publication_date', '2023-01-01'),
              book_data.get('publisher', 'Unknown Publisher'),
              int(book_data.get('ratings_count', 0)),
              int(book_data.get('text_reviews_count', 0)),
              0, 0))  # Assuming available_count and remove_count start at 0
        conn.commit()

    return jsonify({'message': 'Book added successfully'})



def issue_book_to_user(user_id, bookID, book_title, authors):
    try:
        with connect_db()[0] as conn:
            cursor = conn.cursor()

            # Retrieve user_id and email using the entered username
            cursor.execute('SELECT user_id, email FROM users WHERE user_id = ?', (user_id,))
            user_data = cursor.fetchone()

            if user_data:
                user_id, email = user_data
                cursor.execute('SELECT bookID, available_count FROM Book WHERE bookID = ?', (bookID,))
                book_data = cursor.fetchone()

                if book_data and book_data[1] > 0:
                    updated_count = book_data[1] - 1
                    cursor.execute('UPDATE Book SET available_count = ? WHERE bookID = ?', (updated_count, book_data[0]))

                    india_timezone = pytz.timezone('Asia/Kolkata')
                    issue_date = datetime.now(india_timezone).replace(microsecond=0)

                    cursor.execute('''
                        INSERT INTO booktransaction (user_id, email, bookID, book_title, author, issue_date, return_date, penalty)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)  
                    ''', (user_id, email, book_data[0], book_title, authors, issue_date.strftime("%Y-%m-%d %H:%M:%S"), None, 0))

                    conn.commit()
                    return True, 'Book issued successfully'
                else:
                    return False, 'Book not available'
            else:
                return False, 'User not found'

    except sqlite3.Error as e:
        print(f"Error issuing the book: {str(e)}")
    return False, f'Error issuing the book: {str(e)}'
@app.route('/issue-books', methods=['POST'])
def issue_books():
    if request.method == 'POST':
        data = request.json
        user_id= data.get('user_id') 
        bookID = data.get('bookID')
        book_title = data.get('title')
        authors = data.get('authors')

        success, message = issue_book_to_user(user_id, bookID, book_title, authors)

        if success:
            return jsonify({'message': message}), 200
        else:
            return jsonify({'error': message}), 400

def calculate_penalty(issue_date, return_date):
    if return_date > issue_date:
        overdue_days = (return_date - issue_date).days
        penalty = max(0, overdue_days - 7) * 5  
        return penalty
    return 0

@app.route('/return-books', methods=['POST'])
def return_books():
    data = request.get_json()
    user_id = data['user_id']
    book_id = data['bookID']

    try:
        conn, cursor = connect_db()
        cursor.execute('SELECT * FROM booktransaction WHERE user_id = ? AND bookID = ? AND return_date IS NULL', (user_id, book_id))
        transaction_data = cursor.fetchone()

        if transaction_data:
            india_timezone = pytz.timezone('Asia/Kolkata')
            issue_date = india_timezone.localize(datetime.fromisoformat(transaction_data[6]))
            return_date = datetime.now(india_timezone).replace(microsecond=0)
            penalty = calculate_penalty(issue_date, return_date)

            confirmation_message = f'Book return confirmation: Penalty: {penalty} Rs. Do you want to proceed? (yes/no)'

            return jsonify({
                "confirmation_message": confirmation_message,
                "transaction_id": transaction_data[0],
                "book_id": book_id,
                "user_id": user_id
            })

        else:
            return jsonify({"error": "No active transaction found for the user and book"})

    except sqlite3.Error as e:
        print(f"Error getting book return information: {str(e)}")
        return jsonify({"error": f'Error getting book return information: {str(e)}'})

    finally:
        conn.close()

@app.route('/confirm-return', methods=['POST'])
def confirm_return():
    data = request.get_json()
    transaction_id = data['transaction_id']
    user_id = data['user_id']
    book_id = data['book_id']
    confirmation = data['confirmation']

    try:
        conn, cursor = connect_db()
        cursor.execute('SELECT * FROM booktransaction WHERE id = ? AND user_id = ? AND bookID = ? AND return_date IS NULL',
                       (transaction_id, user_id, book_id))
        transaction_data = cursor.fetchone()

        if transaction_data:
            if confirmation.lower() == 'yes':
                india_timezone = pytz.timezone('Asia/Kolkata')
                return_date = datetime.now(india_timezone).replace(microsecond=0)
                penalty = calculate_penalty(india_timezone.localize(datetime.fromisoformat(transaction_data[6])), return_date)

                cursor.execute('UPDATE booktransaction SET return_date = ?, penalty = ? WHERE id = ?',
                               (return_date.strftime("%Y-%m-%d %H:%M:%S"), penalty, transaction_id))
                cursor.execute('SELECT available_count FROM Book WHERE bookID = ?', (book_id,))
                available_count = cursor.fetchone()[0]
                updated_count = available_count + 1
                cursor.execute('UPDATE Book SET available_count = ? WHERE bookID = ?', (updated_count, book_id))
                conn.commit()

                return jsonify({"success": True, "message": f"Book returned successfully. Penalty: {penalty} Rs"})

            else:
                return jsonify({"success": False, "message": "Return canceled by the user"})

        else:
            return jsonify({"error": "No active transaction found for the user and book"})

    except sqlite3.Error as e:
        print(f"Error confirming the book return: {str(e)}")
        return jsonify({"error": f'Error confirming the book return: {str(e)}'})

    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=port)
