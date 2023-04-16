import configparser
from datetime import date, datetime
from random import randrange

import requests
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType

from vkinder_db import Users, Parameters, session


# получаем из файла "settings.ini" токен для сообщества и пользовательский
def get_tokens():
    config = configparser.ConfigParser()
    config.read("settings.ini")
    key_group_access = config["VK"]["key_group_access"]
    access_token = config["VK"]["access_token"]
    return {"group_token": key_group_access, "user_token": access_token}


vk = vk_api.VkApi(token=get_tokens()["group_token"])
session_api = vk.get_api()
long_poll = VkLongPoll(vk)


class VkBot:
    def __init__(self):
        self.offset = 0
        self.user_index = 0
        self.user_index_list = 0
        self.prev_event = ""
        self.main_domain = "https://vk.com/"
        self.request = ""
        self.results = []
        self.event = ""
        (
            self.start,
            self.main,
            self.favorites,
            self.blacklist,
            self.stop,
            self.del_k
        ) = self.create_keyboard()

    # Создание клавиатур
    @staticmethod
    def create_keyboard():
        keyboard_start = VkKeyboard(inline=True)
        keyboard_start.add_button("Поиск", color=VkKeyboardColor.PRIMARY)

        keyboard_main = VkKeyboard(one_time=True)
        keyboard_main.add_button("Следующий", color=VkKeyboardColor.PRIMARY)
        keyboard_main.add_line()
        keyboard_main.add_button("В избранное", color=VkKeyboardColor.POSITIVE)
        keyboard_main.add_button("В черный список", color=VkKeyboardColor.NEGATIVE)
        keyboard_main.add_line()
        keyboard_main.add_button("Избранное", color=VkKeyboardColor.SECONDARY)
        keyboard_main.add_button("Черный список", color=VkKeyboardColor.SECONDARY)
        keyboard_main.add_line()
        keyboard_main.add_button("Новый поиск", color=VkKeyboardColor.SECONDARY)

        keyboard_favorites = VkKeyboard(one_time=True)
        keyboard_favorites.add_button("Далее", color=VkKeyboardColor.PRIMARY)
        keyboard_favorites.add_line()
        keyboard_favorites.add_button(
            "Переместить в черный список", color=VkKeyboardColor.NEGATIVE
        )
        keyboard_favorites.add_line()
        keyboard_favorites.add_button(
            "Вернуться к поиску", color=VkKeyboardColor.PRIMARY
        )

        keyboard_blacklist = VkKeyboard(one_time=True)
        keyboard_blacklist.add_button("Далее", color=VkKeyboardColor.PRIMARY)
        keyboard_blacklist.add_line()
        keyboard_blacklist.add_button(
            "Переместить в избранное", color=VkKeyboardColor.POSITIVE
        )
        keyboard_blacklist.add_line()
        keyboard_blacklist.add_button(
            "Вернуться к поиску", color=VkKeyboardColor.PRIMARY
        )

        keyboard_stop = VkKeyboard().get_empty_keyboard()

        keyboard_del = VkKeyboard(inline=True)
        keyboard_del.add_button("Удалить", color=VkKeyboardColor.NEGATIVE)

        return (
            keyboard_start,
            keyboard_main,
            keyboard_favorites,
            keyboard_blacklist,
            keyboard_stop,
            keyboard_del
        )

    # отправка сообщения
    @staticmethod
    def write_msg(user_id, message=None, attachment=None, keyboard=None):
        parameters = {
            "user_id": user_id,
            "message": message,
            "attachment": attachment,
            "keyboard": keyboard,
            "random_id": randrange(10**7)
        }
        vk.method("messages.send", parameters)

    # получаем данные о пользователе ботом метод -- users.get
    def get_info_user(self):
        info = session_api.users.get(
            user_ids=self.event.user_id,
            fields=("bdate", "sex", "city", "domain", "country"),
        )
        age = self.calculate_age(info[0]["bdate"])
        sex = info[0]["sex"]
        country = info[0]["country"]["id"]
        city = info[0]["city"]["title"]
        region = "??????????"  # как его найти?
        return {
            "age": age,
            "sex": sex,
            "city": city,
            "country": country,
            "region": region
        }

    # ищем пользователей по параметрам, метод -- users.search
    def get_info_user_params(self):
        url = "https://api.vk.com/method/users.search"
        params = {
            "user_ids": self.event.user_id,
            "access_token": get_tokens()["user_token"],
            "v": "5.131",
            "count": 1000,
            "offset": self.offset,
            "country": self.get_info_user()["country"],
            "hometown": self.get_info_user()["city"],
            "sex": self.get_info_user()["sex"],
            "fields": "domain,photo_id,country,city,sex,bdate",
            "age_from": self.get_info_user()["age"] - 5,
            "age_to": self.get_info_user()["age"] + 5,
            "has_photo": True
        }
        response = requests.get(
            url,
            params={**params}
        ).json()["response"]["items"]
        return response

    # вычисляем возраст по дате рождения
    @staticmethod
    def calculate_age(born: str) -> int:
        born = datetime.strptime(born, "%d.%m.%Y").date()
        today = date.today()
        return (
            today.year - born.year - (
                (today.month, today.day) < (born.month, born.day)
            )
        )

    # логика сообщения "НАЧАТЬ"
    def start_search(self):
        message = (
            "Привет! Я твой помощник Кузя. "
            '\nЧтобы начать поиск людей нажми кнопку "Поиск"'
        )
        self.write_msg(
            user_id=self.event.user_id,
            message=message,
            keyboard=self.start.get_keyboard()
        )

    # логика для кнопки "ПОИСК" и "СЛЕДУЮЩИЙ"
    def search(self):
        message = f"Найдено {len(self.results)} пользователей\n"
        if self.request == "следующий":
            self.user_index += 1
            message = ""
            if self.user_index < 0 or self.user_index >= len(self.results):
                self.user_index = 0
        message += (
            f"\n{self.results[self.user_index]['first_name']}"
            f"\n{self.results[self.user_index]['last_name']}"
            f"\n{self.main_domain + self.results[self.user_index]['domain']}"
        )
        self.write_msg(
            user_id=self.event.user_id,
            message=message,
            attachment="photo" + self.results[self.user_index]["photo_id"],    # !!! изменить на вывод 3х фото !!!!
            keyboard=self.main.get_keyboard()
        )
        return self.user_index

    # логика кнопок "В избранное" и "В черный список"
    def add_favorites_or_blacklist(self, flag):
        user = Users(
            user_id=self.results[self.user_index]["id"],
            first_name=self.results[self.user_index]["first_name"],
            last_name=self.results[self.user_index]["last_name"],
            profile_link=self.main_domain +
                         self.results[self.user_index]["domain"],
            favorite=flag,
            block=not flag,
            parameter_id=self.results[self.user_index]["id"]
        )
        sex = self.results[self.user_index]["sex"]
        if sex == 1:
            sex_text = "female"
        elif sex == 2:
            sex_text = "male"
        else:
            sex_text = "not specified"
        parameter = Parameters(
            parameter_id=self.results[self.user_index]["id"],
            country=self.results[self.user_index]["country"]["title"],
            region="Moscow",
            city=self.results[self.user_index]["city"]["title"],
            sex=sex_text,
            age_from=self.get_info_user()["age"] - 5,
            age_to=self.get_info_user()["age"] + 5
        )
        # user_photo = UserPhoto(                                       # реализовать UserPhoto
        #     user_id=self.results[self.user_index]["id"],
        #     photo_id=self.results[self.user_index]["photo_id"]
        # )
        # for photo in photos:                                          # реализовать photos
        #     photo = Photos(photo_id='1', photo_link='222', likes=89)

        session.add_all([user, parameter])
        session.commit()
        if flag:
            message = f"Пользователь " \
                      f"{self.results[self.user_index]['last_name']} " \
                      f"добавлен в избранные"
        else:
            message = f"Пользователь " \
                      f"{self.results[self.user_index]['last_name']} " \
                      f"добавлен в черный список"
        self.write_msg(
            user_id=self.event.user_id,
            message=message,
            keyboard=self.main.get_keyboard()
        )

    # логика кнопок просмотра избранных и черного списка
    def look_favorites_or_blacklist(self, flag):
        if flag == "favorite":
            filter_ = Users.favorite == "true"
            keyboard_name = self.favorites.get_keyboard()
        elif flag == "blacklist":
            filter_ = Users.block == "true"
            keyboard_name = self.blacklist.get_keyboard()
        users_list = session.query(Users).filter(filter_).all()
        if users_list:
            message = f"Найдено {len(users_list)} пользователей\n"
            if self.request == "далее":
                self.user_index_list += 1
                message = ""
                if self.user_index_list < 0 \
                        or self.user_index_list >= len(users_list):
                    self.user_index_list = 0
            message += (
                f"\n{users_list[self.user_index_list].first_name}"
                f"\n{users_list[self.user_index_list].last_name}"
                f"\n{users_list[self.user_index_list].profile_link}"
            )
        else:
            message = "Вы еще никого не добавили"
            keyboard_name = self.main.get_keyboard()
        self.write_msg(
            user_id=self.event.user_id,
            message=message,
            keyboard=keyboard_name
        )
        if users_list:
            self.write_msg(
                user_id=self.event.user_id,
                message="-----------------",
                keyboard=self.del_k.get_keyboard()
            )
        return (
            self.user_index_list,
            users_list[self.user_index_list].user_id if users_list else None
        )

    # логика кнопки "Удалить"
    def del_from_list(self, user_id):
        if self.prev_event == "избранное":
            keyboard_name = self.favorites.get_keyboard()
        elif self.prev_event == "черный список":
            keyboard_name = self.blacklist.get_keyboard()
        users = session.query(Users).filter_by(user_id=user_id).first()
        session.delete(users)
        session.commit()
        self.write_msg(
            user_id=self.event.user_id,
            message="Пользователь удален",
            keyboard=keyboard_name
        )

    # логика кнопок "Переместить ..."
    def moving(self, user_id):
        users = session.query(Users).filter_by(user_id=user_id).first()
        if self.request == "переместить в черный список":
            users.block = True
            users.favorite = False
            keyboard_name = self.favorites.get_keyboard()
        elif self.request == "переместить в избранное":
            users.block = False
            users.favorite = True
            keyboard_name = self.blacklist.get_keyboard()
        session.commit()
        message = f"Пользователь перемещен {' '.join(self.request.split()[1:])}"
        self.write_msg(
            user_id=self.event.user_id,
            message=message,
            keyboard=keyboard_name
        )

    # логика кнопки "ВЕРНУТЬСЯ К ПОИСКУ"
    def return_to_search(self):
        message = "Выберите действие"
        self.write_msg(
            user_id=self.event.user_id,
            message=message,
            keyboard=self.main.get_keyboard()
        )

    # Обработка сообщений
    def handle_message(self):
        for self.event in long_poll.listen():
            if self.event.type == VkEventType.MESSAGE_NEW and self.event.to_me:
                self.request = self.event.text.lower()
                if self.request == "начать":
                    self.start_search()
                elif self.request in ("поиск", "следующий"):
                    self.results = self.get_info_user_params()
                    self.user_index = self.search()
                elif self.request == "в избранное":
                    flag = True
                    self.add_favorites_or_blacklist(flag)
                elif self.request == "в черный список":
                    flag = False
                    self.add_favorites_or_blacklist(flag)
                elif self.request in ("избранное", "черный список"):
                    self.prev_event = self.request
                    if self.request == "избранное":
                        flag = "favorite"
                    elif self.request == "черный список":
                        flag = "blacklist"
                    self.user_index_list, user_id = \
                        self.look_favorites_or_blacklist(flag)
                elif self.request == "далее":
                    self.user_index_list, user_id = \
                        self.look_favorites_or_blacklist(flag)
                elif self.request == "новый поиск":  # нужно реализовать, вызывает ошибку
                    self.offset += 1000
                    self.results = self.get_info_user_params()
                    # реализовать логику поиск следующих 1000 пользователей или по другим параметрам?
                    message = f"Найдено {len(self.results)} пользователей\n"
                    message += (
                        f"{self.results[self.user_index]['first_name']}"
                        f"\n{self.results[self.user_index]['last_name']}"
                        f"\n{self.main_domain + self.results[self.user_index]['domain']}"
                    )
                    self.write_msg(
                        user_id=self.event.user_id,
                        message=message,
                        attachment="photo" + self.results[self.user_index]["photo_id"],
                        keyboard=self.main.get_keyboard(),
                    )
                elif self.request == "вернуться к поиску":
                    self.return_to_search()
                elif self.request == "удалить":
                    self.del_from_list(user_id)
                elif self.request in (
                    "переместить в черный список",
                    "переместить в избранное"
                ):
                    self.moving(user_id)
                elif self.request == "пока":
                    message = "Всего хорошего!"
                    self.write_msg(
                        user_id=self.event.user_id,
                        message=message,
                        keyboard=self.stop
                    )
                else:
                    message = "Я не понимаю Вас."
                    self.write_msg(
                        user_id=self.event.user_id,
                        message=message,
                        keyboard=self.main.get_keyboard(),
                    )


if __name__ == "__main__":
    vk_bot = VkBot()
    vk_bot.handle_message()
