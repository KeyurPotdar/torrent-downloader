import logging
import os
import re
import requests
import subprocess
import sys
import tkinter as tk
from bs4 import BeautifulSoup
from multiprocessing import Process

WEBSITE_NAME = 'https://bayhypertpb.be'
WEBSITE_PREFIX = '/s/?q='
WEBSITE_SPACE = '+'
WEBSITE_SUFFIX = '&page=0&orderby=99'

LOGFILE_NAME = os.path.splitext(os.path.basename(__file__))[0] + '.log'
logging.basicConfig(filename=LOGFILE_NAME, level=logging.DEBUG, format='%(asctime)s %(message)s')

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}


def format_episode(season, episode):
    """
    Returns the complete episode formed using `season` and `episode`.

    Example:
    >>> format_episode(3, 11)
    's03e11'
    """
    return 's{:02d}e{:02d}'.format(season, episode)


def format_url(name, season=None, episode=None):
    """
    Returns the URL formed by using `name`, `season` and `episode`.

    Example:
    >>> format_url('the office', 4, 11)
    'https://bayhypertpb.be/s/?q=the+office+s04e11&page=0&orderby=99'
    >>> format_url('the office', 's04e11')
    'https://bayhypertpb.be/s/?q=the+office+s04e11&page=0&orderby=99'
    >>> format_url('the office s04e11')
    'https://bayhypertpb.be/s/?q=the+office+s04e11&page=0&orderby=99'
    """
    if season is None and episode is None:
        return WEBSITE_NAME + WEBSITE_PREFIX + name.replace(' ', WEBSITE_SPACE) + WEBSITE_SUFFIX
    if episode:
        episode = format_episode(season, episode)
    else:
        episode = season
    return WEBSITE_NAME + WEBSITE_PREFIX + name.replace(' ', WEBSITE_SPACE) + WEBSITE_SPACE + episode + WEBSITE_SUFFIX


def download_torrent(link, root=None):
    """
    Starts the torrent download. Requires any torrent application pre-installed (μTorrent, BitTorrent, etc).
    """
    try:
        if root:
            root.destroy()
        r = requests.get(WEBSITE_NAME+link, headers=headers)
        soup = BeautifulSoup(r.text, 'lxml')
        magnet = soup.find('a', {'title': 'Get this torrent'}).get('href')

        # Linux
        if sys.platform.startswith('linux'):
            subprocess.Popen(['xdg-open', magnet], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Windows
        elif sys.platform.startswith('win32'):
            os.startfile(magnet)
        # Cygwin
        elif sys.platform.startswith('cygwin'):
            os.startfile(magnet)
        # macOS
        elif sys.platform.startswith('darwin'):
            subprocess.Popen(['open', magnet], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            subprocess.Popen(['xdg-open', magnet], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        logging.error(str(e), exc_info=True)


def show_torrents(url):
    """
    Scrapes the PirateBay proxy and displays all available torrents.
    """
    # Establish connection and get page content
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

    # Scrape the page
    soup = BeautifulSoup(r.text, 'lxml')
    for row, tr in enumerate(soup.select('#searchResult tr')[1:15], 1):
        det_link = tr.find('a', {'class': 'detLink'})
        name = det_link.text
        href = det_link.get('href')
        seeders, leechers = [x.text for x in tr.find_all('td', {'align': 'right'})]
        info_regex = re.compile(r'Uploaded (.*), Size (.*), ULed by (.*)')
        uploaded, size, uploader = info_regex.search(tr.find('font', {'class': 'detDesc'}).text).groups()
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

    tk.Label(root, text='Separate multiple episodes with\n'
                        'commas(,). Use hyphen(-) to \n'
                        'specify a range of episodes.\n'
                        'Example: 1-5, 6, 8-12', justify=tk.LEFT).grid(row=3, column=1, padx=10, sticky='w')

    # noinspection PyUnusedLocal
    def button1_click(event=None):
        n = name.get().replace("'s", 's').strip()
        if not n or not n.strip():
            return
        try:
            s = int(season.get())
            e = episode.get().split(',')
            for x in e:
                x = x.strip()
                if re.match(r'\d+-\d+', x):
                    f, t = map(int, re.search(r'(\d+)-(\d+)', x).groups())
                    for ep in range(f, t+1):
                        try:
                            url = format_url(n, s, ep)
                            Process(target=show_torrents, args=(url,)).start()
                        except Exception as e:
                            logging.error(str(e), exc_info=True)
                else:
                    try:
                        url = format_url(n, s, int(x))
                        Process(target=show_torrents, args=(url,)).start()
                    except ValueError:
                        continue
                    except Exception as e:
                        logging.error(str(e), exc_info=True)
        except ValueError:
            return

    name.bind('<Return>', button1_click)
    season.bind('<Return>', button1_click)
    episode.bind('<Return>', button1_click)

    tk.Button(root, text='Get Torrents', command=button1_click).grid(row=4, column=1, padx=10, pady=(4, 10), sticky='w')

    tk.Label(root, text='Search: ', anchor='w').grid(row=5, column=0, padx=10, pady=4, sticky='w')
    search = tk.Entry(root, width=30)
    search.grid(row=5, column=1, padx=10, pady=4)

    # noinspection PyUnusedLocal
    def button2_click(event=None):
        s = search.get().strip()
        if s:
            show_torrents(format_url(s))

    search.bind('<Return>', button2_click)
    tk.Button(root, text='Get Torrents', command=button2_click).grid(row=6, column=1, padx=10, pady=(4, 10), sticky='w')

    root.mainloop()


if __name__ == '__main__':
    main()
