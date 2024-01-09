from meczbot import reddit
import requests
from bs4 import BeautifulSoup
from time import sleep
from sub_dict import leagues
import json
import logging
import re
from datetime import datetime
from collections import namedtuple
from meczbot import rand_headers


headers = {
'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36',
}
base_link = "https://www.transfermarkt.com"
FromScorerTuple = namedtuple('FromScorerTuple', 
                          ['scorer_id', 'goal_for', 'goal_against', 'season', 'league_abbr', 
                                     'matchdate', 'round', 'venue'])

def trans_date_parser(date_string):
    return datetime.strptime(date_string, "%m/%d/%y").date()
    
def get_competitors(input_string):
    score = re.findall(r'\[*\d\]*\s*-\s*\d|\d\s*-\s*\[*\d\]*', input_string)
    if score:
        score = re.sub(r"[\[\]]", '', score[0])
    splitted = input_string.split('-')
    home = ' '.join(splitted[0].split()[:-1])
    away = ' '.join(splitted[1].split()[1:])
    scorer = re.sub(r'\([^)]*\)','',' '.join(splitted[2:]))
    scorer = ' '.join(scorer.split("'")[:-1])
    scorer = re.sub(r"[0-9']", '', scorer)
    return home, away, scorer, score

def check_competition_offline(input_string: str, resource: dict):
    return resource.get(input_string)

def transfermarkt_query(input_string):
    link = "https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query={}"
    input_string = '+'.join(input_string.split())
    link = link.format(input_string)
    return link

def check_scorer_online(input_string):
    while input_string:
        link = transfermarkt_query(input_string)
        r = requests.get(link, headers=rand_headers()).text    
        soup = BeautifulSoup(r, 'html.parser')
        try:
            soup = soup.find('div', {'id':'main'})
            soup = soup.main.find_all('div', recursive=False)[0]
            soup = soup.table.tbody.find_all('tr', recursive=False)
            soup = soup[0].find('td', {'class':'hauptlink'}).a['href']
        except AttributeError as e:
            logging.info("input: {} raises {}".format(input_string, e))
            input_string = ' '.join(input_string.split(' ')[:-1]).strip()
            continue
        if 'spieler' in soup:
            return soup
        else:
            input_string = ' '.join(input_string.split(' ')[:-1]).strip()
    else:
        return None
        
        
def check_competition_online(input_string):
    link = transfermarkt_query(input_string)
    r = requests.get(link, headers=rand_headers()).text
    soup = BeautifulSoup(r, 'html.parser')
    soup = soup.find('div', {'id':'main'})
    soup = soup.main.find_all('div', recursive=False)
    for div in soup:
        div = div.table.tbody.find_all('tr', recursive=False)
        div = div[0].find('td', {'class':'hauptlink'}).a['href']
        if 'verein' not in div:
            print(div)
            continue
        div = str(div).replace('startseite', 'spielplan')
        link = "https://www.transfermarkt.pl" + div
        html = requests.get(link, headers=rand_headers()).text
        div = BeautifulSoup(html, 'html.parser')
        div = div.find_all('div', {'class': 'table-header'})
        return [competition.h2.a['href'] for competition in div]
    return None

def goal_data_from_scorer(scorer_link: str, timestamp):
    submition_date = datetime.fromtimestamp(timestamp).date()
    scorer_link = scorer_link.replace('profil', 'leistungsdaten')
    scorer_id = scorer_link.split('/')[-1]
    link = base_link + scorer_link
    r = requests.get(link, headers=rand_headers()).text
    soup = BeautifulSoup(r, 'html.parser')
    soup = soup.find('div', {'class': 'large-8 columns'})
    soup = soup.findAll('div', {'class': 'box'}, recursive=False)[2:]
    for competition in soup:
        matches = competition.findAll('tr')
        league_abbr = competition.div.a['name']
        for match in matches[1:-1]:
            match = match.findAll('td')
            try:
                round = match[0].text.strip()
                matchdate = trans_date_parser(match[1].text)
                if matchdate != submition_date:
                    continue
                try:
                    int(match[-6].text.strip())
                except (IndexError, ValueError):
                    continue
                venue = match[2].text
                goal_for = match[3].a['href'].split('/')[-3]
                goal_against = match[5].a['href'].split('/')[-3]
                season = match[3].a['href'].split('/')[-1]
            except IndexError or AttributeError:
                continue
            return FromScorerTuple(scorer_id, goal_for, goal_against, season, league_abbr, 
                                     matchdate, round, venue)
    else:
        return None
            
def links_from_comment(comment):
    comment.refresh()
    replies = comment.replies
    for replie in replies:
        pass
    return None
    
def get_player_info(player_id):
    assert player_id
    link = "https://www.transfermarkt.com/player/leistungsdaten/spieler/{}".format(player_id)
    r = requests.get(link, headers=rand_headers()).text
    soup = BeautifulSoup(r, 'html.parser')
    soup = soup.find('header', {'class': 'data-header'})
    soup_name = soup.find('div', {'class': 'data-header__headline-container'})
    try:
        name = soup_name.h1.text.strip().split('\n')[1].strip()
    except IndexError:
        name = soup_name.h1.text.strip()
    soup = soup.find('div', {'class':"data-header__info-box"})
    soup = soup.div.ul.find_all('li')
    birth_date, birth_city, birth_state, citizenship_state = None, None, None, None
    for entry in soup:
        match entry.text.split(':')[0].strip():
            case "Date of birth/Age":
                birth_date = entry.span.text.strip()
                birth_date = re.sub(r"(,|\([^)]*\))", "", birth_date)
                birth_date = birth_date.split()
                if len(birth_date) == 1:
                    birth_date = '0' + birth_date
                birth_date = " ".join(birth_date)
                birth_date = datetime.strptime(birth_date, "%b %d %Y").date()
                birth_date = datetime.strftime(birth_date, "%Y-%m-%d")
            case "Place of birth":
                birth_city = entry.span.text.strip()
                try:
                    birth_state = entry.img['title']
                except AttributeError as e:
                    logging.error(player_id + "causes (no img)" + e)
            case "Citizenship":
                citizenship_state = entry.span.text.strip()
    return name, birth_date, birth_city, birth_state, citizenship_state

def get_team_info(team_id):
    assert team_id
    link = "https://www.transfermarkt.com/team/startseite/verein/{}".format(team_id)
    r = requests.get(link, headers=rand_headers()).text
    soup = BeautifulSoup(r, 'html.parser')
    soup = soup.find('header', {'class': 'data-header'})    
    name = soup.div.h1.text.strip()
    return name, 
    
def get_league_info(league_abbr):
    assert league_abbr
    link = "https://www.transfermarkt.com/leauge/startseite/pokalwettbewerb/{}".format(league_abbr)
    r = requests.get(link, headers=rand_headers()).text
    soup = BeautifulSoup(r, 'html.parser')
    soup = soup.find('header', {'class': 'data-header'})    
    name = soup.div.h1.text.strip()
    soup = soup.find('div', {'class': 'data-header__info-box'}).div.ul.li.span
    try:
        state_name = soup.img['title']
    except (AttributeError, TypeError):
        state_name = None
    tier = soup.text.strip()
    return name, state_name, tier
    
if __name__ == '__main__':
    while True:
        try:
            logging.basicConfig(filename='golgif.log', encoding='utf-8', level=logging.INFO)
            subreddit = reddit.subreddit('soccer')
            result = subreddit.stream.submissions(skip_existing=True)


            template = "[{}]({})"


            with open('data.json', encoding='utf-8') as f:
                for submission in result:
                    if submission.link_flair_text == 'Media':
                        if '-' in submission.title:
                            threads = json.load(f)
                            f.seek(0)
                            competitors = get_competitors(submission.title)
                            logging.info(submission.title)
                            try:
                                competitions_links = check_competition_online(competitors[0])
                            except AttributeError as e:
                                try:
                                    competitions_links = check_competition_online(competitors[1])
                                except AttributeError:
                                    competitions_links = None
                            if competitions_links:
                                for link in competitions_links:
                                    thread_title = leagues.get(link.split('/')[4])
                                    if thread_title:
                                        thread_id = threads.get(thread_title)
                                        if thread_id:
                                            thread = reddit.submission(thread_id)
                                            thread.reply(template.format(submission.title, 
                                                                         submission.url))
                                            logging.info('Submitted: {}'.format(submission.title))
                                            break
        except Exception as e:
            logging.exception(e)
            continue
