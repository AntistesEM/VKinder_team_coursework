<h5 align="right"><a href="./README.md">RU</h5> 

<div id="header" align="center">
  <img src="https://webmg.ru/wp-content/uploads/2022/11/4Nm6Pw35ux8.jpg" width="900"/>
</div>

<h1 align="center">Team project on the course "Professional work with Python"</h1>

## VKinder - a bot program for interacting with the database of the VK social network for dating in the form of a dialog with the user.

---

### Program Features

1. the bot independently determines the parameters of the user (age, gender, city, books, music, what groups he is a member of) who writes to him.
2. Using the received information about the user, the bot searches for other users of VKontakte for dating.
3. Outputs to the chat information about found users in the format:
```
- first name and last name,
- profile link,
- three most popular photos in the profile (popularity is determined by the number of likes).
```
4. Switching between found users is done with the help of a button or command.
5. Saving the user to the favorites list or to the black list with the help of a button or command (saving takes place in the database).
6. Viewing the favorite or blacklist by using the button or command.
7. Transferring a user from the Favourites List to the Black List and back using a button or command.
8. Deleting a user from the lists with a button or command.

------
  
### Installation Instructions

1. Make sure that your computer is configured to work with the PostgreSQL database. 
2. Create the database - **vkinder**.
3. Create a group in VKontakte, on behalf of which the bot will communicate. [Instruction](https://postium.ru/kak-sozdat-gruppu-v-kontakte/).
4. Get a token for VKontakte group. [Instructions](https://github.com/AntistesEM/VKinder_team_coursework/blob/main/task/group_settings.md).
5. Create application for chatbot and get access token. [Instructions](https://docs.google.com/document/d/1_xt16CMeaEir-tWLbUFyleZl6woEdJt-7eyva1coT3w/edit?usp=sharing).
6. In the file _settings.ini_ enter your data:
- access_token - user's access key
- key_group_access - community access key
- password - database password
   _and also if necessary change other parameters in the file._
7. Install the necessary packages from the file _requirements.txt_ using the command `pip install -r requirements.txt`.
8. Run the file **main.py** in any IDE.

------

### Instructions for interacting with the bot

- To start interacting with the bot, if there is no **"Начать"** button, send a message to the chat group **"Начать"**.
- To start the search, press the **"Поиск"** button. The bot will propose a user profile containing the user's first and last name, a link to the VK profile and three profile pictures, if any, with the most likes.
- With the **"Следующий"** button (**"Далее"**) the bot will suggest the next profile of the user.
- With the buttons **"В избранное"** and **"В черный список"** you can add the user to the corresponding list.
- With the **"Избранное**" and **"Черный список"** buttons you can view the corresponding list.
- With **"Переместить в избранное"** and **"Переместить в черный список"** you can move the user from one list to another.
- With the **"Удалить"** button you can delete the user from the list.
- With the **"Вернуться к поиску"** button you can continue viewing the found users.

------

### Project structure

* main.py - launches the bot
* bot.py - contains bot logic
* VKinder.py - contains the logic for requests to the VK API
* vkinder_db_models.py - contains database logic
* requirements.txt - contains list of packages necessary for Python-applications work
* settings.ini - contains necessary settings for Python-application work
* vkinder_db_scheme.png - DB scheme

------

### The project was worked on by

* [Andrey](https://github.com/Jamesmobile16) 
* [Dmitriy](https://github.com/dmitrykhay) 
* [Evgeniy](https://github.com/AntistesEM)




