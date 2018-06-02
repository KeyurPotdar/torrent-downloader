import os
import sys
import subprocess
import logging
import requests
from bs4 import BeautifulSoup
import tkinter as tk

WEBSITE_NAME = 'https://piratepirate.eu'
WEBSITE_PREFIX = '/s/?q='
WEBSITE_SPACE = '+'
WEBSITE_SUFFIX = '&page=0&orderby=99'

LOGFILE_NAME = os.path.splitext(os.path.basename(__file__))[0] + '.log'
logging.basicConfig(filename=LOGFILE_NAME, level=logging.DEBUG, format='\n%(asctime)s \n%(message)s')

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}


def format_episode(season, episode):
    return 's{:02d}e{:02d}'.format(season, episode)


def format_url(name, season=None, episode=None):
    """
    Usage:
    (1): format_url('the office', 4, 11)
    (2): format_url('the office', 's04e11')
    (3): format_url('the office s04e11')
    """
    if season is None and episode is None:
        return WEBSITE_NAME + WEBSITE_PREFIX + name.replace(' ', WEBSITE_SPACE) + WEBSITE_SUFFIX
    if episode:
        episode = format_episode(season, episode)
    else:
        episode = season
    return WEBSITE_NAME + WEBSITE_PREFIX + name.replace(' ', WEBSITE_SPACE) + WEBSITE_SPACE + episode + WEBSITE_SUFFIX


def download_torrent(link, root=None):
    try:
        if root:
            root.destroy()
        r = requests.get(WEBSITE_NAME+link, headers=headers)
        soup = BeautifulSoup(r.text, 'lxml')
        magnet = soup.find('a', {'title': 'Get this torrent'}).get('href')

        if sys.platform.startswith('linux'):
            subprocess.Popen(['xdg-open', magnet], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elif sys.platform.startswith('win32'):
            os.startfile(magnet)
        elif sys.platform.startswith('cygwin'):
            os.startfile(magnet)
        elif sys.platform.startswith('darwin'):
            subprocess.Popen(['open', magnet], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            subprocess.Popen(['xdg-open', magnet], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        logging.error(str(e), exc_info=True)


def show_torrent_links(url):
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
    except (requests.ConnectionError, requests.HTTPError) as e:
        root = tk.Tk()
        tk.Label(root, text=str(e)).pack()
        root.mainloop()
        return
    except Exception as e:
        logging.error(str(e), exc_info=True)
        return

    root = tk.Tk()
    root.title(url)
    for col, label in enumerate(['Sr No', 'NAME', 'SE', 'LE', 'SIZE', 'UPLOADED', 'LINK'], 1):
        tk.Label(root, text=label).grid(column=col, row=1, sticky=tk.W, padx=10, pady=10)

    soup = BeautifulSoup(r.text, 'lxml')
    for row, tr in enumerate(soup.select('#searchResult tr')[1:15], 1):
        det_link = tr.find('a', {'class': 'detLink'})
        name = det_link.text
        href = det_link.get('href')
        seeders, leechers = [x.text for x in tr.find_all('td', {'align': 'right'})]
        uled, sz, _ = tr.find('font', {'class': 'detDesc'}).text.replace('&nbsp;', '').split(', ')
        uploaded = uled[9:]
        size = sz[5:]
        for col, label in enumerate([row, name, seeders, leechers, size, uploaded], 1):
            tk.Label(root, text=label).grid(column=col, row=row+1, sticky=tk.W, padx=5, pady=5)
        tk.Button(root, text='Download', command=lambda c=href: download_torrent(c, root))\
            .grid(column=7, row=row+1, sticky=tk.W, padx=10, pady=5)

    root.mainloop()


def main():
    root = tk.Tk()
    root.title('PirateBay Torrents')

    tk.Label(root, text='Name: ', anchor='w').grid(row=0, column=0, padx=10, pady=(10, 4), sticky='w')
    tk.Label(root, text='Season: ', anchor='w').grid(row=1, column=0, padx=10, pady=4, sticky='w')
    tk.Label(root, text='Episode: ', anchor='w').grid(row=2, column=0, padx=10, pady=4, sticky='w')

    name = tk.Entry(root, width=30)
    name.grid(row=0, column=1, padx=10, pady=(10, 4))
    name.focus()
    season = tk.Entry(root, width=30)
    season.grid(row=1, column=1, padx=10, pady=4)
    episode = tk.Entry(root, width=30)
    episode.grid(row=2, column=1, padx=10, pady=4)

    # noinspection PyUnusedLocal
    def button1_click(event=None):
        n = name.get().replace("'s", 's')
        try:
            s = int(season.get())
            e = int(episode.get())
        except ValueError:
            return
        if all(x for x in (n, s, e)):
            try:
                show_torrent_links(format_url(n, s, e))
            except Exception as e:
                logging.error(str(e), exc_info=True)

    name.bind('<Return>', button1_click)
    season.bind('<Return>', button1_click)
    episode.bind('<Return>', button1_click)

    tk.Button(root, text='Get Torrents', command=button1_click).grid(row=3, column=1, padx=10, pady=(4, 10), sticky='w')

    tk.Label(root, text='Search: ', anchor='w').grid(row=4, column=0, padx=10, pady=4, sticky='w')
    search = tk.Entry(root, width=30)
    search.grid(row=4, column=1, padx=10, pady=4)

    # noinspection PyUnusedLocal
    def button2_click(event=None):
        s = search.get()
        if s:
            show_torrent_links(format_url(s))

    search.bind('<Return>', button2_click)
    tk.Button(root, text='Get Torrents', command=button2_click).grid(row=5, column=1, padx=10, pady=(4, 10), sticky='w')

    root.mainloop()


if __name__ == '__main__':
    main()
