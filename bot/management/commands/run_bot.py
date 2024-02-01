from django.core.management.base import BaseCommand
from aiogram import Bot, Dispatcher
import requests
import json
import urllib.parse
from bot.utils.loader import bot, dp, loop

from aiogram import executor, types
import asyncio

import time
from concurrent.futures import ThreadPoolExecutor

from bot.models import TelegramUser

stop = True
def start_bot():
    while stop:
        page_count = 180
        csmoney_allowed_discount = 0.25

        for page in range(0, page_count, 60):
            stop_loop = False
            response = requests.get(f"https://cs.money/1.0/market/sell-orders?limit=60&minPrice=0.25&offset={page}&order=desc&sort=discount&type=12")

            src = response.text
            try:   
                data = json.loads(src)
            except json.JSONDecodeError as e:
                data = {
                    'items': []
                }
                stop_loop = True
                print('CSMONEY ERROR')

            with open(f'items{page}.json','w',encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)

            item_list = []
            for item in data['items']:
                if item['pricing']['discount'] >= csmoney_allowed_discount:
                    item_id = item["id"]
                    full_name_of_item = item["asset"]["names"]["full"]
                    item_link = f"https://steamcommunity.com/market/listings/730/{urllib.parse.quote(full_name_of_item)}"
                    csmoney_computed_price = item["pricing"]["computed"]
                    csmoney_discount = item["pricing"]["discount"]
                    
                    item_list.append(
                        {
                        "Name": full_name_of_item,
                        "Link": item_link,
                        "Price": csmoney_computed_price,
                        "Discount": csmoney_discount
                        }
                    )
                else:
                    stop_loop = True
                    break

            with open(f'items_discount{page}.json','w',encoding='utf-8') as file:
                json.dump(item_list, file, indent=4, ensure_ascii=False)

            if stop_loop:
                break
        print('code')
        time.sleep(60)

async def on_startup(_):
    print("Bot started")
    loop.run_in_executor(ThreadPoolExecutor(), start_bot)

async def on_shutdown(_):
    global stop
    stop = False
    dp.stop_polling()
    await dp.storage.close()
    await dp.storage.wait_closed()
    loop.stop()

    
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await bot.send_message(message.chat.id, 'Hello')
    await TelegramUser.objects.aget_or_create(chat_id=message.from_user.id)

class Command(BaseCommand):
    help = 'Start bot'

    def handle(self, *args, **options):        
        
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)