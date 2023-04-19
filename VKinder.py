import configparser
import re
import time
from datetime import datetime

import requests

config = configparser.ConfigParser()
config.read("settings.ini")


class VKinder:

    def __init__(self, user_id: str, version='5.131'):
        self.token = config["VK"]["access_token"]
        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    # Функция собирает информацию о текущем пользователе и возвращает
    # словарь с данными.
    def self_info(self, id_user=None) -> dict:
        url = 'https://api.vk.com/method/users.get'
        params = {'user_ids': id_user}
        fields = {'fields': 'bdate, city, sex, music, books'}
        response = requests.get(
            url,
            params={**self.params, **params, **fields}
        ).json()
        self_info = {}
        bdate = response['response'][0]['bdate']
        bdate = bdate.split(sep='.')
        self_year = int(bdate[2])
        current_year = datetime.now().date().year
        self_age = current_year - self_year
        self_info['age'] = self_age
        self_info['city'] = response['response'][0]['city']['id']
        self_info['sex'] = response['response'][0]['sex']
        self_info['books'] = response['response'][0]['books']
        self_info['music'] = response['response'][0]['music']
        self_info['groups'] = self.groups_get(self.id)['response']['items']
        return self_info

    # Функция получает список групп пользователя и возвращает словарь.
    def groups_get(self, user_id) -> list:
        url = 'https://api.vk.com/method/groups.get'
        params = {'user_id': user_id, 'count': 1000}
        response = requests.get(url, params={**self.params, **params}).json()
        if 'response' not in response:
            pass
        else:
            return response

    def users_search(self):
        #Функция запрашивает пользователей VK (х1000), далее фильтрует их, сравнивая с текущим пользователем.
        #В category1_search попадают пользователи, подожедшие по базовым критериям (город, пол, возварст)
        #В category2_search попадают пользователи после первой фильтрации, у которых есть одинаковые группы.
        #В category3_search попадают пользователи после второй фильтрации, у которых есть совпадения либо по
        #общим книгам, либо по музыке. Функция возвращает список пользователей со всеми данными, либо после 3ей фильтрации,
        # либо, если таких не найдено, после предыдущей.
        self_info = self.self_info(self.id)
        self_age = self_info['age']
        self_city = self_info['city']
        self_sex = self_info['sex']
        self_music = self_info['music']
        self_music = ''.join(self_music.split()).lower().split(',')
        self_books = self_info['books']
        self_books = ''.join(self_books.split()).lower().split(',')
        category1_search = {}
        category2_search = {}
        url = 'https://api.vk.com/method/users.search'
        fields_ = {
            'count': 1000,
            'sex': 1 if self_sex == 2 else 2,
            'city_id': self_city,
            'has_photo': 1,
            'age_from': self_age - 5,
            'age_to': self_age + 5,
            'fields': 'bdate, city, sex, music, books',
            'group_id': self.groups_get(self.id)['response']['items']
        }
        response = requests.get(url, params={**self.params, **fields_}).json()
        time.sleep(0.33)
        for user in response['response']['items']:
            category1_search[user['id']] = user
        for user1 in category1_search.values():
            if 'music' in user1.keys():
                user1_music = user1['music']
                user1_music = ''.join(user1_music.split()).lower().split(',')
                for pattern in user1_music:
                    for music in self_music:
                        match = re.search(pattern, music)
                        if match is None:
                            pass
                        elif match.group(0) in user1_music:
                            category2_search[user1['id']] = user1
                        else:
                            pass
            else:
                pass
        for user2 in category1_search.values():
            if 'books' in user2.keys():
                user2_books = user2['books']
                user2_books = ''.join(user2_books.split()).lower().split(',')
                for pattern1 in user2_books:
                    for book in self_books:
                        match1 = re.search(pattern1, book)
                        if match1 is None:
                            pass
                        elif match1.group(0) in user2_books:
                            category2_search[user2['id']] = user2
                        else:
                            pass
            else:
                pass
        if len(category2_search) != 0:
            return category2_search
        elif len(category1_search) != 0:
            return category1_search

    # Функция возвращает фото с профиля пользователя в максимальном разрешении.
    def get_photos(self, self_id) -> list[tuple[int, str, int]]:
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': self_id,
                  'album_id': 'profile',
                  'extended': '1',
                  'photo_sizes': '0',
                  'count': 1000
        }
        response = requests.get(url, params={**self.params, **params}).json()
        time.sleep(0.33)
        photo_list = response['response']['items']
        photo_to_upload = []
        for photo_info in photo_list:
            for dimension in photo_info['sizes']:
                b = {}
                b.update(dimension)
                if dimension['height'] > b['height']:
                    b.update(dimension)
                else:
                    pass
                b.update(photo_info['likes'])
                b['id'] = photo_info['id']
                b['date'] = photo_info['date']
            a = (b['count'], b['url'], b['id'])
            photo_to_upload.append(a)
        photo_to_upload.sort(reverse=1)
        n = 3
        photos_list = [x for index, x in enumerate(photo_to_upload) if index < n]
        return photos_list

    # Функция возвращает нужные данные найденных ранее пользоватедей
    # (Имя, ссылку, фото х3)
    def get_users_info(self) -> list[dict[str, any]]:
        users_info = []
        ids = self.users_search()
        for user_id in ids.values():
            user_info = {}
            photo_list = self.get_photos(user_id['id'])
            photo_url_list = []
            for photo in photo_list:
                photo_url_list.append(f"photo{user_id['id']}_{photo[2]}")
            user_info['photos'] = photo_url_list
            user_info['first_name'] = user_id['first_name']
            user_info['last_name'] = user_id['last_name']
            user_info['link_user'] = user_id['id']
            users_info.append(user_info)
        return users_info


if __name__ =='__main__':
    pass
