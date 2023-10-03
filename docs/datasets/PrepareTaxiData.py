# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.15.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# +
import pandas as pd

#download any month of data for yellow cabs https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
data = pd.read_parquet("/Users/sirsh/Downloads/yellow_tripdata_2023-01.parquet")
#get the zone lookup from some site 
zones = pd.read_csv("/Users/sirsh/Downloads/taxi+_zone_lookup.csv")
data.head()
# -

zones.head()

# +
columns = {
    "tpep_pickup_datetime": 'pick_up_at',
    "tpep_dropoff_datetime": 'drop_off_at',
    "passenger_count": "passenger_count",
    "trip_distance": "trip_distance",
    "payment_type": "payment_type",
    "congestion_surcharge": "congestion_surcharge",
    "airport_fee": "airport_fee",
    "Borough": "borough_pick_up",
    "Zone": "zone_pick_up",
    "Borough_drop_off": "borough_drop_off",
    "Zone_drop_off": "zone_drop_off"
}

def payment_types (i):
    """
    from the data dict for sourced data on site
    """
    return ['Credit card', 'Cash', 'No charge', 'Dispute', 'Unknown'][i-1]

data = pd.merge(data,zones, left_on='PULocationID', right_on='LocationID', suffixes=['', '_pick_up'])
data = pd.merge(data,zones, left_on='DOLocationID', right_on='LocationID', suffixes=['', '_drop_off'])
data['payment_type'] = data['payment_type'].map(payment_types)
data = data.rename(columns=columns)
data = data.drop(columns=[c for c in data.columns if c not in columns.values()],index=1).reset_index()
sample = data[::100].reset_index(drop=True)
sample['pick_up_at'] = pd.to_datetime(sample['pick_up_at'])
sample['drop_off_at'] = pd.to_datetime(sample['drop_off_at'])
sample.head()

# +
# from tqdm import tqdm
# import time
# from langchain.utilities import WikipediaAPIWrapper
# wikipedia = WikipediaAPIWrapper()
# trivia = []
 

# for zone in tqdm(sample['zone_pick_up'].unique()):
#     try:
#         trivia.append(   {"entity_type" : 'nyc_zone', "entity_key": zone, 'text' : wikipedia.run(zone)})
#         time.sleep(2)
#     except:
#         pass
        
# trivia = pd.DataFrame(trivia).reset_index()
# trivia['id'] = trivia['index']
# trivia.to_csv("/Users/sirsh/Downloads/nyc_zones.csv", index=None)
# trivia  

# -

import pandas as pd
passengers = pd.read_csv("/Users/sirsh/Downloads/avengers.csv", encoding='latin-1')
passengers = passengers[['URL', 'Name/Alias', 'Appearances', 'Gender']].rename(columns={'Name/Alias':'Name', 'URL' : 'uri'})
passengers.columns = [c.lower() for c in passengers.columns]
passengers



# +
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
def scrape_html_paragraphs(uri):
    """
    util - we dont care about errors - this is a try or ignore for test data
    """
    try:
        response = requests.get(uri)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string
            paragraphs = soup.find_all('p')
            for i, p in enumerate(paragraphs):
                yield i, p.get_text()
        else:
            return None
    except Exception as e:
        return None

bios = []
for record in tqdm(passengers.to_dict('records')):  
    for i, text in scrape_html_paragraphs(record['uri']):
        bios.append(   {"entity_type" : 'people', "entity_key": f"{record['name']}_{i}", 'text' : text})

bios = pd.DataFrame(bios)
bios.to_csv("/Users/sirsh/Downloads/marvel_bios.csv", index=None)
bios
# -

bios.iloc[10]['text'] 

import numpy as np
sample['passenger_name'] = np.random.choice(passengers['name'], len(sample))
sample




