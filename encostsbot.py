
import encosts_private

import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, InlineQueryHandler,ConversationHandler, Filters
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler

import requests
import json
from os import path
import logging
from datetime import datetime, date, time
from time import sleep,ctime
import random


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)


#Состояния бота
CHOOSE_MAIN_ACTION, TASKS_MENU, HELP_MENU, STATE_4, STATE_5, STATE_7 = range(6)

#Переменные


#Текстовые переменные
WELCOME_HI_TEXT = ["Это ЭнкостБот."]
WELCOME_DESCRIPTION_TEXT = ["Я буду помогать тебе в работе."]


#Смайлики
fingerup = u'\U0000261D'
nerdface = u'\U0001F913'

#Авторизация в AMOCRM
def amo_auth():
	session = requests.Session()
	auth_resp = session.post('https://%s.amocrm.ru/private/api/auth.php?type=json' % encosts_private.amo_domain, data = json.dumps({'USER_LOGIN':'%s' % encosts_private.amo_apiuser,'USER_HASH':'%s' % encosts_private.amo_apiuserhash}))
	return auth_resp

#Получение массива задач для конкретного username
def get_tasks(username):
	session = requests.Session()	
	user_tasks = session.get('https://{0}.amocrm.ru/api/v2/tasks?responsible_user_id%5B%5D={1}'.format(encosts_private.amo_domain, encosts_private.accounts_amo[username]['user_id']), cookies=amo_auth().cookies)
	
	json_resp = json.loads(user_tasks.text)
	return json_resp['_embedded']['items']
	

#Команда /start
def start(bot, update):
	bot.send_message(chat_id=update.message.chat_id, text="Привет, %s!" % (encosts_private.accounts_tg[update.message.chat.username]))
	bot.send_message(chat_id=update.message.chat_id, text=random.choice(WELCOME_HI_TEXT))
	sleep(0.5)
	bot.send_message(chat_id=update.message.chat_id, text=random.choice(WELCOME_DESCRIPTION_TEXT))
	sleep(1)

	main_keyboard(bot,update)
	
	return CHOOSE_MAIN_ACTION
#Клавиатура главного меню InlineKeyboard
def main_keyboard(bot, update):

	keyboard = [[InlineKeyboardButton("Мои задачи",callback_data='11')],
				[InlineKeyboardButton("Посмотреть функции",callback_data='12')]]
	reply_markup = InlineKeyboardMarkup(keyboard)

	if update.message != None:
		chat_id = update.message.chat_id
		bot.send_message(chat_id=chat_id, text='Выберите действие', reply_markup=reply_markup)
		username = update.message.chat.username
	elif update.callback_query.message != None:
		chat_id = update.callback_query.message.chat_id
		bot.send_message(chat_id=chat_id, text='Выберите действие', reply_markup=reply_markup)
		username = update.callback_query.message.chat.username

	return CHOOSE_MAIN_ACTION

#Выбор пунктов Главного меню
def choose_main_action(bot, update):
	choice = update.callback_query.data

	if choice == '11' :
		uncompleted_tasks_list(bot, update)
		main_keyboard(bot, update)
		return CHOOSE_MAIN_ACTION
	elif choice == '12' :
		help_menu(bot, update)
		main_keyboard(bot, update)
		return CHOOSE_MAIN_ACTION

#Вывод незавершенных задач
def uncompleted_tasks_list(bot, update):
	if update.message != None:
		chat_id = update.message.chat_id
		username = update.message.chat.username
	elif update.callback_query.message != None:
		chat_id = update.callback_query.message.chat_id
		username = update.callback_query.message.chat.username
	
	
	tasks = get_tasks(username)
	
	tasks_resp = ''
	task_number = 0
	for index, item in enumerate(tasks):
		if item['is_completed'] == False:
			task_number+=1
			tasks_resp+=str(
				'Задача №' + str(task_number) + ':\n'
				+ str(find_task_parent(item['element_id'], item['element_type'])) + '\n' 
				+ item['text'] + '\n' 
				+ 'Срок выполнения до: ' + datetime.fromtimestamp(int(item['complete_till_at'])).strftime('%d-%m-%Y') 
				+ '\n--------------' 
				+ '\n')

	bot.send_message(chat_id=chat_id, text="Невыполненные задачи для: %s (%s)" % (encosts_private.accounts_tg[username], encosts_private.accounts_amo[username]['user']))
	bot.send_message(chat_id=chat_id, text=tasks_resp)
	
	
#Поиск привязки задачи	 
def find_task_parent(parent_id, parent_type):
	session = requests.Session()	

	if parent_type == 0:
		return 'Свободная задача'
	elif parent_type == 1:
		parent = json.loads(session.get('https://{0}.amocrm.ru/api/v2/contacts/?id={1}'.format(encosts_private.amo_domain, parent_id), cookies=amo_auth().cookies).text)
		return 'Задача для контакта: ' + parent['_embedded']['items'][0]['name'] + '\nКомпания: ' + parent['_embedded']['items'][0]['company']['name']
	elif parent_type == 2:
		parent = json.loads(session.get('https://{0}.amocrm.ru/api/v2/leads?id={1}'.format(encosts_private.amo_domain, parent_id), cookies=amo_auth().cookies).text)
		return 'Задача по сделке: ' + parent['_embedded']['items'][0]['name']
	elif parent_type == 3:
		parent = json.loads(session.get('https://{0}.amocrm.ru/api/v2/customers?id={1}'.format(encosts_private.amo_domain, parent_id), cookies=amo_auth().cookies).text)
		return 'Задача для покупателя: ' + parent['_embedded']['items'][0]['name']
	else:
		return 'Неизвестное происхождение задачи'

	
#Список команд
def help_menu(bot, update):
	if update.message != None:
		chat_id = update.message.chat_id
	elif update.callback_query.message != None:
		chat_id = update.callback_query.message.chat_id

	bot.send_message(chat_id=chat_id, text="/start - Рестарт\n /mainmenu - Главное меню \n/mytasks - Мои задачи\n /help - Справка по командам\n/stop - Закончить диалог")
	
	
	
	
#Завершение диалога
def stop_conversation(bot, update):
	bot.send_message(chat_id=update.message.chat_id, text="До встречи.")

	main_keyboard(bot, update)
	
	return CHOOSE_MAIN_ACTION


#*************************************
#Тестовые команды
def test_fu(bot,update):
	bot.send_message(chat_id=update.message.chat_id, text="%s" % update.message)

#*************************************


#Главная функция скрипта
def main():

	bot = telegram.Bot(token=encosts_private.tg_token)
	updater = Updater(token=encosts_private.tg_token)
	dp = updater.dispatcher
	conv_handler = ConversationHandler(
		entry_points= [CommandHandler('start', start)],

		states={
			CHOOSE_MAIN_ACTION: [CallbackQueryHandler(choose_main_action)],
			TASKS_MENU: [MessageHandler(Filters.text, start)],
			HELP_MENU: [MessageHandler(Filters.text, start)]
		},

		fallbacks=[CommandHandler('stop', stop_conversation)])



	dp.add_handler(conv_handler)
	dp.add_handler(CommandHandler('start', start))
	dp.add_handler(CommandHandler('help', help_menu))
	dp.add_handler(CommandHandler('mytasks', uncompleted_tasks_list))
	dp.add_handler(CommandHandler('mainmenu', main_keyboard))
	dp.add_handler(CommandHandler('test', test_fu))

	


	print(bot.get_me())
	updater.start_polling()
	updater.idle()



if __name__ == '__main__':
	main()


# start - Рестарт
# mainmenu - Главное меню
# stop - Закончить диалог
# mytasks - Мои задачи
# help - Список команд