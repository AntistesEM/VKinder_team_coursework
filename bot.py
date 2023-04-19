import configparser
from random import randrange

import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType

from VKinder import VKinder
from vkinder_db_models import Users, Parameters, session, Photos, UserPhoto


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
        self.event = None
        self.results = None
        self.vkinder_requests = None
        self.user_index = 0
        self.user_index_list = 0
        self.prev_event = ""
        self.main_domain = "https://vk.com/"
        self.request = ""
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
        self.results = self.vkinder_requests.get_users_info()
        message = f"Найдено {len(self.results)} пользователей\n"
        if self.request == "следующий":
            self.user_index += 1
            message = ""
            if self.user_index < 0 or self.user_index >= len(self.results):
                self.user_index = 0
        message += (
            f"\n{self.results[self.user_index]['first_name']}"
            f"\n{self.results[self.user_index]['last_name']}"
            f"\n{self.main_domain + 'id'}"
            f"{self.results[self.user_index]['link_user']}"
        )
        self.write_msg(
            user_id=self.event.user_id,
            message=message,
            attachment=','.join(self.results[self.user_index]["photos"]),
            keyboard=self.main.get_keyboard()
        )
        return self.user_index

    # логика кнопок "В избранное" и "В черный список"
    def add_favorites_or_blacklist(self, flag):
        user = Users(
            user_id=self.results[self.user_index]["link_user"],
            first_name=self.results[self.user_index]["first_name"],
            last_name=self.results[self.user_index]["last_name"],
            profile_link=f"{self.main_domain + 'id'}"
                         f"{self.results[self.user_index]['link_user']}",
            favorite=flag,
            block=not flag,
            parameter_id=self.results[self.user_index]["link_user"]
        )
        info_user = self.vkinder_requests.self_info(
            self.results[self.user_index]["link_user"]
        )
        sex = info_user['sex']
        if sex == 1:
            sex_text = "female"
        elif sex == 2:
            sex_text = "male"
        else:
            sex_text = "not specified"
        parameter = Parameters(
            parameter_id=self.results[self.user_index]["link_user"],
            city=info_user['city'],
            sex=sex_text,
            age=info_user['age'],
            books=info_user['books'],
            music=info_user['music'],
            groups=','.join(map(str, info_user['groups']))
        )
        session.add_all([user, parameter])
        session.commit()
        photos_list = self.vkinder_requests.get_photos(
            self.results[self.user_index]["link_user"]
        )
        for photo_ in photos_list:
            user_photo = UserPhoto(
                user_id=self.results[self.user_index]["link_user"],
                photo_id=photo_[2]
            )
            photo = Photos(
                photo_id=photo_[2],
                photo_link=photo_[1],
                likes=photo_[0]
            )
            session.add(user_photo)
            session.add(photo)
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
        user_photo = session.query(UserPhoto).filter_by(user_id=None).all()
        for photo in user_photo:
            session.delete(photo)
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
                self.vkinder_requests = VKinder(self.event.user_id)
                self.request = self.event.text.lower()
                if self.request == "начать":
                    self.start_search()
                elif self.request in ("поиск", "следующий", "новый поиск"):
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
