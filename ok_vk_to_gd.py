from urllib.parse import urljoin
import datetime
import json
import tqdm
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
import requests
import os

token_vk = 'tok.txt'  # токен и id вк
token_ok = 'tok_ok.txt'  # ключи к ок и id
token_gd = ''  # адрес к токенам гугл драйва


def get_token_vk(file_name):
    with open(os.path.join(os.getcwd(), file_name), 'r') as token_file:
        token = token_file.readline().strip()
        token_id = token_file.readline().strip()
    return [token, token_id]


def get_token_ok(file_name):
    with open(os.path.join(os.getcwd(), file_name), 'r') as token_file:
        app_key = token_file.readline().strip()
        sess_key = token_file.readline().strip()
        sig = token_file.readline().strip()
        token_id = token_file.readline().strip()
    return [app_key, sess_key, sig, token_id]


class GDUpload:
    def __init__(self, scopes, service_account_file, folder_id=''):   # folder_id твоя папка для сохранения в драйве
        self.scopes = scopes
        self.service_account_file = service_account_file
        self.folder_id = folder_id

    def upload(self, name, file_path):
        credentials = service_account.Credentials.from_service_account_file(
            self.service_account_file, scopes=self.scopes)
        service = build('drive', 'v3', credentials=credentials)
        file_metadata = {
            'name': name,
            'parents': [self.folder_id]
        }
        media = MediaFileUpload(file_path, resumable=True)
        service.files().create(body=file_metadata, media_body=media, fields='id,webViewLink').execute()


class PhotoVkLoader:
    VKAPI_BASE_URL = 'http://api.vk.com/method/'

    def __init__(self, tokens, version='5.131', gdupload=GDUpload(['https://www.googleapis.com/auth/drive'],
                                                                  token_gd)):
        self.token = tokens[0]
        self.id = tokens[1]
        self.version = version
        self.gdupload = gdupload

    @staticmethod
    def get_max_photo_size(size_dict):
        if size_dict['width'] >= size_dict['height']:
            return size_dict['width']
        else:
            return size_dict['height']

    def get_photos_from_vk(self, count=5, album_id='profile'):
        photos_get_url = urljoin(self.VKAPI_BASE_URL, 'photos.get')
        response = requests.get(photos_get_url, params={
            'access_token': f'{self.token}',
            'v': self.version,
            'owner_id': self.id,
            'album_id': album_id,
            'extended': 1,
            'count': count,
            'rev': 1,
            'photo_sizes': 1
        })
        all_photos = response.json()['response']['items']
        self.upload_photo_to_gd(all_photos)
        return all_photos

    def upload_photo_to_gd(self, photos):
        new_all_photo = []
        data_for_json = []
        title_list = []
        for photo in tqdm.tqdm(photos):
            name_file = photo['likes']['count']
            all_size = photo['sizes']
            date_photo = datetime.datetime.fromtimestamp(photo['date'])
            normal_date = date_photo.strftime('%Y%m%d')
            max_photo_url = max(all_size, key=self.get_max_photo_size)['url']
            max_size_type = max(all_size, key=self.get_max_photo_size)['type']
            title = str(name_file) + '.jpg'
            photo_dict = {
                'date': normal_date,
                'likes': name_file,
                'max_photo_url': max_photo_url,
                'max_type': max_size_type
            }
            if title in title_list:
                title += '_' + normal_date + '.jpg'
            title_list.append(title)
            download_photo = requests.get(max_photo_url)
            with open(title, 'wb') as f:
                f.write(download_photo.content)
            basename = os.path.basename(title)
            self.gdupload.upload(name=title, file_path=basename)
            new_all_photo.append(photo_dict)
            data_for_json.append({"file_name": title, "size": max_size_type})
            with open('Photo_from_vk.json', 'w') as f:
                json.dump(data_for_json, f, indent=2)
        return data_for_json


class OkLoader:
    def __init__(self, tokens, gdupload=GDUpload(['https://www.googleapis.com/auth/drive'],
                                                 token_gd)):
        self.app_key = tokens[0]
        self.sess_key = tokens[1]
        self.sig = tokens[2]
        self.fid = tokens[3]
        self.gdupload = gdupload

    def get_ok_photo(self):
        response = requests.get('https://api.ok.ru/fb.do', params={
            'application_key': self.app_key,
            'fid': self.fid,
            'format': 'json',
            'method': 'photos.getPhotos',
            'session_key': self.sess_key,
            'sig': self.sig
        })
        photos = response.json().get('photos')
        self.ulpoad_photo_to_gd(photos)
        return photos

    def ulpoad_photo_to_gd(self, photos):
        data_for_json = []
        for pic in tqdm.tqdm(photos):
            url = pic['pic640x480']
            name = pic['id'] + '.jpg'
            download_photo = requests.get(url)
            with open(name, 'wb') as f:
                f.write(download_photo.content)
            basename = os.path.basename(name)
            self.gdupload.upload(name=name, file_path=basename)
            data_for_json.append({"file_name": name, "size": '640x480'})
            with open('Photo_from_ok.json', 'w') as f:
                json.dump(data_for_json, f, indent=2)
        return data_for_json


if __name__ == '__main__':
    vkload = PhotoVkLoader(get_token_vk(token_vk))
    vkload.get_photos_from_vk()
    OkLoader = OkLoader(get_token_ok(token_ok))
    OkLoader.get_ok_photo()
