import time
import random
from datetime import datetime
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from bs4 import BeautifulSoup
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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

def get_url(position, location):
    template = 'https://in.indeed.com/jobs?q={}&l={}'
    position = position.replace(' ', '+')
    location = location.replace(' ', '+')
    return template.format(position, location)

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
    summary = summary_tag.text.strip().replace("\n", " ") if summary_tag else 'NOT MENTIONED'

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
    records = []
    url = get_url(position, location)

    # Selenium setup
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--headless")

    driver = webdriver.Chrome(options=options)

    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
    )

    driver.get(url)
    time.sleep(5)

    # scroll to half page right after load
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
    time.sleep(2)

    page_num = 1
    while True:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        cards = soup.select("a.tapItem, div.job_seen_beacon")

        print(f"📄 Page {page_num}: Found {len(cards)} jobs")
        for card in cards:
            try:
                job = get_record(card)
                records.append(job)
            except Exception as e:
                print(f"⚠️ Error parsing card: {e}")

        next_btn = soup.find('a', {'data-testid': 'pagination-page-next'})
        if next_btn and next_btn.get('href'):
            next_url = 'https://in.indeed.com' + next_btn['href']
            driver.get(next_url)
            page_num += 1
            time.sleep(random.uniform(3, 6))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        else:
            break

    driver.quit()
    return records, page_num

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'Welcome to Job Scraper API',
        'version': '1.0',
        'status': 'active',
        'endpoints': {
            'GET /': 'API information',
            'GET /api/health': 'Health check',
            'GET /api/usage': 'Usage documentation',
            'POST /api/scrape-jobs': 'Scrape jobs from Indeed',
            'GET /api/jobs': 'Retrieve jobs from database'
        },
        'example_usage': {
            'url': '/api/scrape-jobs',
            'method': 'POST',
            'body': {
                'position': 'Python Developer',
                'location': 'Mumbai'
            }
        }
    })

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Job scraping API is running',
        'database': 'SQLite connected',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/usage', methods=['GET'])
def api_usage():
    return jsonify({
        'api_name': 'Job Scraper API',
        'description': 'RESTful API for scraping job listings from Indeed.com and storing in database',
        'endpoints': {
            '/': {
                'method': 'GET', 
                'description': 'API root info'
            },
            '/api/health': {
                'method': 'GET', 
                'description': 'API health status'
            },
            '/api/usage': {
                'method': 'GET', 
                'description': 'Get API usage information'
            },
            '/api/scrape-jobs': {
                'method': 'POST',
                'description': 'Scrape jobs and store in database',
                'parameters': {
                    'position': 'string - Job position/title (required)',
                    'location': 'string - Job location (required)'
                },
                'example': {
                    'position': 'Python Developer',
                    'location': 'Mumbai'
                }
            },
            '/api/jobs': {
                'method': 'GET',
                'description': 'Fetch stored jobs from database',
                'query_parameters': {
                    'position': 'string - Filter by job position (optional)',
                    'location': 'string - Filter by location (optional)'
                },
                'example': '/api/jobs?position=Python&location=Mumbai'
            }
        }
    })

@app.route('/api/scrape-jobs', methods=['POST'])
def api_scrape_jobs():
    try:
        data = request.get_json()

        if not data or 'position' not in data or 'location' not in data:
            return jsonify({
                'error': 'Missing required parameters',
                'message': 'Please provide both "position" and "location" in the request body'
            }), 400

        position = data['position']
        location = data['location']

        if not position.strip() or not location.strip():
            return jsonify({
                'error': 'Invalid parameters',
                'message': 'Position and location cannot be empty'
            }), 400

        # Scrape jobs
        jobs, pages_scraped = scrape_jobs(position, location)

        # Save jobs to database
        saved_jobs = []
        for job in jobs:
            # Check if job already exists (avoid duplicates)
            existing_job = Job.query.filter_by(
                job_title=job['JobTitle'],
                company=job['Company'],
                job_url=job['JobUrl']
            ).first()

            if not existing_job:
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

        return jsonify({
            'success': True,
            'data': {
                'jobs': jobs,
                'total_jobs_scraped': len(jobs),
                'new_jobs_saved': len(saved_jobs),
                'pages_scraped': pages_scraped,
                'position_searched': position,
                'location_searched': location,
                'scraped_at': datetime.now().isoformat()
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Scraping failed',
            'message': str(e)
        }), 500

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    try:
        position = request.args.get('position', '').strip()
        location = request.args.get('location', '').strip()

        query = Job.query

        if position:
            query = query.filter(Job.job_title.ilike(f'%{position}%'))
        if location:
            query = query.filter(Job.location.ilike(f'%{location}%'))

        jobs = query.all()

        return jsonify({
            'success': True,
            'total_jobs': len(jobs),
            'filters': {
                'position': position if position else None,
                'location': location if location else None
            },
            'jobs': [job.to_dict() for job in jobs]
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve jobs',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Job Scraper API with SQLAlchemy database...")
    print("📍 Server available at: http://127.0.0.1:5000")
    print("💾 Database: SQLite (jobs.db)")
    print("🔍 Visit http://127.0.0.1:5000 for API information")
    app.run(debug=True, host='0.0.0.0', port=5000)
