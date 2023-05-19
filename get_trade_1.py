# Get from https://www.vietrade.gov.vn

import requests
from bs4 import BeautifulSoup
import sqlite3
import os

# Check if the data already exists in the database cache
def is_duplicate(cursor, title):
    cursor.execute("SELECT title FROM news WHERE title = ?", (title,))
    return cursor.fetchone() is not None

# Load existing data from the database cache
def load_database_cache():
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM news")    
    cache = set(title[0] for title in cursor.fetchall())
    #cursor.fetchall() retrieves all the rows returned by the SELECT query as a list of tuples. Each tuple contains the values of the columns in the selected rows.
    #The expression title[0] for title in cursor.fetchall() is a list comprehension that extracts the first element (index 0) from each tuple in the result. In this case, it extracts the title value from each tuple.
    conn.close()
    return cache

conn = sqlite3.connect('news.db')
cursor = conn.cursor()

# Create a table to store titles if it doesn't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        note TEXT,
        content TEXT,
        tags TEXT,
        post_date TEXT,
        image TEXT
    )
""")

# Load existing data from the database cache
database_cache = load_database_cache()
#print(f'data cache: {database_cache}')

base_url = 'https://www.vietrade.gov.vn'
url = 'https://www.vietrade.gov.vn/danh-muc/co-hoi-giao-thuong'
response = requests.get(url)
#print(response)
content = response.content

# Create the 'images' folder if it doesn't exist
os.makedirs('images', exist_ok=True)

# Parse the HTML and extract titles
soup = BeautifulSoup(content, "html.parser")
articles = soup.find_all("article")
skip_keywords = ['TIN XEM NHIỀU', ['BẢN TIN XUẤT KHẨU']]
data = []

for article in articles:
    #print(article)
    title_element = article.find("h2", class_="zm-post-title")
    if not title_element:
        continue
    title = title_element.text.strip()
    if title in skip_keywords or is_duplicate(cursor, title) or title in database_cache:
        #print('Duplicate data found')
        continue

    post_date = article.find("a", class_="zm-date").text.strip()

    # Extract image source if available
    img_element = article.find("div", class_="zm-post-thumb f-left").find('img')
    #print(img_element)
    if img_element:        
        img_url = img_element["src"]        
        #print(f'image_url {image_url}')        
        image_response = requests.get(img_url)
        image_filename = os.path.join('images', f'{title}.jpg')
        try:
            with open(image_filename, 'wb') as f:
                f.write(image_response.content)
        except:
            image_filename = ''
    else:
        image_filename = ''

    pv_content_element = article.find("div", class_="zm-post-content")
    if pv_content_element:
        pv_content = pv_content_element.text.strip()
    else:
        continue
    
    # Extract full content from title link
    full_content_link = title_element.find("a")["href"]    
    try:
        full_content_response = requests.get(full_content_link, timeout=5)
        full_content_soup = BeautifulSoup(full_content_response.content, "html.parser")
        full_content = full_content_soup.find("div", class_="zm-post-content").text.strip()
    except requests.exceptions.ConnectTimeout as e:
        print(f"Error occurred while fetching full content: {e}")
        full_content = ''
            
    # print(f'title: {title}')
    # print(f'date: {post_date}')
    # print(f'image: {image_filename}')
    # print(f'content: {pv_content}')
    # print(f'full content: {full_content}')

    data.append({
        'title': title,
        'post_date': post_date,
        'note': pv_content,
        'content': full_content,
        'image': image_filename
    })
    
#print(f'data: {data}\nThere are {len(data)} titles found')

# Insert data
if data:
    for item in data:      
        cursor.execute("INSERT INTO news (title, note, content, tags, post_date, image) VALUES (?, ?, ?, ?, ?, ?)", 
                       (item['title'], item['note'], item['content'], '', item['post_date'], item['image']))
        
    conn.commit()
    conn.close()
    print("Data saved to the SQLite database successfully.")

else:
    print('No data found or duplicated data')