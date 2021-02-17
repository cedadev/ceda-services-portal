import requests
from requests.auth import HTTPBasicAuth
import pandas as pd

source = requests.get(
    'http://team.badc.rl.ac.uk/cgi-bin/pgweb/websql.cgi.pl?tbname=account_types&db=userdb&query=select+*+from+tbdatasets',
    auth=HTTPBasicAuth('USERNAME', 'PASSWORD'),
)

df = pd.read_html(source.text)[0]
for index, row in df.iterrows():
    # every other row in source database is empty
    if index % 2 == 0:
        params = {
            'category_name': 'default',
            'category_long_name': 'default',
            'service_name': row['Grp'] if pd.isnull(row['Grp']) else row['Datasetid'],
            'service_summary': row['Description'],
        }

        result = requests.get('http://0.0.0.0:8000/api/v1/service/create/', params=params)
