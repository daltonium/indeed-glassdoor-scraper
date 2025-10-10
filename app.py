import time
import random
import traceback
from datetime import datetime
from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from bs4 import BeautifulSoup
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'

db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_title = db.Column(db.String(256))
    company = db.Column(db.String(256))
    location = db.Column(db.String(128))
    post_date = db.Column(db.String(64))
    extract_date = db.Column(db.String(64))
    summary = db.Column(db.Text)
    salary = db.Column(db.String(128))
    job_url = db.Column(db.String(512))

    def to_dict(self):
        return {
            "id": self.id,
            "JobTitle": self.job_title,
            "Company": self.company,
            "Location": self.location,
            "PostDate": self.post_date,
            "ExtractDate": self.extract_date,
            "Summary": self.summary,
            "Salary": self.salary,
            "JobUrl": self.job_url
        }

with app.app_context():
    db.create_all()
    # Create default user if not exists
    if not User.query.filter_by(username='admin').first():
        default_user = User(username='admin', password='admin123')
        db.session.add(default_user)
        db.session.commit()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_url(position, location):
    return f'https://in.indeed.com/jobs?q={position.replace(" ", "+")}&l={location.replace(" ", "+")}'

def get_record(card):
    title_tag = card.find('h2', {'class': 'jobTitle'})
    job_title = title_tag.text.strip() if title_tag else 'NOT MENTIONED'

    company_tag = card.find('span', {'data-testid': 'company-name'})
    company = company_tag.text.strip() if company_tag else 'NOT MENTIONED'

    location_tag = card.find('div', {'data-testid': 'text-location'})
    job_location = location_tag.text.strip() if location_tag else 'NOT MENTIONED'

    post_date_tag = card.find('span', {'data-testid': 'myJobsStateDate'})
    post_date = post_date_tag.text.strip() if post_date_tag else 'NOT MENTIONED'

    today = datetime.today().strftime('%Y-%m-%d')

    summary_tag = card.find('div', {'class': 'job-snippet'})
    if not summary_tag: 
        summary_tag = card.find('div', {'data-testid': 'job-snippet'})
    summary = summary_tag.text.strip().replace("\n"," ") if summary_tag else 'NOT MENTIONED'

    job_url = "https://in.indeed.com" + card.get('href') if card.get('href') else 'NOT MENTIONED'

    salary_tag = card.find('div', {'data-testid': 'attribute_snippet_testid-salary'})
    if not salary_tag: 
        salary_tag = card.find('div', {'class': 'salary-snippet'})
    salary = salary_tag.text.strip() if salary_tag else 'NOT MENTIONED'

    return {
        "JobTitle": job_title,
        "Company": company,
        "Location": job_location,
        "PostDate": post_date,
        "ExtractDate": today,
        "Summary": summary,
        "Salary": salary,
        "JobUrl": job_url
    }

def scrape_jobs(position, location):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=options)

    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)

    url = get_url(position, location)
    driver.get(url)

    time.sleep(5)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
    time.sleep(2)

    jobs, page_num = [], 1
    while True:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        cards = soup.select("a.tapItem, div.job_seen_beacon")

        for card in cards:
            try: 
                jobs.append(get_record(card))
            except: 
                continue

        next_btn = soup.find('a', {'data-testid': 'pagination-page-next'})

        if next_btn and next_btn.get('href'):
            driver.get('https://in.indeed.com' + next_btn['href'])
            page_num += 1
            time.sleep(random.uniform(3, 6))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        else: 
            break

    driver.quit()
    return jobs, page_num

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session['logged_in'] = True
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

# Web Routes (Protected)
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/jobs')
@login_required
def jobs_page():
    position = request.args.get('position', '')
    location = request.args.get('location', '')
    query = Job.query
    if position: 
        query = query.filter(Job.job_title.ilike(f'%{position}%'))
    if location: 
        query = query.filter(Job.location.ilike(f'%{location}%'))
    jobs = query.all()
    return render_template('jobs.html', jobs=jobs, position=position, location=location)

@app.route('/scrape', methods=['GET', 'POST'])
@login_required
def scrape_route():
    if request.method == 'GET':
        return render_template('index.html')
    else:
        try:
            if request.is_json:
                data = request.get_json()
                position = data.get('position', '').strip()
                location = data.get('location', '').strip()
            else:
                position = request.form.get('position', '').strip()
                location = request.form.get('location', '').strip()

            if not position or not location:
                return jsonify({'success': False, 'error': 'Both "position" and "location" are required.'}), 400

            jobs, pages_scraped = scrape_jobs(position, location)
            saved_jobs = []
            for job in jobs:
                if not Job.query.filter_by(job_title=job['JobTitle'], company=job['Company'], job_url=job['JobUrl']).first():
                    job_entry = Job(
                        job_title=job['JobTitle'],
                        company=job['Company'],
                        location=job['Location'],
                        post_date=job['PostDate'],
                        extract_date=job['ExtractDate'],
                        summary=job['Summary'],
                        salary=job['Salary'],
                        job_url=job['JobUrl']
                    )
                    db.session.add(job_entry)
                    saved_jobs.append(job)
            db.session.commit()
            flash(f'Successfully scraped {len(jobs)} jobs! {len(saved_jobs)} new jobs added.', 'success')
            return redirect(url_for('jobs_page', position=position, location=location))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
