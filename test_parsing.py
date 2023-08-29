from transfermarkt_parsing import MotherCompetitions, \
DomesticLeague, DomesticCup, EuroCup, Fixtures
from transfermarkt_parsing import is_theDay
from bs4 import BeautifulSoup
import datetime
import requests
import pytest
from transfermarkt import main_cups, second_cups

f = Fixtures()
headers = {
'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36',
}

past_date = datetime.datetime.strptime('02.03.2023', '%d.%m.%Y').date()
competition = "/cbf-brasileiro-u20/startseite/wettbewerb/CB20/saison_id/2022"
r = requests.get(f.fixtures_link(past_date), headers=headers)
soup = BeautifulSoup(r.text, 'html.parser')  

def test_link():
    assert f.fixtures_link(past_date) == 'https://www.transfermarkt.pl/aktuell/waspassiertheute/aktuell/new/datum/2023-03-02'
        

def test_matches_by_competitions():
    
    test_02_03 = f.matches_by_competitions(soup)
    assert len(test_02_03) == 44
    assert len(test_02_03[competition][1]) == 3
    print(test_02_03.keys())
    
def test_single_match():
    match = f.single_match(f.matches_by_competitions(soup)[competition][1][1])
    print(match)
    assert match.host == 'Grêmio U20'
    assert match.host_link == 'https://www.transfermarkt.pl/gremio-porto-alegre-u20/spielplan/verein/12690/saison_id/2022'
    assert match.guest == 'Athletico U20'
    assert match.guest_link == 'https://www.transfermarkt.pl/club-athletico-paranaense-u20/spielplan/verein/15038/saison_id/2022'
    assert match.time == '2:1'
    assert match.match_link == 'https://www.transfermarkt.pl/spielbericht/index/spielbericht/4034041'
    assert match.status == 'matchresult finished'