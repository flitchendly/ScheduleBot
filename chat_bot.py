import os
from datetime import datetime, timedelta

from aiogram                    import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context        import FSMContext
from aiogram.fsm.state          import State, StatesGroup
from aiogram.filters            import Command
from aiogram.types              import BotCommand
from aiogram.client.default     import DefaultBotProperties
from aiogram.enums              import ParseMode


import sqlite3
import asyncio
import logging

# Настройки логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен для Telegram API
ACCESS_TOKEN = "7834222412:AAEid2-JgISz0VS6xD9QONh_F9kdWNfSo9M"


class SchedulerBot:
    def __init__(self, token):
        self.bot = Bot(
            token = token,#ACCESS_TOKEN,
            default = DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
        )
        self.bot_storage = MemoryStorage()
        self.bot_dispatcher = Dispatcher()
        self.setup_handlers()

    # Настройка FSM
    class AddEvent(StatesGroup):
        waiting_for_event_name = State()
        waiting_for_event_date = State()
        waiting_for_event_time = State()

    # Настройка бота
    def setup_handlers(self):
        self.bot_dispatcher.message.register(self.command_start, Command("start"))
        self.bot_dispatcher.message.register(self.command_help, Command("help"))
        self.bot_dispatcher.message.register(self.command_schedule, Command("schedule"))
        self.bot_dispatcher.message.register(self.command_today, Command("today"))
        self.bot_dispatcher.message.register(self.command_tomorrow, Command("tomorrow"))
        self.bot_dispatcher.message.register(self.command_week, Command("week"))
        self.bot_dispatcher.message.register(self.command_add, Command("add"))
        #Уведомление о событиях

    async def set_commands(self):
        command_list = [
            BotCommand(command="/start", description="Начало работы"),
            BotCommand(command="/help", description="Помощь"),
            BotCommand(command="/today", description="Расписание на сегодня"),
            BotCommand(command="/tomorrow", description="Расписание на завтра"),
            BotCommand(command="/week", description="Расписание на неделю"),
            BotCommand(command="/add", description="Добавить событие"),
            BotCommand(command="/schedule", description="Инструкция"),
        ]
        await self.bot.set_my_commands(command_list)

    async def command_start(self, message : types.message):
        """

        :param message:
        :return:
        """
        await message.answer(
            "Привет! Я бот-планировщик для студентов и преподавателей.\n"
            "Я помогу вам управлять расписанием и напоминать о важных событиях.\n"
            "Используйте /help для списка команд"
        )

    async def command_help(self, message: types.message):
        """

        :param message:
        :return:
        """
        help_message = (
            "Доступные команды:\n\n"
            "Расписание:\n"
            "/today - Занятия на сегодня\n"
            "/tomorrow - Занятия на завтра\n"
            "/week - Занятия на неделю\n\n"
            "Добавление событий:\n"
            "/add - Добавить новое событие\n"
            "/schedule - Как добавить событие\n\n"
            "Напоминания:\n"
            "Автоматически за 1 час до события\n"
            "Конец"
        )
        await message.answer(help_message)

    async def command_schedule(self, message : types.message):
        """

        :param message:
        :return:
        """
        schedule_info = (
            "Как добавить событие:\n"
            "1. Быстрый способ:\n"
            "```\n/add название 2025-07-13 18:00\n```"
            "2. Пошаговый способ:\n"
            "Отправьте команду /add и следуйте инструкциям\n\n"
            "Пример:\n"
            "/add deadline по тз 2025-07-14 10:00\n"
        )
        await message.answer(schedule_info)





    async def command_today(self, message : types.message):
        """
        Обработчик команды /today - показывает события на сегодня
        :param message:
        :return:
        """
        today = datetime.now().strftime("%Y-%m-%d")
        events = self.get_events_for_date(message.from_user.id, today)

        if events:
            response = "*Расписание на сегодня*\n"
            for event in events:
                response += f"- {event[2]} в {event[4]}\n"
        else:
            response = "Нет запланированных событий на сегодня"

        await message.answer(response)

    async def command_tomorrow(self, message : types.message):
        """

        :param message:
        :return:
        """
        await message.answer("tomorrow")

    async def command_week(self, message : types.message):
        """

        :param message:
        :return:
        """
        await message.answer("week")

    async def command_add(self, message : types.message, state : FSMContext):
        """

        :param message:
        :return:
        """
        add_args = message.text.split()[1:]
        if len(add_args) >= 3:
            try:
                event_name = ' '.join(add_args[:-2])
                event_date = add_args[-2]
                event_time = add_args[-1]
                datetime.strptime(event_date, '%Y-%m-%d')
                datetime.strptime(event_time, '%H:%M')

                self.save_event(message.from_user.id, event_name, event_date, event_time)
                await message.answer(
                    f"Событие {event_name} успешно добавлено\n"
                    f"Дата:  {event_date}\n"
                    f"Время: {event_time}\n"
                )
                return
            except ValueError:
                pass

        await state.set_state(self.AddEvent.waiting_for_event_name)
        await message.answer("Введите название события:")


    # Настройка БД
    @staticmethod
    def init_db():
        db_connection = sqlite3.connect("Schedule.db")
        print("init_db")
        cursor = db_connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedule_table(
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            event_name TEXT NOT NULL,
            event_date TEXT NOT NULL,
            event_time TEXT NOT NULL,
            reminded   INTEGER DEFAULT 0
            )   
        ''')
        db_connection.commit()
        db_connection.close()
        print("create_schedule")

    def save_event(self, user_id: int, event_name: str, event_date: str, event_time: str):
        '''

        :param user_id:
        :param event_name:
        :param event_date:
        :param event_time:
        :return:
        '''
        db_connection = sqlite3.connect("Schedule.db")
        print("save_event")
        cursor = db_connection.cursor()

        cursor.execute(
            "INSERT INTO schedule_table (user_id, event_name, event_date, event_time) VALUES (?, ?, ?, ?)",
            (user_id, event_name, event_date, event_time)
        )
        db_connection.commit()
        db_connection.close()


#-----------------------------------------------------------------------------------------------------------------------
    async def check_reminders(self):
        current_time = datetime.now()
        reminder_time = current_time + timedelta(hours=1)

    #БД
    def get_events_for_date(self, user_id : int, date : str) -> list:
        """
        Получает события пользователя на конкретную дату
        :param user_id:
        :param date:
        :return:
        """
        db_connection = sqlite3.connect("Schedule.db")
        print("get_events_for_date")
        cursor = db_connection.cursor()

        cursor.execute('''
            SELECT * FROM schedule_table 
            WHERE user_id = ? AND event_date = ?
            ORDER BY event_time 
        ''', (user_id, date))
        events = cursor.fetchall()

        db_connection.close()

        return events


    async def run(self):
        self.init_db()
        await self.set_commands()

        async def scheduler():
            while True:
                await self.check_reminders() #расчет оставшегося времени до посылки уведомления
                await asyncio.sleep(60)

        asyncio.create_task(scheduler())
        await self.bot_dispatcher.start_polling(self.bot)



if __name__ == "__main__":
    bot = SchedulerBot(ACCESS_TOKEN)
    asyncio.run(bot.run())
