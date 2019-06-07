import requests
import redis
import os
import json
from time import sleep

# BOT
class Bot:

    def __init__(self, token):
        self.token = token
        self.MAIN_URL = f'https://api.telegram.org/bot{token}/'
        self.participants = []
        self.tasks = []
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
    def join(self):
        chat_id = self.get_last_update()['message']['chat']['id']
        allias = self.get_last_update()['message']['from']['username']
        if allias in self.participants:
            self.send_message(chat_id, 'You are already joined!')
        else:
            self.participants.append(allias)
            self.send_message(chat_id, allias)

    # add new task
    def add_task(self):
        chat_id = self.get_last_update()['message']['chat']['id']
        task = self.get_last_update()['message']['text'].split(' ', 1)

        if len(task) > 1 and task[1] not in self.tasks:
            self.tasks.append(task[1])
            self.send_message(chat_id, task[1])
        elif len(task) > 1 and task[1] in self.tasks:
            self.send_message(chat_id, 'There is already such task!')
        else:
            self.send_message(chat_id, 'You should specify task!')

    # show all tasks
    def show_tasks(self):
        chat_id = self.get_last_update()['message']['chat']['id']
        msg = ''

        for i, task in enumerate(self.tasks):
            msg = msg + str(i + 1) + ': ' + self.tasks[i] + '\n'

        if len(self.tasks) == 0:
            self.send_message(chat_id, 'There are no tasks! Add tasks!')
        else:
            self.send_message(chat_id, msg)



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
