import requests
import redis
import os
import json
from time import sleep


# # TODO:

"""

1) Мне нужно проверить, что человек присоединился, чтобы отправлять другие команды
2) Нужно разобраться с тем как будет учитываться статистика выполнения заданий
3) Понять как определять очередь для жителей комнаты
4) Нужно сделать уведомления о том, чья очередь выполнять задание
5) Нормально выводить все команды (по красивше ты шо лиса)
6) Айнура жепа

"""



# BOT
class Bot:

    def __init__(self, token):
        self.token = token
        self.MAIN_URL = f'https://api.telegram.org/bot{token}/'
        self.client = redis.Redis(host = '192.168.100.8', port = 6379)


    # Get updates from API
    def get_updates(self, offset = None, timeout = 30):
        params = {'timeout': timeout, 'offset': offset}
        responce = requests.get(self.MAIN_URL + 'getUpdates', params)
        result_json = responce.json()['result']
        return result_json

    # send message to the chat
    def send_message(self, chat_id, text):
        params = {'chat_id': chat_id, 'text':text}
        response = requests.post(self.MAIN_URL + 'sendMessage', params)
        return response


    def get_last_update(self):

        result = self.get_updates()

        if len(result) > 0:
            last_update = result[-1]
        else:
            last_update = result[len(result)]

        return last_update

    # function that will called in the very beginning
    def start(self):
        msg = "Welcome to Div&Do bot, here you can track whose is it turn to do particular task!"
        self.send_message(self.get_last_update()['message']['chat']['id'], msg)

    # function that will join the user to the participants
    #TODO:
    # Нужно реализовать хранение информации в редис
    # решить как хранить юзеров когда они присоединяться
    def join(self):
        chat_id = self.get_last_update()['message']['chat']['id']
        allias = self.get_last_update()['message']['from']['username']
        user_id = self.get_last_update()['message']['from']['id']

        if self.client.hexists(chat_id, allias):
            self.send_message(chat_id, 'You are already joined!')
        else:
            # setting statistics for tasks
            # TODO: when we add new task we need update list of tasks for every user
            set = self.client.smembers('tasks' + str(chat_id))

            while len(set) != 0:
                task_pair = set.pop()
                # adding task and number of times it was done by user in the hash table
                self.client.hset(allias+str(chat_id), task_pair, 0)

            # PREV VERSION:
            # self.client.hset(chat_id, allias, user_id)
            # self.send_message(chat_id, self.client.hget(chat_id, allias))

            # NEW VERSION
            # adding user to the 'list' of joined users
            self.client.hset(chat_id, allias, allias+str(chat_id))
            self.send_message(chat_id, self.client.hget(chat_id, allias))

    # function that checks if user is joined
    def is_join(self, chat_id, allias):

        if self.client.hexists(chat_id, allias):
            return True
        else:
            return False

    # add new task
    def add_task(self):
        chat_id = self.get_last_update()['message']['chat']['id']
        allias = self.get_last_update()['message']['from']['username']
        task = self.get_last_update()['message']['text'].split(' ', 1)

        # user can use other commands only when he(she and other great genders also should be joined) is joined
        if self.is_join(chat_id, allias):

            if len(task) > 1 and not self.client.sismember('tasks' + str(chat_id), task[1]):
                # GOVNO CODE MODE: ON
                self.client.sadd('tasks' + str(chat_id), task[1])

                # adding new task and its counter
                # 1st arg - name of hash, 2nd arg - task, 3rd - counter
                # self.client.hset(allias+str(chat_id), task[1], 0)

                usernames = self.client.hgetall(chat_id)        # hash that contains all usernames and titles of list with tasks

                for i in usernames:
                    self.client.hset(usernames[i], task[1], 0)

                # debug god
                self.send_message(chat_id, self.client.hexists(allias+str(chat_id), task[1]))
            elif len(task) > 1 and self.client.sismember('tasks' + str(chat_id), task[1]):
                self.send_message(chat_id, 'There is already such task!')
            else:
                self.send_message(chat_id, 'You should specify task!')
        else:
            self.send_message(chat_id, 'You should joined to use commands. Use /join to use other commands')

    # show all tasks
    def show_tasks(self):
        chat_id = self.get_last_update()['message']['chat']['id']
        allias = self.get_last_update()['message']['from']['username']

        if self.is_join(chat_id, allias):

            hash = self.client. hgetall(allias + str(chat_id))
            msg = 'Tasks statistics of @{}: \n'.format(allias)

            if self.client.scard('tasks' + str(chat_id)) == 0:
                self.send_message(chat_id, 'There are no tasks! Add tasks!')
            else:
                for i in hash:
                    msg = msg + i.decode('utf-8') + ': ' + hash[i].decode('utf-8') + '\n'

                self.send_message(chat_id, msg)
        else:
            self.send_message(chat_id, 'You should joined to use commands. Use /join to use other commands')

def main():
    token = '878358054:AAEyKwwvCuXgd6AyTP5VgXyQSBjd9o51EXA'
    my_bot = Bot(token)

    with open('updates.json', 'w') as write_file:
        json.dump(my_bot.get_updates(), write_file)

    last_update = my_bot.get_last_update()
    last_update_id = last_update['update_id']

    while True:
        upd = my_bot.get_last_update()
        upd_command = upd['message']['text']
        if last_update_id == upd['update_id']:
            if upd_command == '/start':
                my_bot.start()
                last_update_id+=1
            elif upd_command == '/join':
                my_bot.join()
                last_update_id+=1
            elif '/addtask' in upd_command:
                my_bot.add_task()
                last_update_id+=1
            elif upd_command == '/showtasks':
                my_bot.show_tasks()
                last_update_id+=1

if __name__ == '__main__':
    main()
