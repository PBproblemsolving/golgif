from bs4 import BeautifulSoup
from datetime import date, datetime
import logging
import re

logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
        
class FutureGame(Exception):
    "Raised when game will be played tomorrow or later"
    pass

class NoDate(Exception):
    "Raised when game date was not in a.tag and date from previous game wasn't provided"
    pass

def title_text(competition_name):
    return competition_name + '  ' + str(date.today())

def body_text(games: list[dict]):
    games = [str(match).replace('\'', '') for match in games]
    return '\n\n'.join(games)
    
def game_dict_parser(game_dict):
    assert len(game_dict) == 7
    temp_dict = AttrDict(game_dict)
    temp_dict.host = "[{}]({})".format(temp_dict.host, temp_dict.host_link)
    temp_dict.pop('host_link', None)
    temp_dict.guest = "[{}]({})".format(temp_dict.guest, temp_dict.guest_link)
    temp_dict.pop('guest_link', None)
    temp_dict.time = "[{}]({})".format(temp_dict.time, temp_dict.match_link)
    temp_dict.pop('match_link', None)
    temp_dict.pop('status', None)
    return temp_dict

def is_theDay(checked_date_string:date, theDay:date):
    return datetime.strptime(checked_date_string, '%d.%m.%Y').date() == theDay
    
def is_today(checked_date_string:date):
    time = is_theDay(checked_date_string, date.today())
    return time

def is_past(date_string):
    return datetime.strptime(date_string, '%d.%m.%Y').date() < date.today()
    
def is_future(date_string):
    return datetime.strptime(date_string, '%d.%m.%Y').date() > date.today()

class MotherCompetitions():
    
    
    
    def __init__(self) -> None:
        self.helper_date = None
        self.helper_time = None
        self.date_pattern = re.compile(r"\b(\d{1,2})[.\s](.*)[.\s](\d{4})\b")
        logging.basicConfig(filename='failed_extractions.log', encoding='utf-8', level=logging.WARN)
        
    def single_game(self, game) -> dict or bool:
        game_dict = {}
        game_date = self.date_pattern.search(game[0].text)
        if game_date:
            game_date = game_date.group(0)
            game_dict['date'] = game_date
            self.helper_date = game_date
        elif self.helper_date:
            game_dict['date'] = self.helper_date
        else:
            logging.warning('Failed, no date available:{}'.format(str(game)))
            raise NoDate
            
        game_time = game[1].text.strip()
        if game_time:
            game_dict['time'] = game_time
            self.helper_time = game_time
        else:
            if self.helper_time:
                game_dict['time'] = self.helper_time
            else:
                logging.warning('Failed, no time available:{}'.format(str(game)))
                game_dict['time'] = 'b/d'
                
        game_dict['host'] = game[2].a.text.strip()
        game_dict['guest'] = game[6].a.text.strip()
        
        assert game_dict['date']
        assert game_dict['guest']
        assert game_dict['host']
        assert game_dict['time']
        
        return game_dict

class DomesticLeague(MotherCompetitions):

    @staticmethod
    def oneSeason_gamedays(soup):
        gamedays = soup.body.div.main.find_all('div', {'class': 'content-box-headline'})
        return [gameday.parent for gameday in gamedays]
    
    @staticmethod        
    def oneDay_games(gameday):
        gameday = gameday.table.tbody.find_all('tr')
        return [game.find_all('td') for game in gameday if not game.has_attr('class')] #9 matches 

class DomesticCup(MotherCompetitions):
    
    @staticmethod
    def parse_date(string_date: str):
        mapping = {'sty': '01', 'lut': '02', 'mar': '03', 'kwi': '04', 'maj': '05', 'cze': '06', 
                   'lip': '07', 'sie': '08', 'wrz': '09', 'paź': '10', 'lis': '11', 'gru': '12'}
        string_date = string_date.split(' ')
        string_date[1] = mapping[string_date[1]]
        return '.'.join(string_date)
    
    @staticmethod
    def two_top_rounds(soup: BeautifulSoup):
        rounds = soup.find('div', {'class': 'large-8 columns'}).div.find_next_sibling('div').table.find_all('tbody')
        if len(rounds) >= 2:
            return rounds[0:2]
        else:
            return rounds[0:1]
    
    @staticmethod
    def games_from_round(round):
        round = round.find_all('tr')
        return [game.find_all('td') for game in round if not game.has_attr('class')]

class EuroCup(DomesticCup):
    pass

class Fixtures():
    
    base_link = 'https://www.transfermarkt.pl/aktuell/waspassiertheute/aktuell/new/datum/'
    
    @staticmethod
    def fixtures_link(checked_date:date | None = None) -> str:
        if not checked_date:
            checked_date = datetime.today().date()
        checked_date = str(checked_date)
        #assert re.match("\\d{4}-\\d{2}-\\d{2}",checked_date)
        link = Fixtures.base_link + checked_date
        return link
        
    @staticmethod
    def matches_by_competitions(aktuell_soup: BeautifulSoup):
        competitions = aktuell_soup.find_all('tr', {'class': 'wettbewerbsZeile'})
        times = {}
        for league in competitions:
            title = league.td.div.div.div.a.text
            link = league.td.div.div.div.a['href']
            games = league.parent.find_all('tr', {'class': 'begegnungZeile'}, recursive=False)
            times[link] = (title, games)
        return times
            
    @staticmethod
    def single_match(match_html):
        match_dict = AttrDict()
        match = match_html.findAll('td')
        try:
            entry = match[2]
            match_dict.host = entry.find('span', {'class': 'vereinsname'}).a.text
        except (AttributeError, TypeError) as e:
            logging.error(f'{e}: {entry}')
            match_dict.host = ''
        try:
            entry = match[2]
            match_dict.host_link = entry.find('span', {'class': 'vereinsname'}).a['href']
            match_dict.host_link = 'https://www.transfermarkt.pl' + match_dict.host_link
        except (AttributeError, TypeError) as e:
            logging.error(f'{e}: {entry}')
            match_dict.host_link = ''
        try:
            entry = match[4]
            match_dict.guest = entry.find('span', {'class': 'vereinsname'}).a.text
        except (AttributeError, TypeError) as e:
            logging.error(f'{e}: {entry}')
            match_dict.guest = ''
        try:
            entry = match[4]
            match_dict.guest_link = entry.find('span', {'class': 'vereinsname'}).a['href']
            match_dict.guest_link = 'https://www.transfermarkt.pl' + match_dict.guest_link
        except (AttributeError, TypeError) as e:
            logging.error(f'{e}: {entry}')
            match_dict.guest_link = ''
        try:
            entry = match[3]
            match_dict.time = entry.span.a.span.text
        except (AttributeError, TypeError) as e:
            logging.error(f'{e}: {entry}')
            match_dict.time = ''
        try:
            entry = match[3]
            match_dict.match_link = match[3].span.a['href']
            match_dict.match_link = 'https://www.transfermarkt.pl' + match_dict.match_link 
        except (AttributeError, TypeError) as e:
            logging.error(f'{e}: {entry}')
            match_dict.match_link = ''
        try:
            entry = match[3]
            match_dict.status = ' '.join(match[3].span.a.span['class'])
        except (AttributeError, TypeError) as e:
            logging.error(f'{e}: {entry}')
            match_dict.status = ''
        return match_dict