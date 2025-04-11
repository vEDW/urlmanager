import os
from flask import Flask, render_template, request, redirect, url_for, flash
import validators  
import psycopg2

app = Flask(__name__)
app.secret_key = "super secret key"

MY_NODE_NAME = os.getenv('MY_NODE_NAME')
IMAGE_TAG= os.getenv('IMAGE_TAG')
hostname = os.uname()[1]

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.environ['DB_HOST'],  # Assuming the service name for PostgreSQL is 'postgres'
            database=os.environ['DB_NAME'],
            user=os.environ['DB_USERNAME'],
            password=os.environ['DB_PASSWORD']
        )
        return conn

    except psycopg2.Error as e:
        print(f"Unable to connect to the database: {e}")
        return None

def check_and_create_database():
    # Connect to PostgreSQL server without specifying a database
    print("connecting to DB")

    try:
        conn = psycopg2.connect(
            host=os.environ['DB_HOST'],  # Assuming the service name for PostgreSQL is 'postgres'
            user=os.environ['DB_USERNAME'],
            password=os.environ['DB_PASSWORD']
        )
        conn.autocommit = True  # Enable autocommit mode
        cur = conn.cursor()
    except psycopg2.Error as e:
        print(f"Unable to connect to the database: {e}")
        return

    # Check if the database exists
    db_name = os.environ['DB_NAME']

    try:
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
    except psycopg2.Error as e:
            print(f"Unable to connect to query the database tables: {e}")
            return 

    if not cur.fetchone():
        # Create the database if it does not exist
        cur.execute(f"CREATE DATABASE {db_name}")
        print("creating DB instance")

    cur.close()
    conn.close()

    conn = get_db_connection()
    cur = conn.cursor()

    #Check if table exists
    cur.execute(f'''
    SELECT EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_name = 'urls'
    );
    ''')
    
    if not cur.fetchone()[0]:
        # Create the table if it doesn't exist
        cur.execute('''
            CREATE TABLE IF NOT EXISTS urls (
                id SERIAL PRIMARY KEY,
                url VARCHAR(255) NOT NULL,
                description TEXT NOT NULL
            );
        ''')
        # Insert initial data
        initial_data = [
            ('https://www.nutanix.com/uk/products/database-service', 'Nutanix NDB'),
            ('https://www.nutanix.com/uk/products/kubernetes-management-platform/', 'Nutanix NKP'),
            ('https://www.nutanix.com/uk/support-services/training-certification', 'Nutanix University')
        ]
        print("Injecting data")
        cur.executemany('INSERT INTO urls (url, description) VALUES (%s, %s)', initial_data)
        conn.commit()

    cur.close()
    conn.close()

    return "Database initialized with sample data!"

def drop_database():
    # Connect to PostgreSQL server without specifying a database
    conn = psycopg2.connect(
        host=os.environ['DB_HOST'],  # Assuming the service name for PostgreSQL is 'postgres'
        user=os.environ['DB_USERNAME'],
        password=os.environ['DB_PASSWORD']
    )
    conn.autocommit = True  # Enable autocommit mode
    cur = conn.cursor()
    db_name = os.environ['DB_NAME']
    cur.execute(f"DROP DATABASE {db_name}")
    cur.close()
    conn.close()
    return "Database dropped!"

print("apptest started")
print("checking DB connection and existence")

print(check_and_create_database())  # Check and create database if necessary
    
@app.route('/')
def index():
    conn = get_db_connection()
    if conn is None:
        return render_template('index.html', db_error="Unable to connect to the database")
    
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM urls;')
        urls = cur.fetchall()
        cur.close()
        conn.close()
        returntext = "REMOTE_ADDR=" + str(request.environ.get('REMOTE_ADDR'))
        returntext = returntext + " HTTP_X_FORWARDED_FOR=" + str(request.environ.get('HTTP_X_FORWARDED_FOR'))
        returntext = returntext + " X-Real-IP=" + str(request.environ.get('X-Real-IP'))
        print(returntext)
        return render_template('index.html', urls=urls, hostname=str(hostname), node_name=str(MY_NODE_NAME), topology_region=str(TOPOLOGY_REGION), topology_zone=str(TOPOLOGY_ZONE), image_tag=str(IMAGE_TAG))
    except psycopg2.Error as e:
        return render_template('index.html', db_error=f"Database error: {str(e)}",hostname=str(hostname), node_name=str(MY_NODE_NAME), topology_region=str(TOPOLOGY_REGION), topology_zone=str(TOPOLOGY_ZONE), image_tag=str(IMAGE_TAG))
    
@app.route('/dblist')
def dblist():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM pg_catalog.pg_database")
    dblist = cur.fetchall()
    cur.close()
    conn.close()
    return dblist

@app.route('/add', methods=['POST'])
def add_url():
    url = request.form['url']
    description = request.form['description']

    # Validate the URL
    if not validators.url(url):
        flash("Error: You must provide a valid URL!")
        return redirect(url_for('index'))
    
    print("adding url : " + str(url) + " - description : " + str(description) )

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO urls (url, description) VALUES (%s, %s)', (url, description))
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/curlme')
def curlme():
    db_status="DB OK"
    conn = get_db_connection()
    if conn is None:
        db_status="DB DOWN"
    else:
        conn.close()
    returntext = str(IMAGE_TAG) + " - " + hostname + " - " + str(MY_NODE_NAME) + " - " + str(db_status)
    print(request.remote_addr)
    return returntext

@app.route('/dropdb')
def drop_db():
    drop_database()
    return "Database destroyed!"

@app.route('/delete/<int:id>')
def delete_url(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM urls WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/healthz')
def healthz():
    return '', 200

if __name__ == '__main__':
    app.run(debug=True)
