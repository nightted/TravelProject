import asyncio
from bot.booking_scraper import get_hotel_information
from bot.google_search_and_show import *
from bot.tools import  get_date_string

from functools import partial


url = "https://www.booking.com/searchresults.zh-tw.html"
header_url = "https://www.booking.com"


loop = asyncio.get_event_loop() #建立一個Event Loop

# Async for main construct step
async def async_main_construct_step(hotel):

    await loop.run_in_executor(None , hotel.main_construct_step())

def tasks_generator_for_main_construct_step_by_hotel(hotels): # 定義一個中間會被中斷的協程

    tasks = []
    for hotel in hotels :
        tasks.append(loop.create_task(async_main_construct_step(hotel)))
    return tasks

def async_main_construct_step_by_hotel(hotels):

    tasks = tasks_generator_for_main_construct_step_by_hotel(hotels)
    loop.run_until_complete(asyncio.wait(tasks)) # https://stackoverflow.com/questions/44048536/python3-get-result-from-async-method
    print('Finish comparison!')




# TODO : async search
# Async for get hotel information
async def async_get_search_result(resturant):

    # from : https://stackoverflow.com/questions/53368203/passing-args-kwargs-to-run-in-executor
    res = await loop.run_in_executor(None , partial(get_search_result_by_resturant, resturant ))
    return res

def tasks_generator_for_get_search_result_by_resturant(resturants): # 定義一個中間會被中斷的協程

    tasks = []
    for resturant in resturants :
        tasks.append(loop.create_task(async_get_search_result(resturant)))
    return tasks

def async_get_search_result_by_resturant(resturants):

    tasks = tasks_generator_for_get_search_result_by_resturant(resturants)
    res  , _ = loop.run_until_complete(asyncio.wait(tasks)) # https://stackoverflow.com/questions/44048536/python3-get-result-from-async-method
    res_dict = [ele.result() for ele in res]

    return res_dict




# Async for get hotel information
async def async_get_hotel_information( **kwargs ):

    # from : https://stackoverflow.com/questions/53368203/passing-args-kwargs-to-run-in-executor
    res = await loop.run_in_executor(None , partial(get_hotel_information, **kwargs ))
    return res

def tasks_generator_for_get_hotel_information_by_date( dates , **kwargs ): # 定義一個中間會被中斷的協程

    tasks = []
    for date in dates :
        tasks.append(loop.create_task(async_get_hotel_information(  **kwargs , date = date )))
    return tasks

def async_get_hotel_information_by_date(target_days , **kwargs ):

    dates = [[day , get_date_string(day ,1)] for day in target_days] # construct input date for func. get_hotel_information
    tasks = tasks_generator_for_get_hotel_information_by_date( dates = dates , **kwargs)
    res  , _ = loop.run_until_complete(asyncio.wait(tasks)) # https://stackoverflow.com/questions/44048536/python3-get-result-from-async-method
    res_dict = [ele.result() for ele in res]

    return res_dict