import datetime
import json
import logging
import requests
import time
from bs4 import BeautifulSoup


def get_pages_from_sitemap():
    urls = []
    req = requests.Session()
    sitemap = req.get("https://www.conjugaison.com/sitemap.xml").text
    soup = BeautifulSoup(sitemap, 'lxml')
    locs = soup.find_all("loc")
    for item in locs:
        urls.append(item.text)
    return urls


def get_conjugation(url_link):
    global webpage
    titles_text = []
    verbs_to_be_sorted = []
    new_verbs = []
    sorted_conjugations = []
    try:
        webpage = requests.get(url_link)
    except Exception as exception:
        logging.debug(exception)
        time.sleep(30)
        requests.get(url_link)
        pass

    logging.info(f"{webpage.url} {webpage.status_code}")
    soup = BeautifulSoup(webpage.text, 'html.parser')
    titles = soup.find_all('h2')
    [titles_text.append(item.text) for item in titles]
    verbeboxes = soup.find_all('div', {'class': 'col-xs-6 col-sm-6 col-md-3 col-lg-3 verbebox'})
    [verbs_to_be_sorted.append(item.text.strip().replace('\n', ';').replace(";;", ";").strip()) for item in verbeboxes]
    for item in verbs_to_be_sorted:
        if len(item) > 1:
            new_verbs.append(item)
    for item in new_verbs:
        sorted_conjugations.append(item.split(";"))

    return sorted_conjugations


def get_cumulated_data(sorted_conjugations: list):
    verb_dict = {
        'Infinitif': sorted_conjugations[0:2],
        'Participe': sorted_conjugations[2:4],
        'Indicatif': sorted_conjugations[4:12],
        'Subjonctif': sorted_conjugations[12:16],
        'Conditionnel': sorted_conjugations[16:19],
        'Impératif': sorted_conjugations[19:21]
    }
    return verb_dict


def jsonify(data, json_file):
    json.dump(data, json_file, indent=4, sort_keys=False, ensure_ascii=False)


if __name__ == "__main__":
    logging.basicConfig(filename="french_verbs.log",
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)
    verbs = []
    counter = 0
    list_of_links = get_pages_from_sitemap()
    for url in list_of_links:
        verbs.append(get_cumulated_data(get_conjugation(url)))
        counter += 1
        logging.info(f"{counter}/{len(list_of_links)}")

    with open(f"verbes-conjugaison-dictionnaire{datetime.date.today()}.json", "a+") as file:
        jsonify(verbs, file)
