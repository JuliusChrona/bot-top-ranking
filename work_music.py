import requests
import random
import csv

from bs4 import BeautifulSoup as BS

# CHARTS_URL = r'https://megapesni.com/online/'
CHARTS_URL = r'https://megapesni.com/rock_chart.html'
MAIN_URL = r'https://megapesni.com'
OK_STATUS_CODE = 200

ZAYCEV_URL = r'https://zaycev.net'


def get_links(count_music):
    response = requests.get(CHARTS_URL)
    if response.status_code != OK_STATUS_CODE:
        return []
    page = BS(response.text, 'html.parser')
    download_links_a = page.find_all('a', class_='popular-download-link')
    random.shuffle(download_links_a)
    links = []
    titles = []

    for link in download_links_a[:count_music]:
        response = requests.get(MAIN_URL + str(link.get('href')))
        if response.status_code != OK_STATUS_CODE:
            continue
        download_page = BS(response.text, 'html.parser')
        links.append(download_page.find('a', class_='song-author-btn song-author-btn--download').get('href'))
        title = download_page.find('h1', class_='music-title').text
        titles.append(title)
    return links, titles

def download_music_link(music_link):
    link = MAIN_URL + music_link
    req = requests.get(link, stream=True)
    if req.status_code == OK_STATUS_CODE:
        with open('song.mp3', 'wb') as mp3:
            mp3.write(req.content)

def create_csv(file_name, music_count):
    """This is function create csv file from ZAYCEV.NET
    ```
    title, author, link
    ```
    ```py
    create_csv("music.csv")
    ```
    Args:
        file_name (str): Path to csv file
    """
    songs = []

    response = requests.get(ZAYCEV_URL)
    soup = BS(response.content, 'html.parser')

    all_top_songs = soup.find_all(class_='musicset-track__download-link')

    for song_a in all_top_songs[:music_count+1]:
        song = {}
        song['author'], song['title'] = song_a.get('title').split(' ', 2)[-1].split(' – ', 1)
        song['link'] = 'https://zaycev.net' + song_a.get('href')
        songs.append(song)

    with open(file_name, mode="w", encoding='utf-8') as w_file:
        names=["title", "author", "link"]
        csv_writer = csv.DictWriter(w_file, delimiter=',', lineterminator='\r', fieldnames=names)
        csv_writer.writeheader()
        for song in songs:
            csv_writer.writerow(song)

def get_music_csv(file_name):
    """This is function return a list that contain song
    ```py
    get_music_csv("music.csv")
    ```
    Args:
        file_name (str): Path to csv file
    Returns:
        list[dict]: List with list of music with ```title, author, link```
    """
    songs = []
    with open(file_name, encoding='utf-8') as r_file:
        csv_reader = csv.DictReader(r_file, delimiter=',')
        for idx, song in enumerate(csv_reader):
            if idx == 0:
                continue
            song['mark'] = 0
            song['pos'] = idx
            songs.append(song)
    return songs