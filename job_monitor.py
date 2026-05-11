import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import os

JOB_DATA_FILE = 'job_data.json'

def get_zhaopin_jobs():
    jobs = []
    try:
        url = 'https://www.zhaopin.com/jobsearch/result.html?kw=%E5%AE%89%E4%BF%9D%E4%B8%BB%E7%AE%A1%20%E5%AE%89%E4%BF%9D%E7%BB%8F%E7%90%86&city=539&salary=10001-15000,15001-20000,20000+'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        job_list = soup.find_all('div', class_='joblist-box__item')
        for item in job_list[:10]:
            try:
                title = item.find('a', class_='joblist-box__name').get_text(strip=True) if item.find('a', class_='joblist-box__name') else ''
                company = item.find('a', class_='joblist-box__company-name').get_text(strip=True) if item.find('a', class_='joblist-box__company-name') else ''
                salary = item.find('span', class_='joblist-box__salary').get_text(strip=True) if item.find('span', class_='joblist-box__salary') else ''
                location = item.find('span', class_='joblist-box__location').get_text(strip=True) if item.find('span', class_='joblist-box__location') else ''
                experience = item.find('span', class_='joblist-box__attribute').get_text(strip=True) if item.find('span', class_='joblist-box__attribute') else ''
                
                if title and salary:
                    job = {
                        'title': title,
                        'company': company,
                        'salary': salary,
                        'location': location,
                        'experience': experience,
                        'source': '智联招聘',
                        'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'is_finance': any(keyword in title or keyword in company for keyword in ['银行', '金融', '保险', '证券', '基金'])
                    }
                    jobs.append(job)
            except Exception as e:
                continue
    except Exception as e:
        print(f"智联招聘抓取失败: {e}")
    
    return jobs

def get_liepin_jobs():
    jobs = []
    try:
        url = 'https://www.liepin.com/zhaopin/?key=%E5%AE%89%E4%BF%9D%E4%B8%BB%E7%AE%A1%20%E5%AE%89%E4%BF%9D%E7%BB%8F%E7%90%86&city=539&salary=10k-20k,20k+'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        job_list = soup.find_all('div', class_='job-card-wrapper')
        for item in job_list[:10]:
            try:
                title = item.find('h3', class_='job-card-title').get_text(strip=True) if item.find('h3', class_='job-card-title') else ''
                company = item.find('a', class_='company-name').get_text(strip=True) if item.find('a', class_='company-name') else ''
                salary = item.find('span', class_='job-card-salary').get_text(strip=True) if item.find('span', class_='job-card-salary') else ''
                location = item.find('span', class_='job-area').get_text(strip=True) if item.find('span', class_='job-area') else ''
                experience = item.find('span', class_='requirement').get_text(strip=True) if item.find('span', class_='requirement') else ''
                
                if title and salary:
                    job = {
                        'title': title,
                        'company': company,
                        'salary': salary,
                        'location': location,
                        'experience': experience,
                        'source': '猎聘',
                        'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'is_finance': any(keyword in title or keyword in company for keyword in ['银行', '金融', '保险', '证券', '基金'])
                    }
                    jobs.append(job)
            except Exception as e:
                continue
    except Exception as e:
        print(f"猎聘抓取失败: {e}")
    
    return jobs

def get_jobui_salary_data():
    data = {}
    try:
        url = 'https://www.jobui.com/salary/zhuhai-anbaojingli/'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        salary_info = soup.find('div', class_='salary-info')
        if salary_info:
            data['source'] = '职友集'
            data['update_time'] = datetime.now().strftime('%Y-%m-%d')
    except Exception as e:
        print(f"职友集抓取失败: {e}")
    
    return data

def crawl_jobs():
    all_jobs = []
    all_jobs.extend(get_zhaopin_jobs())
    all_jobs.extend(get_liepin_jobs())
    
    filtered_jobs = []
    for job in all_jobs:
        salary_low = extract_salary(job['salary'])
        if salary_low >= 10000:
            filtered_jobs.append(job)
    
    filtered_jobs.sort(key=lambda x: extract_salary(x['salary']), reverse=True)
    
    return filtered_jobs[:20]

def extract_salary(salary_str):
    try:
        salary_str = salary_str.replace(',', '').replace('K', '000').replace('k', '000').replace('W', '0000').replace('w', '0000')
        if '-' in salary_str:
            parts = salary_str.split('-')
            return int(parts[0].strip())
        return int(salary_str.strip())
    except:
        return 0

def save_jobs(jobs):
    data = {
        'jobs': jobs,
        'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_count': len(jobs)
    }
    with open(JOB_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_jobs():
    if os.path.exists(JOB_DATA_FILE):
        with open(JOB_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'jobs': [], 'crawl_time': '', 'total_count': 0}

def refresh_jobs():
    jobs = crawl_jobs()
    save_jobs(jobs)
    return jobs

if __name__ == '__main__':
    print("正在抓取珠海安保岗位信息...")
    jobs = crawl_jobs()
    save_jobs(jobs)
    print(f"共抓取到 {len(jobs)} 个符合条件的岗位")
    for job in jobs:
        print(f"{job['title']} | {job['company']} | {job['salary']} | {job['location']}")