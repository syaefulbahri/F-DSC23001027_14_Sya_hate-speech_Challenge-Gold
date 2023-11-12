import re
import pandas as pd

from flask import Flask, jsonify
from flask import request
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flasgger import swag_from

import sqlite3

class CustomFlaskAppWithEncoder(Flask):
    json_provider_class = LazyJSONEncoder

app = CustomFlaskAppWithEncoder(__name__)

df = pd.read_csv('data.csv', encoding='ISO-8859-1')

daftar_alay = pd.read_csv('new_kamusalay.csv', encoding='ISO-8859-1', header=None)
daftar_alay = daftar_alay.rename(columns={0: 'awal', 1: 'ganti'}) 


app.json_encoder = LazyJSONEncoder
swagger_template = dict(
info = {
    'title': LazyString(lambda: 'API Documentation for Data Processing and Modeling'),
    'version': LazyString(lambda: '1.0.0'),
    'description': LazyString(lambda: 'Dokumentasi API untuk Data Processing dan Modeling'),
    },
    host = LazyString(lambda: request.host)
)
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'docs',
            "route": '/docs.json',
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}
swagger = Swagger(app, template=swagger_template, config=swagger_config)

#Cleansing
def bersih_bersih(text):
    text = re.sub('\n',' ',text)
    text = re.sub('rt',' ',text)
    text = re.sub('user',' ',text)
    text = re.sub('((www\.[^\s]+)|(https?://[^\s]+)|(http?://[^\s]+))',' ',text)
    text = re.sub('  +', ' ', text)
    text = re.sub('[^0-9a-zA-Z]+', ' ', text)
    return text

def lowercase(text):
    return text.lower()

kamus_alay = dict(zip(daftar_alay['awal'], daftar_alay['ganti']))
def ganti_alay(text):
    return ' '.join([kamus_alay[word] if word in kamus_alay else word for word in text.split(' ')])

#Jadikan satu fungsi Cleansing
def cleansing(text):
    text = bersih_bersih(text) 
    text = lowercase(text)
    text = ganti_alay(text)
    return text

#endpoint
@swag_from("docs/hello_world.yml", methods=['GET'])
@app.route('/', methods=['GET'])
def hello_world():
    json_response = {
        'status_code': 200,
        'description': "API untuk Data Cleansing",
        'data': "Syaeful Bahri : Binar Academy, Data Science Gelombang 14",}

    response_data = jsonify(json_response)
    return response_data

#endpoint teks input
@swag_from("docs/text_processing.yml", methods=['POST'])
@app.route('/text-processing', methods=['POST'])
def text_processing():

    text = request.form.get('text')

    json_response = {
        'status_code': 200,
        'description': "Teks yang sudah diproses",
        'data' : cleansing(text)}

    response_data = jsonify(json_response)
    return response_data

#endpoint teks upload
@swag_from("docs/text_processing_file.yml", methods=['POST'])
@app.route('/text-processing-file', methods=['POST'])
def text_processing_file():

    file = request.files.getlist('file')[0]
    df = pd.read_csv(file, encoding='ISO-8859-1')

    cleaned_text = []
    for text in df['Tweet']:
        
        cleaned_text.append(cleansing(text))

    df['cleaned_text'] = cleaned_text

    conn = sqlite3.connect('cleantweet_database1.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tweets (
            id INTEGER PRIMARY KEY,
            tweet_text TEXT,
            cleaned_text TEXT)''')
    
    for text, cleaned_text in zip(df['Tweet'], cleaned_text):
        cursor.execute('''
            INSERT INTO tweets (tweet_text, cleaned_text)
            VALUES (?, ?)''',
            (text, cleaned_text))

    conn.commit()
    conn.close()

    json_response = {
        'status_code': 200,
        'description': "Teks yang sudah diproses",
        'data': cleaned_text}
    
    response_data = jsonify(json_response)
    return response_data

if __name__ == '__main__':
   app.run()