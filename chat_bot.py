import os
import sqlite3
import asyncio
import logging
from datetime                   import datetime, timedelta
from aiogram                    import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context        import FSMContext
from aiogram.fsm.state          import State, StatesGroup
from aiogram.filters            import Command
from aiogram.types              import BotCommand
from aiogram.client.default     import DefaultBotProperties
from aiogram.enums              import ParseMode

#Установка и настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScheduleBot:
    def __init__(self, token):
        self.bot = Bot(
            token = token,
            default = DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        self.bot_storage = MemoryStorage()
        self.bot_dispatcher = Dispatcher(storage=self.bot_storage)
        self.setup_handlers()


    class AddEvent(StatesGroup):
        waiting_for_event_name = State()
        waiting_for_event_date = State()
        waiting_for_event_time = State()


    def setup_handlers(self):
        self.bot_dispatcher.message.register(self.command_start,    Command("start"))
        self.bot_dispatcher.message.register(self.command_help,     Command("help"))
        self.bot_dispatcher.message.register(self.command_schedule, Command("schedule"))
        self.bot_dispatcher.message.register(self.command_today,    Command("today"))
        self.bot_dispatcher.message.register(self.command_tomorrow, Command("tomorrow"))
        self.bot_dispatcher.message.register(self.command_week,     Command("week"))
        self.bot_dispatcher.message.register(self.command_add,      Command("add"))
        self.bot_dispatcher.message.register(self.proccess_event_name, self.AddEvent.waiting_for_event_name)
        self.bot_dispatcher.message.register(self.proccess_event_date, self.AddEvent.waiting_for_event_date)
        self.bot_dispatcher.message.register(self.proccess_event_time, self.AddEvent.waiting_for_event_time)


    async def set_commands(self):
        command_list = [
            BotCommand(command="/start",    description="Начало работы"),
            BotCommand(command="/help",     description="Помощь"),
            BotCommand(command="/today",    description="Расписание на сегодня"),
            BotCommand(command="/tomorrow", description="Расписание на завтра"),
            BotCommand(command="/week",     description="Расписание на неделю"),
            BotCommand(command="/add",      description="Добавить событие"),
            BotCommand(command="/schedule", description="Инструкция"),
        ]
        await self.bot.set_my_commands(command_list)


    async def command_start(self, message : types.message):
        """
        Обработчик команды /start - приветственное сообщение
        """
        await message.answer(
            "Привет! Я бот-планировщик для студентов и преподавателей.\n"
            "Я помогу вам управлять расписанием и напоминать о важных событиях.\n"
            "Используйте /help для списка команд"
        )


    async def command_help(self, message: types.message):
        """
        Обработчик команды /help - показывает доступные команды
        """
        help_message = (
            "<b>Доступные команды:</b>\n\n"
            "📅 <b>Расписание:</b>\n"
            "/today - Занятия на сегодня\n"
            "/tomorrow - Занятия на завтра\n"
            "/week - Занятия на неделю\n\n"
            "🆕 <b>Добавление событий:</b>\n"
            "/add - Добавить новое событие\n"
            "/schedule - Как добавить событие\n\n"
            "🔔 <b>Напоминания:</b>\n"
            "Автоматически за 1 час до события\n"
        )
        await message.answer(help_message)


    async def command_schedule(self, message : types.message):
        """
        Обработчик команды /schedule - инструкция для добавления события
        """
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        schedule_info = (
            "Как добавить событие:\n"
            "<b>1. Быстрый способ:</b>\n"
            f"  /add название {today} 18:00\n\n"
            "<b>2. Пошаговый способ:</b>\n"
            "  Отправьте команду /add и следуйте инструкциям\n\n"
            "<i>Пример:</i>\n"
            f"/add Олимпиада {today} 10:00\n"
        )
        await message.answer(schedule_info)


    async def command_today(self, message : types.message):
        """
        Обработчик команды /today - показывает события на сегодня
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
        """
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        events = self.get_events_for_date(message.from_user.id, tomorrow)
        if events:
            response = "<b>🗓  Расписание на завтра</b>\n\n"
            for event in events:
                response += f"⏳ {event[4]} — {event[2]}\n"
        else:
            await message.answer("Нет запланированных событий на завтра")
            return

        await message.answer(response)


    async def command_week(self, message : types.message):
        """
        Обработчик команды /week - показывает события на неделю
        """
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)
        events = self.get_events_for_period(message.from_user.id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        if not events:
            await message.answer("Нет событий на предстоящую неделю\n")
            return
        response = "<b>🗓  Расписание на неделю</b>\n"
        current_date = None

        for event in sorted(events, key=lambda x:(x[3], x[4])):
            event_date = event[3]
            if event_date != current_date:
                current_date = event_date
                response += f"<b>\n{current_date}:</b>\n"
            response += f"⏳ {event[4]} — {event[2]}\n"

        await message.answer(response)


    async def command_add(self, message : types.message, state : FSMContext):
        """
        Обработчик команды /add - добавление события
        """
        add_args = message.text.split()[1:]
        if len(add_args) >= 3:
            try:
                event_name = ' '.join(add_args[:-2])
                event_date = add_args[-2]
                event_time = self.normalize_time(add_args[-1])
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


    @staticmethod
    def init_db():
        """
        Инициализация базы данных
        """
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
        """
        Сохранение события
        """
        db_connection = sqlite3.connect("Schedule.db")
        cursor = db_connection.cursor()

        cursor.execute(
            "INSERT INTO schedule_table (user_id, event_name, event_date, event_time) VALUES (?, ?, ?, ?)",
            (user_id, event_name, event_date, event_time)
        )
        db_connection.commit()
        db_connection.close()


    async def check_reminders(self):
        now = datetime.now()
        reminder_time = now + timedelta(hours=1)

        db_connection = sqlite3.connect('Schedule.db')
        cursor = db_connection.cursor()

        cursor.execute('''
        SELECT * FROM schedule_table 
        WHERE reminded = 0 
        AND event_date = ? 
        AND event_time BETWEEN ? AND ?
        ''', (now.strftime('%Y-%m-%d'),
              now.strftime('%H:%M'),
              reminder_time.strftime('%H:%M')))

        for event in cursor.fetchall():
            try:
                await self.bot.send_message(
                    event[1],
                    f"🔔 <b>Напоминание:</b>\nЧерез час событие '{event[2]}' в {event[4]}"
                )
                cursor.execute('UPDATE schedule_table SET reminded = 1 WHERE id = ?', (event[0],))
                db_connection.commit()
            except Exception as e:
                logger.error(f"Ошибка напоминания: {e}")

        db_connection.close()


    def normalize_time(self, time_str: str) -> str:
        """
        Функция для нормализации времени
        """
        try:
            if ":" in time_str:
                hours, minutes = time_str.split(":")
            else:
                raise ValueError("❌ Некорректный формат времени")

            normalized = f"{int(hours):02d}:{int(minutes):02d}"
            datetime.strptime(normalized, "%H:%M")
            return normalized
        except (ValueError, AttributeError) as e:
            raise ValueError(f"❌ Некорректный формат времени: {time_str}") from e


    def get_events_for_date(self, user_id : int, date : str) -> list:
        """
        Получает события пользователя на конкретную дату
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
        обработчик состояния - получения названия события
        """
        current_date = datetime.now().strftime("%Y-%m-%d")
        if len(message.text) > 100:
            await message.answer("Название слишком длинное (макс. 100 символов)")
            return
        await state.update_data(event_name = message.text)
        await state.set_state(self.AddEvent.waiting_for_event_date)
        await message.answer(f"🗓 Введите дату события в формате <b>ГГГГ-ММ-ДД</b> (например, {current_date}):")


    async def proccess_event_date(self, message : types.Message, state : FSMContext):
        """
        обработчик состояния - получения даты события
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
        обработчик состояния - получения времени события
        """
        try:
            datetime.strptime(message.text, "%H:%M")
            data = await state.get_data()
            normalize_time = self.normalize_time(message.text)

            self.save_event(
                user_id=message.from_user.id,
                event_name=data["event_name"],
                event_date=data["event_date"],
                event_time=normalize_time
            )

            await message.answer(
                f"Событие <b>'{data['event_name']}'</b> добавлено!\n"
                f"Дата: <b>{data['event_date']}</b>\n"
                f"Время: <b>{message.text}</b>"
            )
            await state.clear()

        except ValueError:
            await message.answer("❌ Неверный формат времени. Используйте <b>ЧЧ:ММ</b>")


    def calc_time_left(self, now : datetime, event_time : str) -> str:
        """
        Форматирование времени
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
        """
        Основной метод запуска бота
        """
        self.init_db()
        await self.set_commands()

        async def scheduler():
            while True:
                await self.check_reminders()
                await asyncio.sleep(60)

        asyncio.create_task(scheduler())
        await self.bot_dispatcher.start_polling(self.bot)


ACCESS_TOKEN = "7834222412:AAEid2-JgISz0VS6xD9QONh_F9kdWNfSo9M"

if __name__ == "__main__":
    bot = ScheduleBot(ACCESS_TOKEN)
    asyncio.run(bot.run())
