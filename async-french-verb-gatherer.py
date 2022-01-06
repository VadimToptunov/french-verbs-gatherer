import asyncio
import json
import logging

import aiohttp
import requests
from bs4 import BeautifulSoup

conn = aiohttp.TCPConnector(limit_per_host=250, limit=0, ttl_dns_cache=300)
PARALLEL_REQUESTS = 250
results = []


def get_pages_from_sitemap():
    urls = []
    req = requests.Session()
    sitemap = req.get("https://www.conjugaison.com/sitemap.xml").text
    soup = BeautifulSoup(sitemap, 'lxml')
    locs = soup.find_all("loc")
    for item in locs:
        urls.append(item.text)
    return urls


def get_conjugation(webpage_text):
    titles_text = []
    verbs_to_be_sorted = []
    new_verbs = []
    sorted_conjugations = []
    soup = BeautifulSoup(webpage_text, 'html.parser')
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


async def gather_with_concurrency(n):
    semaphore = asyncio.Semaphore(n)
    session = aiohttp.ClientSession(connector=conn, trust_env=True)

    async def get(url):
        async with semaphore:
            async with session.get(url, ssl=False) as response:
                logging.info(f"{response.url} {response.status}")
                web_text = await response.text()
                results.append(get_cumulated_data(get_conjugation(web_text)))

    await asyncio.gather(*(get(url) for url in get_pages_from_sitemap()))
    await session.close()


if __name__ == "__main__":
    logging.basicConfig(filename="async-french_verbs.log",
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(gather_with_concurrency(PARALLEL_REQUESTS))
    conn.close()

    with open("async-verbs.json", "a+") as file:
        jsonify(results, file)
