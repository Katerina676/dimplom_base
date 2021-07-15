from urllib.parse import urljoin
import datetime
import json
import tqdm
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
import requests
import os


class GDUpload:
    def __init__(self, scopes, service_account_file):
        self.scopes = scopes
        self.service_account_file = service_account_file

    def upload(self, name, file_path):
        credentials = service_account.Credentials.from_service_account_file(
            self.service_account_file, scopes=self.scopes)
        service = build('drive', 'v3', credentials=credentials)
        folder_id = ''
        file_metadata = {
            'name': name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, resumable=True)
        service.files().create(body=file_metadata, media_body=media, fields='id,webViewLink').execute()


class PhotoVkLoader:
    VKAPI_BASE_URL = 'http://api.vk.com/method/'
    V = '5.131'

    def __init__(self, token: str):
        self.token = token

    @staticmethod
    def get_max_photo_size(size_dict):
        if size_dict['width'] >= size_dict['height']:
            return size_dict['width']
        else:
            return size_dict['height']

    def get_photos_from_vk(self, user_id, count=5, album_id='profile'):
        photos_get_url = urljoin(self.VKAPI_BASE_URL, 'photos.get')
        response = requests.get(photos_get_url, params={
            'access_token': f'{self.token}',
            'v': self.V,
            'owner_id': user_id,
            'album_id': album_id,
            'extended': 1,
            'count': count,
            'rev': 1,
            'photo_sizes': 1
        })
        all_photos = response.json()['response']['items']
        self.upload_photo_to_yd(all_photos)
        return all_photos

    def upload_photo_to_yd(self, photos):
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
            temp_dict = {
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
            gdupload = GDUpload(['https://www.googleapis.com/auth/drive'],
                                '')
            gdupload.upload(name=title, file_path=basename)
            new_all_photo.append(temp_dict)
            data_for_json.append({"file_name": title, "size": max_size_type})
            with open('Photo_from_vk.json', 'w') as f:
                json.dump(data_for_json, f, indent=2)
        return data_for_json


class OkLoader:
    def __init__(self, app_key: str, sess_key: str, sig: str):
        self.app_key = app_key
        self.sess_key = sess_key
        self.sig = sig

    def get_ok_photo(self, fid):
        response = requests.get('https://api.ok.ru/fb.do', params={
            'application_key': self.app_key,
            'fid': fid,
            'format': 'json',
            'method': 'photos.getPhotos',
            'session_key': self.sess_key,
            'sig': self.sig
        })
        photos = response.json().get('photos')
        self.ulpoad_photo_to_yd(photos)
        return photos

    def ulpoad_photo_to_yd(self, photos):
        data_for_json = []
        for pic in tqdm.tqdm(photos):
            url = pic['pic640x480']
            name = pic['id'] + '.jpg'
            download_photo = requests.get(url)
            with open(name, 'wb') as f:
                f.write(download_photo.content)
            basename = os.path.basename(name)
            gdupload = GDUpload(['https://www.googleapis.com/auth/drive'],
                                '')
            gdupload.upload(name=name, file_path=basename)
            data_for_json.append({"file_name": name, "size": '640x480'})
            with open('Photo_from_ok.json', 'w') as f:
                json.dump(data_for_json, f, indent=2)
        return data_for_json


if __name__ == '__main__':
    vkload = PhotoVkLoader()
    vkload.get_photos_from_vk()
    OkLoader = OkLoader()
    OkLoader.get_ok_photo()
