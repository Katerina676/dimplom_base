import requests
import json
import tqdm
import os

token_ok = 'tok_ok.txt'  # токен и id ок
token_ya = 'tok_ya.txt'  # токен яндекс диска


def get_token(file_name):
    with open(os.path.join(os.getcwd(), file_name), 'r') as token_file:
        app_key = token_file.readline().strip()
        sess_key = token_file.readline().strip()
        sig = token_file.readline().strip()
        token_id = token_file.readline().strip()
    return [app_key, sess_key, sig, token_id]


class YaUploader:
    def __init__(self, tokens):
        self.token = tokens[0]

    def get_headers(self):
        return {"Authorization": f'OAuth {self.token}'}

    def create_yadisk_folder(self):
        folder_name = 'Photo_from_OK'
        yandex_folder_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self.get_headers()
        params = {'path': folder_name}
        requests.put(yandex_folder_url, params=params, headers=headers)
        return folder_name

    def upload(self, file_path: str, file_name: str):
        url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = self.get_headers()
        folder_name = self.create_yadisk_folder()
        params = {"url": file_path, 'path': f'{folder_name}/{file_name}.jpg'}
        response_upload = requests.post(url, headers=headers, params=params)
        return print(response_upload.status_code)


class OkLoader:
    def __init__(self, tokens, uploader=YaUploader(get_token(token_ya))):
        self.app_key = tokens[0]
        self.sess_key = tokens[1]
        self.sig = tokens[2]
        self.fid = tokens[3]
        self.uploader = uploader

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
        self.ulpoad_photo_to_yd(photos)
        return photos

    def ulpoad_photo_to_yd(self, photos):
        data_for_json = []
        for pic in tqdm.tqdm(photos):
            url = pic['pic640x480']
            name = pic['id']
            self.uploader.upload(file_path=url, file_name=name)
            data_for_json.append({"file_name": f'{name}.jpg', "size": '640x480'})
            with open('Photo_from_ok.json', 'w') as f:
                json.dump(data_for_json, f, indent=2)
        return data_for_json


if __name__ == '__main__':
    OkLoader = OkLoader(get_token(token_ok))
    OkLoader.get_ok_photo()
