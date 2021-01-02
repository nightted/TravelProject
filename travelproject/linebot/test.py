from linebot.async_scraper import async_get_hotel_information_by_date
from linebot.google_map_scraper import moving_store_scraper
from linebot.tools import read_key

import googlemaps
import time
import os
import django
import matplotlib.pyplot as plt

# [NOTE!] : 這邊解法 from https://blog.csdn.net/kong_and_whit/article/details/104167178?utm_medium=distribute.pc_relevant_t0.none-task-blog-BlogCommendFromBaidu-1.not_use_machine_learn_pai&depth_1-utm_source=distribute.pc_relevant_t0.none-task-blog-BlogCommendFromBaidu-1.not_use_machine_learn_pai
#           另外 content root path 要改成 django 的 root (travelproject) , 而不是 Venv 的 root !!!
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "travelproject.settings")
django.setup()
from linebot.models import Hotel , Resturant , Station , Sightseeing , Place , Comment , Picture , Hotel_Instance



def test_hotel_available(day_range , hotel , num_people , num_rooms):

    price = []
    for d in range(10,31,2*day_range + 1):

        res = async_get_hotel_information_by_date( target_day = f'2021-01-{d}',
                                                 day_range = day_range ,
                                                 num_people = num_people ,
                                                 num_rooms = num_rooms ,
                                                 hotel_name = hotel,
                                                 destination_admin = '台南',
                                                 instant_information = True )

        for ele in sorted(r, reverse=False, key=lambda x: x['queried_date']):

            print(f" 日期 : {ele['queried_date']}  , 推薦房源 : {ele['room_recommend']} , {ele['room_remainings']} , 一晚 {ele['price']} TWD !")

            if ele['price']:
                price.append(ele['price'])
        time.sleep(5)

    plt.plot(price)
    plt.show()

    return res

def test_hotel_instant( test_len ):

    test_hotel = []
    all_hotels = Hotel.objects.all()

    for hotel in all_hotels:
        if hotel.room_source == 'booking':
            test_hotel.append(hotel)
        if len(test_hotel) > test_len :
            break

    for htl in test_hotel:
        print(f'now in hotel : {htl.name}')
        htl.construct_instant_attr(
                                    date='2021-01-10' ,
                                    day_range=2,
                                    num_rooms=1,
                                    num_people=2
                                  )


if __name__ == '__main__':

    KEY_PATH = 'C:/Users/h5904/PycharmProjects/TravelProject/travelproject/docs/API_KEY.txt'
    GOOGLE_API_KEY = read_key(KEY_PATH)
    maps = googlemaps.Client(GOOGLE_API_KEY)
    location = maps.geocode('春川煎餅')[0]['geometry']['location']


    parkings = moving_store_scraper(
        maps = maps,
        keyword = '停車場',
        search_center = location,
        admin_area = '台南',
        radius = 500,
        ranging = 0,
        next_page_token=None,
        objects=None,
        place_type='station',
        place_sub_type='parking',
        mode="max_area"
    )

    for p in parkings:
        print(p.__dict__)

