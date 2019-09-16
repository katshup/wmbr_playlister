from bs4 import BeautifulSoup
import requests
from urllib import parse
from bullet import ScrollBar
import datetime
import re
import time
import os
from pathlib import Path
from gmusicapi import Mobileclient


class Playlister(object):

    WMBR_SITE = "https://track-blaster.com/wmbr/index.php"
    WMBR_SITE_NO_PHP = "https://track-blaster.com/wmbr/"
    PROG_SEARCH_FILL = {"startdt": "June 28, 1984", "enddt": datetime.datetime.now().strftime("%B %d, %Y"), "sort": "desc"}

    CRED_PATH = os.path.join(str(Path.home()), ".wmbr", "cred")

    def __init__(self):
        self.programs = {}
        site_data = requests.get(self.WMBR_SITE)
        parser = BeautifulSoup(site_data.content, "html.parser")
        program_selector = None

        for selector in parser.find_all("select"):
            if selector.get("name") == "program":
                program_selector = selector

        for option in program_selector.find_all("option"):
            self.programs[option.string] = option.get("value")

        self.mb = Mobileclient()

        if not os.path.exists(os.path.dirname(self.CRED_PATH)):
            os.mkdir(os.path.dirname(self.CRED_PATH))

        if not self.mb.oauth_login(Mobileclient.FROM_MAC_ADDRESS, oauth_credentials="/home/carlos/.wmbr/cred"):
            self.mb.perform_oauth(storage_filepath="/home/carlos/.wmbr/cred")
         

    def playlist_visitor(self, lonk):
        lonk = "".join([self.WMBR_SITE_NO_PHP, lonk])
        print("Visting %s" % lonk)
        lonk_data = requests.get(lonk)
        lonk_parser = BeautifulSoup(lonk_data.content, "html.parser")

        row_divs = lonk_parser.find_all("div", {"id": re.compile("row_[0-9]+")})

        store_ids = []

        for row in row_divs:
            try:
                artist_row = row.find_all("div", class_=re.compile(r"-Artist$"))[1] # gonna get a hidden row with this, actual result should be second in the list
                song_row = row.find_all("div", class_=re.compile(r"-Song$"))[1] # gonna get a hidden row with this, actual result should be second in the list
            except IndexError:
                # apparently there are rows with no contents or are filled with comments instead 
                continue

            artist = artist_row.find("a").string
            song = song_row.find("a").string 

            print("%s : %s" % (artist, song))
            try:
                track_dict = self.mb.search("%s %s" % (artist, song), max_results=10)['song_hits'][0]['track']
                store_ids.append(track_dict['storeId'])
            except IndexError:
                print("No results for %s by %s" % (song, artist))

        return store_ids

    def select_a_program(self):
        playlist_links = set()
        cli = ScrollBar(
            "Select a show: ",
            [*self.programs],
            pointer="🎵",
            height=6,
            align=5,
            margin=3
        )

        program = cli.launch()
        search_fill = self.PROG_SEARCH_FILL.copy() # make a copy of the dict in case we want to do another search
        search_fill['program'] = self.programs[program]
        search_url = "?".join([self.WMBR_SITE,parse.urlencode(search_fill)])
        search_data = requests.get(search_url)
        search_parser = BeautifulSoup(search_data.content, "html.parser")
        playlist_a_tags = search_parser.find_all("a", href=re.compile(r"playlist.php*"))

        for a in playlist_a_tags:
            playlist_links.add(a.get('href'))

        playlist_links = list(playlist_links)

        songz = []
        for lonk in playlist_links:
            time.sleep(1)
            songz.extend(self.playlist_visitor(lonk))

        playlist_id = self.mb.create_playlist(program)

        self.mb.add_songs_to_playlist(playlist_id, songz)

pl = Playlister()
pl.select_a_program()