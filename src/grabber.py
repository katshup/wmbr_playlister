from bs4 import BeautifulSoup
import requests
from urllib import parse
from bullet import ScrollBar
import datetime
import re

WMBR_SITE = "https://track-blaster.com/wmbr/index.php"
WMBR_SITE_NO_PHP = "https://track-blaster.com/wmbr/"

def playlist_visitor(lonk):
    lonk = "".join([WMBR_SITE_NO_PHP, lonk])
    print("Visting %s" % lonk)
    lonk_data = requests.get(lonk)
    lonk_parser = BeautifulSoup(lonk_data.content, "html.parser")

    row_divs = lonk_parser.find_all("div", {"id": re.compile("row_[0-9]+")})
    # row_divs = lonk_parser.select('div[id*="row_"]')

    for row in row_divs:
        artist_row = row.find_all("div", class_=re.compile(r"-Artist$"))[1] # gonna get a hidden row with this, actual result should be second in the list
        song_row = row.find_all("div", class_=re.compile(r"-Song$"))[1]

        artist = artist_row.find("a").string
        song = song_row.find("a").string 

        print("%s : %s" % (artist, song))

search_fill = {"startdt": "June 28, 1984", "enddt": datetime.datetime.now().strftime("%B %d, %Y"), "sort": "desc"}

site_data = requests.get(WMBR_SITE)

parser = BeautifulSoup(site_data.content, "html.parser")

program_selector = None

programs = {}

for selector in parser.find_all("select"):
    if selector.get("name") == "program":
        program_selector = selector

for option in program_selector.find_all("option"):
    programs[option.string] = option.get("value")


cli = ScrollBar(
    "Select a show: ",
    [*programs],
    pointer="🎵",
    height=6,
    align=5,
    margin=3
)

program = cli.launch()

search_fill['program'] = programs[program]

search_url = "?".join([WMBR_SITE,parse.urlencode(search_fill)])

search_data = requests.get(search_url)

search_parser = BeautifulSoup(search_data.content, "html.parser")

playlist_a_tags = search_parser.find_all("a", href=re.compile(r"playlist.php*"))

playlist_links = set()

for a in playlist_a_tags:
    playlist_links.add(a.get('href'))

playlist_links = list(playlist_links)

# for lonk in playlist_links:
playlist_visitor(playlist_links[0])