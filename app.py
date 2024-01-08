from flask import Flask, render_template
import json
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import boto3
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Initialize S3 client
s3 = boto3.client('s3')

# Use a specific path for the S3 object key
S3_OBJECT_KEY = "some_files/job_count_data.json"

def scrape_indeed_job_count():
    url = 'https://www.indeed.com/jobs?q=software+engineer&sort=date&fromage=1'

    # Fetch the HTML content of the page using requests
    response = requests.get(url)
    
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Use BeautifulSoup to parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the job count element
        job_count_element = soup.select_one('#jobsearch-JapanPage > div > div.css-hyhnne.e37uo190 > div.css-pprl14.eu4oa1w0 > div.jobsearch-JobCountAndSortPane.css-lrjfwh.eu4oa1w0 > div > div > div.jobsearch-JobCountAndSortPane-jobCount.css-13jafh6.eu4oa1w0')
        print(job_count_element)
        # Check if the element exists
        if job_count_element:
            job_count = job_count_element.text.strip()
            return int(job_count.replace(',', ''))  # Remove commas and convert to integer

    # If the element is not found or the request fails, return 0
    return 0

def save_job_count_to_s3(job_count, timestamp):
    # Get existing data from S3
    existing_data = get_data_from_s3()

    # Append new data to the existing list
    existing_data.append({'timestamp': timestamp, 'job_count': job_count})

    # Save the updated data to S3
    s3.put_object(
        Body=json.dumps(existing_data),
        Bucket="cyclic-colorful-culottes-colt-us-west-2",
        Key=S3_OBJECT_KEY
    )

def get_data_from_s3():
    try:
        # Get data from S3
        existing_data = s3.get_object(
            Bucket="cyclic-colorful-culottes-colt-us-west-2",
            Key=S3_OBJECT_KEY
        )

        return json.loads(existing_data['Body'].read())
    except s3.exceptions.NoSuchKey:
        # If the key does not exist yet, return an empty list
        return []

@app.route('/')
def index():
    job_count = scrape_indeed_job_count()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Save the job count and timestamp to S3
    save_job_count_to_s3(job_count, timestamp)

    return render_template('index.html', job_count=job_count, timestamp=timestamp)

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(scrape_indeed_job_count, 'cron', hour='1,23')
    scheduler.start()

    app.run(debug=True, use_reloader=False)
