import requests
from urllib.parse import urljoin
import datetime
import json
import tqdm


class YaUploader:
    def __init__(self, token: str):
        self.token = token

    def get_headers(self):
        return {"Authorization": f'OAuth {self.token}'}

    def create_yadisk_folder(self):
        folder_name = 'Photo_from_VK'
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
            title = str(name_file)
            temp_dict = {
                'date': normal_date,
                'likes': name_file,
                'max_photo_url': max_photo_url,
                'max_type': max_size_type
            }
            if title in title_list:
                title += '_' + normal_date
            title_list.append(title)
            uploader = YaUploader()
            uploader.upload(file_path=max_photo_url, file_name=title)
            new_all_photo.append(temp_dict)
            data_for_json.append({"file_name": f'{title}.jpg', "size": max_size_type})
            with open('Photo_from_vk.json', 'w') as f:
                json.dump(data_for_json, f, indent=2)
        return data_for_json


if __name__ == '__main__':
    vkload = PhotoVkLoader()
    vkload.get_photos_from_vk('552934290')
