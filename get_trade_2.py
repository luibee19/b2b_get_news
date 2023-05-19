# Get from https://doanhnghiepvathuongmai.vn/

import requests
from bs4 import BeautifulSoup
import sqlite3
import os
from functions import is_duplicate
from functions import load_database_cache

def get_image(html, title):
    image_element = html.find('img')
    image_url = base_url + image_element["src"]
    image_response = requests.get(image_url)
    image_filename = os.path.join('images', f'{title}.jpg')
    try:
        with open(image_filename, 'wb') as f:
            f.write(image_response.content)
    except Exception as e:
        print(f'Error saving image: {e}')
        image_filename = ''
    
    return image_filename

def get_full_content(html, include_pv_content=False):
    full_content_link = html.find("a")["href"]
    full_content_response = requests.get(full_content_link)
    full_content_soup = BeautifulSoup(full_content_response.content, 'html.parser')
    full_content = full_content_soup.find("div", class_= "header-excerpt").text.strip() + '\n' + full_content_soup.find("article", class_= "entry-content").text.strip()
    post_date_full = full_content_soup.find('div', class_= "col-12 col-md-6 col-xl-6 col-lg-6").text.strip()
    post_date = post_date_full.split(':')[1].strip().split('\n')[0]

    if include_pv_content:
        pv_content = full_content_soup.find("div", class_="header-excerpt").text.strip()
        return full_content, pv_content, post_date
    else:
        return full_content, post_date

database = 'trade.db'
conn = sqlite3.connect(database)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS trade (
        id INTERGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        note TEXT,
        content TEXT,
        tags TEXT,
        post_date TEXT,
        image TEXT
    )
""")

# Load existing data from the database cache
database_cache = load_database_cache(database)

base_url = 'https://doanhnghiepvathuongmai.vn'
url = 'https://doanhnghiepvathuongmai.vn/danh-muc/co-hoi-giao-thuong-vasi-45.phtml?page=1'
response = requests.get(url)
#print(response)
content = response.content

os.makedirs('images', exist_ok=True)

# Parse the HTML
soup = BeautifulSoup(content, "html.parser")
#print(soup.prettify())
article_list = []

main_article = soup.find_all('div', class_= 'post-cat-big')
sub_article = soup.find_all('div', class_= "post-cat-small")
list_article = soup.find_all('div', class_= "category-item")

article_list.append(main_article)
article_list.append(sub_article)
article_list.append(list_article)

data = []

for article in article_list:
    #print(article)
    if article == article_list[0]:
        #print(article_list[0])
        title_element = article[0].find('h3')
        if not title_element:
            continue
        title = title_element.text.strip()
        #print(title)
        if is_duplicate(cursor, title) or title in database_cache:
            continue
        
        image_filename = get_image(article[0], title)
        #print(image_filename)
        
        #print(article[0])
        pv_content = article[0].find('div', 'post-cat-excerpt').text.strip()
        #print(pv_content)
        full_content, post_date = get_full_content(article[0]) 

        data.append({
                'title': title,
                'post_date': post_date,
                'note': pv_content,
                'content': full_content,
                'image': image_filename
            })

    elif article == article_list[1]:        
        for sub in article:
            #print(sub)
            title = sub.find('h3').text.strip()
            #print(title)        
            if is_duplicate(cursor, title) or title in database_cache:
                continue
            
            image_filename = get_image(sub, title)
            #print(image_filename)            
            full_content, pv_content, post_date = get_full_content(sub, include_pv_content=True)
            data.append({
                'title': title,
                'post_date': post_date,
                'note': pv_content,
                'content': full_content,
                'image': image_filename
            })
            
    else:
       for sub in article:
            title = sub.find('h3').text.strip()                 
            if is_duplicate(cursor, title) or title in database_cache:
                continue

            image_filename = get_image(sub, title)
            pv_content = sub.find('div', class_= "category-item-excerpt").text.strip()
            full_content, post_date = get_full_content(sub)
            data.append({
                'title': title,
                'post_date': post_date,
                'note': pv_content,
                'content': full_content,
                'image': image_filename
            })
    

print(f'There are {len(data)} titles found')

if data:
    for item in data:
        cursor.execute("INSERT INTO trade (title, note, content, tags, post_date, image) VALUES (?, ?, ?, ?, ?, ?)",
                        (item['title'], item['note'], item['content'], '', item['post_date'], item['image']))
    
    conn.commit()
    conn.close()
    print("Data saved to the SQLite database successfully.")

else:
    print('No data found or duplicated data')
            


            