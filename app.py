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

    # Fetch the HTML content from the URL
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Look for span elements with a text that contains 'Jobs'
    job_count_elements = soup.find_all('span', text=lambda text: text and 'Jobs' in text)
    print(job_count_elements)
    # Iterate through job count elements and try to find the pattern 'number in 100s Jobs'
    for job_count_element in job_count_elements:
        job_count_text = job_count_element.get_text(strip=True)
        
        # Extract the number of jobs using regular expressions
        match = re.search(r'\d+', job_count_text)
        if match:
            job_count = int(match.group())
            return job_count

    # If the element is not found, return 0
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
