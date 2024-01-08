from flask import Flask, render_template
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

DATA_FILE = 'job_count_data.json'

def scrape_indeed_job_count():
    search_query = 'Software Engineer'
    url = f'https://www.indeed.com/jobs?q={search_query}&fromage=1'

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract the job count from the HTML
    job_count_element = soup.find('div', {'id': 'searchCountPages'})
    if job_count_element:
        job_count_text = job_count_element.text.strip().split()[-2]
        return int(job_count_text.replace(',', ''))
    else:
        return 0

def save_job_count_to_file(job_count, timestamp):
    data = load_data_from_file()

    # Append new data to the existing list
    data.append({'timestamp': timestamp, 'job_count': job_count})

    # Save the updated data to the file
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=2)

def load_data_from_file():
    if not os.path.exists(DATA_FILE):
        return []
    
    with open(DATA_FILE, 'r') as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            data = []

    return data

@app.route('/')
def index():
    job_count = scrape_indeed_job_count()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Save the job count and timestamp to the data file
    save_job_count_to_file(job_count, timestamp)

    return render_template('index.html', job_count=job_count, timestamp=timestamp)

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(scrape_indeed_job_count, 'cron', hour='1,23')
    scheduler.start()

    app.run(debug=True, use_reloader=False)  # use_reloader=False to prevent schedule duplication
