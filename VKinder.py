import requests
import time
from pprint import pprint
import re

from credentials import token
from credentials import vk_id


class VKinder:

    def __init__(self, token, user_id, version='5.131'):
        self.token = token
        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def self_info(self): #Функция собирает информацию о текущем пользователе и возвращает словарь с данными.
        url = 'https://api.vk.com/method/users.get'
        params = {'user_ids': self.id}
        fields = {'fields': 'bdate, city, sex, music, books'}
        response = requests.get(url, params={**self.params, **params, **fields}).json()
        self_info = {}
        year = self.get_birthday_year(response['response'][0]['bdate'])
        self_info['year'] = year
        self_info['city'] = response['response'][0]['city']['title']
        self_info['sex'] = response['response'][0]['sex']
        self_info['books'] = response['response'][0]['books']
        self_info['music'] = response['response'][0]['music']
        self_info['groups'] = self.groups_get(self.id)['response']['items']
        return self_info

    def get_birthday_year(self, bdate: str): #Функция обрабатывает полученную дату рождения пользователя и возвращает только год.
        reg = re.match(r'([0-9]{1,2})\.([0-9]{1,2})\.([0-9]{4})', bdate)
        if reg != None:
            year = reg.group(3)
        else:
            year = 0
        return year

    def groups_get(self, user_id): #Функция получает список групп пользователя и возвращает словарь.
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
        url = 'https://api.vk.com/method/users.search'
        fields = {'count': 1000, 'fields': 'bdate, city, sex, music, books'}
        response = requests.get(url, params={**self.params, **fields}).json()
        self_info = self.self_info()
        self_year = self_info['year']
        self_city = self_info['city']
        self_sex = self_info['sex']
        self_groups = self_info['groups']
        self_music = self_info['music']
        self_music = ''.join(self_music.split()).lower().split(',')
        self_books = self_info['books']
        self_books = ''.join(self_books.split()).lower().split(',')
        category1_search = {}
        category2_search = {}
        category3_search = {}
        for user in response['response']['items']:
            if 'bdate' not in user.keys():
                pass
            elif 'city' not in user.keys():
                pass
            else:
                user_year = self.get_birthday_year(user['bdate'])
                if user_year == self_year\
                    and user['city']['title'] == self_city\
                    and user['sex'] != self_sex:
                    category1_search[user['id']] = user
        for user1 in category1_search.values():
            user1_groups = self.groups_get(user1['id'])
            time.sleep(0.3)
            if user1_groups != None:
                for group in self_groups:
                    if group in user1_groups['response']['items']:
                        category2_search[user1['id']] = user1
        for user2 in category2_search.values():
            if 'music' in user2.keys():
                user2_music = user2['music']
                user2_music = ''.join(user2_music.split()).lower().split(',')
                for pattern in user2_music:
                    for music in self_music:
                        match = re.search(pattern, music)
                        if match == None:
                            pass
                        elif match.group(0) in user2_music:
                            category3_search[user2['id']] = user2
                        else:
                            pass
            else:
                pass
        for user3 in category2_search.values():
            if 'books' in user3.keys():
                user3_books = user3['books']
                user3_books = ''.join(user3_books.split()).lower().split(',')
                for pattern1 in user3_books:
                    for book in self_books:
                        match1 = re.search(pattern1, book)
                        if match1 == None:
                            pass
                        elif match1.group(0) in user3_books:
                            category3_search[user3['id']] = user3
                        else:
                            pass
            else:
                pass
        if len(category3_search) != 0:
            return category3_search
        elif len(category2_search) != 0:
            return category2_search
        elif len(category1_search) != 0:
            return category1_search

    def get_photos(self, self_id): #Функция возвращает фото с профиля пользователя в максимальном разрешении.
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': self_id,
                  'album_id': 'profile',
                  'extended': '1',
                  'photo_sizes': '0',
                  'count': 3}
        response = requests.get(url, params={**self.params, **params}).json()
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
                b['date'] = photo_info['date']
            photo_to_upload.append(b)

        return photo_to_upload

    def get_users_info(self): #Функция возвращает нужные данные найденных ранее пользоватедей (Имя, ссылку, фото х3)
        users_info = []
        ids = self.users_search()
        for user_id in ids.values():
            user_info = {}
            photo_list = self.get_photos(user_id['id'])
            photo_url_list = []
            for photo in photo_list:
                photo_url_list.append(photo['url'])
            user_info['photos'] = photo_url_list
            user_info['first_name'] = user_id['first_name']
            user_info['last_name'] = user_id['last_name']
            user_info['link'] = f"vk.com/{user_id['id']}"
            users_info.append(user_info)
        return users_info


if __name__ =='__main__':

    vkinder = VKinder(token, vk_id)
    vkinder.get_users_info()

    # pprint(vkinder.self_info())
    # pprint(vkinder.users_search())
    # print(vkinder.groups_get())
    # pprint(vkinder.get_photos())
    # pprint(vkinder.get_users_info())

