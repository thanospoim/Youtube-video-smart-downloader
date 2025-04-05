from serpapi import GoogleSearch
import json
import pandas as pd
from random import randint
from config import key
choose = input('Which song you want to download?')
params = {
    "engine":"youtube",
    "search_query": str(choose),
    "api_key" : key,
    "output" : "JSON"
}

search = GoogleSearch(params)
results = search.get_dict()
video_results = results['video_results'][:4]

df = pd.DataFrame(video_results)
df_select = df[['position_on_page','title','link']]
df_select2 = df[['link']]
with open("result.json", "w") as json_file:
    json.dump(video_results, json_file, indent=4)

x = randint(1,4)
if x == 1:
    print('num = ',x)
    print(df_select.head(4))
    print(df_select2.head(4).iloc[0,0])
    df_select3 = df_select2.head(4).iloc[0,0]
elif x == 2 :
    print('num = ',x)
    print(df_select.head(4))
    print(df_select2.head(4).iloc[1,0])
    df_select3 = df_select2.head(4).iloc[1,0]
elif x == 3:
    print('num = ',x)
    print(df_select.head(4))
    print(df_select2.head(4).iloc[2,0])
    df_select3 = df_select2.head(4).iloc[2,0]
else:
    print('num = ',x)
    print(df_select.head(4))
    print(df_select2.head(4).iloc[3,0])
    df_select3 = df_select2.head(4).iloc[3,0]

