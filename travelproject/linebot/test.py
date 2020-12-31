from linebot.async_scraper import async_get_hotel_information_by_date
from time import time


start = time()
r = async_get_hotel_information_by_date( target_day = '2020-12-31',
                                         day_range = 3 ,
                                         hotel_name = '台南晶英酒店',
                                         destination_admin = '台南',
                                         instant_information = True )
print( time()-start )
print(r)

for ele in sorted(r , reverse = True, key = lambda x : x['date']):
    print(f" 日期 : {ele['date']}  , 推薦房源 : {ele['room_recommend']} , {ele['room_remainings']} , 一晚 {ele['price']} TWD !")