import time
import random
import traceback
from datetime import datetime
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from bs4 import BeautifulSoup


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

with app.app_context():
    db.create_all()

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
    if not summary_tag: summary_tag = card.find('div', {'data-testid': 'job-snippet'})
    summary = summary_tag.text.strip().replace("\n"," ") if summary_tag else 'NOT MENTIONED'
    
    job_url = "https://in.indeed.com" + card.get('href') if card.get('href') else 'NOT MENTIONED'
    
    salary_tag = card.find('div', {'data-testid': 'attribute_snippet_testid-salary'})
    if not salary_tag: salary_tag = card.find('div', {'class': 'salary-snippet'})
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
            try: jobs.append(get_record(card))
            except: continue
        next_btn = soup.find('a', {'data-testid': 'pagination-page-next'})
        if next_btn and next_btn.get('href'):
            driver.get('https://in.indeed.com' + next_btn['href'])
            page_num += 1
            time.sleep(random.uniform(3, 6))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        else: break
    driver.quit()
    return jobs, page_num

@app.route('/api/scrape-jobs', methods=['POST'])
def api_scrape():
    try:
        data = request.get_json(force=True)
        position = data.get('position', '').strip()
        location = data.get('location', '').strip()
        if not position or not location:
            return jsonify({'success': False, 'error': 'Both \"position\" and \"location\" are required.'}), 400
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
        return jsonify({'success': True, 'jobs': jobs, 'new_jobs_saved': len(saved_jobs)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()}), 500

@app.route('/api/jobs', methods=['GET'])
def api_jobs():
    try:
        position = request.args.get('position', '').strip()
        location = request.args.get('location', '').strip()
        
        query = Job.query
        if position: query = query.filter(Job.job_title.ilike(f'%{position}%'))
        if location: query = query.filter(Job.location.ilike(f'%{location}%'))
        results = [job.to_dict() for job in query.all()]
        return jsonify({'success': True, 'jobs': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()}), 500

if __name__ == '__main__':
    
    app.run(debug=True, host='0.0.0.0', port=5000)
