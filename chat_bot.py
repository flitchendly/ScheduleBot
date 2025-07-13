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
            default = DefaultBotProperties(parse_mode=ParseMode.HTML)
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
        self.bot_dispatcher.message.register(self.proccess_event_name, self.AddEvent.waiting_for_event_name)
        self.bot_dispatcher.message.register(self.proccess_event_date, self.AddEvent.waiting_for_event_date)
        self.bot_dispatcher.message.register(self.proccess_event_time, self.AddEvent.waiting_for_event_time)
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
            "\n/add название 2025-07-13 18:00\n"
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
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        events = self.get_events_for_date(message.from_user.id, today)

        if not events:
            await message.answer("Нет запланированных событий на сегодня")
            return

        past_events = []
        upcoming_events = []

        for event in events:
            event_time = event[4]
            if event_time < current_time:
                past_events.append(event)
            else:
                upcoming_events.append(event)

        response = "<b>🗓  Расписание на сегодня</b>\n\n"
        if past_events:
            response += "<i>✅ Прошедшие события:</i>\n"
            for event in past_events:
                response += f" {event[4]} — {event[2]} <i>(завершено)</i>\n"
            response += "\n"

        if upcoming_events:
            response += "<i>🕒 Предстоящие события:</i>\n"
            for event in upcoming_events:
                time_left = self.calc_time_left(now, event[4])
                response += f" {event[4]} — {event[2]} <i>({time_left})</i>\n"

        await message.answer(response)


    async def command_tomorrow(self, message : types.message):
        """
        Обработчик команды /tomorrow - показывает события на завтра
        :param message:
        :return:
        """
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        events = self.get_events_for_date(message.from_user.id, tomorrow)
        if events:
            response = "<b>🗓  Расписание на завтра</b>\n\n"
            for event in events:
                response += f"XX {event[4]} — {event[2]}\n"
        else:
            await message.answer("Нет запланированных событий на завтра")
            return

        await message.answer(response)


    async def command_week(self, message : types.message):
        """
        Обработчик команды /week - показывает события на неделю
        :param message:
        :return:
        """
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)
        events = self.get_events_for_period(message.from_user.id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        if not events:
            await message.answer("Нет событий на предстоящую неделю\n")
            return
        response = "<b>🗓  Расписание на неделю</b>\n"
        current_date = None
        first_day = True

        for event in sorted(events, key=lambda x:(x[3], x[4])):
            event_date = event[3]
            if event_date != current_date:
                current_date = event_date
                if not first_day:
                    response += "\n"
                else:
                    first_day = False
                response += f"<b>\n{current_date}:</b>\n"
            response += f"X {event[4]} — {event[2]}"

        await message.answer(response)


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
        cursor = db_connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedule_table(
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            event_name  TEXT NOT NULL,
            event_date  TEXT NOT NULL,
            event_time  TEXT NOT NULL,
            reminded    INTEGER DEFAULT 0
            )   
        ''')
        db_connection.commit()
        db_connection.close()


    def save_event(self, user_id: int, event_name: str, event_date: str, event_time: str):
        '''

        :param user_id:
        :param event_name:
        :param event_date:
        :param event_time:
        :return:
        '''
        db_connection = sqlite3.connect("Schedule.db")
        cursor = db_connection.cursor()

        cursor.execute(
            "INSERT INTO schedule_table (user_id, event_name, event_date, event_time) VALUES (?, ?, ?, ?)",
            (user_id, event_name, event_date, event_time)
        )
        db_connection.commit()
        db_connection.close()


#-----------------------------------------------------------------------------------------------------------------------

    async def check_reminders(self):
        now = datetime.now()
        db_connection = sqlite3.connect('schedule.db')
        cursor = db_connection.cursor()

        # Получаем все события, которые:
        # 1. Еще не были напомнены (reminded = 0)
        # 2. Должны начаться в ближайшие 1 час 10 минут
        cursor.execute('''
        SELECT * FROM schedule_table 
        WHERE reminded = 0 
        AND event_date = ?
        AND event_time BETWEEN ? AND ?
        ORDER BY event_time
        ''', (
            now.strftime('%Y-%m-%d'),
            now.strftime('%H:%M'),
            (now + timedelta(minutes=70)).strftime('%H:%M')  # +1ч10мин
        ))

        for event in cursor.fetchall():
            event_time = datetime.strptime(event[4], '%H:%M').time()
            time_diff = (datetime.combine(now.date(), event_time) - now).total_seconds() / 60

            if 60 >= time_diff > 10:  # Напоминание за 1 час
                await self.send_reminder(event,"планируемое событие - ")
                cursor.execute('UPDATE schedule_table SET reminded = 1 WHERE id = ?', (event[0],))

            elif 10 >= time_diff > 0:  # Напоминание за 10 минут
                await self.send_reminder(event,"планируемое событие - ")
                cursor.execute('UPDATE schedule_table SET reminded = 1 WHERE id = ?', (event[0],))

        db_connection.commit()
        db_connection.close()

    async def send_reminder(self, event, time_left):
        try:
            await self.bot.send_message(
                event[1],
                f"<b>Напоминание:</b>\n{time_left} '{event[2]}' в {event[4]}"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки напоминания: {e}")


    def get_events_for_date(self, user_id : int, date : str) -> list:
        """
        Получает события пользователя на конкретную дату
        :param user_id:
        :param date:
        :return:
        """
        db_connection = sqlite3.connect("Schedule.db")
        cursor = db_connection.cursor()

        cursor.execute('''
            SELECT * FROM schedule_table 
            WHERE user_id = ? AND event_date = ?
            ORDER BY event_time 
        ''', (user_id, date))
        events = cursor.fetchall()

        db_connection.close()

        return events

    def get_events_for_period(self, user_id : int, date_start : str, date_end : str) -> list:
        """
        Получает события пользователя за период
        :param user_id:
        :param date:
        :return:
        """
        db_connection = sqlite3.connect("Schedule.db")
        cursor = db_connection.cursor()

        cursor.execute('''
            SELECT * FROM schedule_table 
            WHERE user_id = ? AND event_date BETWEEN ? AND ?
            ORDER BY event_date, event_time
        ''', (user_id, date_start, date_end))
        events = cursor.fetchall()

        db_connection.close()

        return events

    async def proccess_event_name(self, message : types.Message, state : FSMContext):
        """
        Обработчик состояния - получения названия события
        :param message:
        :param state:
        :return:
        """
        current_date = datetime.now().strftime("%Y-%m-%d")
        if len(message.text) > 100:
            await message.answer("Название слишком длинное (макс. 100 символов)")
            return
        await state.update_data(event_name = message.text)
        await state.set_state(self.AddEvent.waiting_for_event_date)
        await message.answer(f"X Введите дату события в формате <b>ГГГГ-ММ-ДД</b> (например, {current_date}):")

    async def proccess_event_date(self, message : types.Message, state : FSMContext):
        """
        Обработчик состояния - получения даты события
        :param message:
        :param state:
        :return:
        """
        try:
            datetime.strptime(message.text, "%Y-%m-%d")
            await state.update_data(event_date = message.text)
            await state.set_state(self.AddEvent.waiting_for_event_time)
            await message.answer("⏰ Введите время события в формате <b>ЧЧ:ММ</b> (например, 14:30):")
        except ValueError:
            await message.answer("❌ Неверный формат даты. Используйте <b>ГГГГ-ММ-ДД</b>")


    async def proccess_event_time(self, message : types.Message, state : FSMContext):
        """
        Обработчик состояния - получения времени события
        :param message:
        :param state:
        :return:
        """
        try:
            datetime.strptime(message.text, "%H:%M")
            data = await state.get_data()

            self.save_event(
                user_id=message.from_user.id,
                event_name=data["event_name"],
                event_date=data["event_date"],
                event_time=message.text
            )

            await message.answer(
                f"Событие <b>'{data['event_name']}'</b> добавлено!\n"
                f"Дата: <b>{data['event_date']}</b>\n"
                f"Время: <b>{message.text}</b>"
            )
            await state.clear()

        except ValueError:
            await message.answer("Неверный формат времени. Используйте <b>ЧЧ:ММ</b>")

    def calc_time_left(self, now : datetime, event_time : str) -> str:
        """

        :param now:
        :param event_time:
        :return:
        """
        event_datetime = datetime.strptime(event_time, "%H:%M")
        delta = timedelta(hours=event_datetime.hour - now.hour, minutes=event_datetime.minute - now.minute)
        if delta.total_seconds() <= 0:
            return "Сейчас"
        hours, reminder = divmod(delta.seconds, 3600)
        minutes = reminder // 60

        if hours > 0:
            return f"через {hours} ч. {minutes} мин."
        else:
            return f"через {minutes} мин."


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
