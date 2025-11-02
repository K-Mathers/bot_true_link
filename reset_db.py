import asyncio
from app.db.database import engine, Base
# Обязательно импортируем модели, чтобы Base знала о них
from app.db.models import User, Subscription 

async def main():
    print("Удаление старых таблиц...")
    async with engine.begin() as conn:
        # Удаляем ВСЕ таблицы, известные Base
        await conn.run_sync(Base.metadata.drop_all)
    print("Старые таблицы удалены.")
    
    print("Создание новых таблиц по моделям...")
    async with engine.begin() as conn:
        # Создаем ВСЕ таблицы заново
        await conn.run_sync(Base.metadata.create_all)
    print("База данных успешно пересоздана.")
    
    # Закрываем пул соединений
    await engine.dispose()

if __name__ == "__main__":
    print("----------------------------------------------------------------")
    print("ВНИМАНИЕ! ЭтоТ СКРИПТ ПОЛНОСТЬЮ УДАЛИТ ВСЕ ДАННЫЕ")
    print("из таблиц 'users' и 'subscriptions'.")
    print("----------------------------------------------------------------")
    
    # Даем пользователю шанс отменить
    try:
        input("Нажмите Enter для продолжения или CTRL+C для отмены...")
    except KeyboardInterrupt:
        print("\nОтмена.")
        exit()

    asyncio.run(main())
