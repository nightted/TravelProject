# GLOBAL　PARAMETERS

import configparser
import os
from bot.tools import read_key

# some params
NEARBY_CRITERIA = 500
GMAP_RATING_THRESHOLD = 4.0
BOOKING_RATING_THRESHOLD = 8.0

# geometry property of taiwan
lng_1 = 102.516520*1000 # 1 longitude to meters
lat_1 = 110.740000*1000 # 1 latitude to meters
Admin_area_range_lng = [120.03786531340755 , 122.00991123709818] # range of lng in taiwan
Admin_area_range_lat = [21.871068186336803 , 25.30245194059663] # range of lng in taiwan

# basic scraper property
basic_scrape = {
                '飯店' : {'radius' : 500 , 'ranging' : 4 , 'place_type' : 'hotel' , 'place_sub_type' : 'hotel'} , # TODO (備忘) : need to construct hotel first due to manytomany field !!!!!
                '餐廳' : {'radius' : 500 , 'ranging' : 4 , 'place_type' : 'resturant' , 'place_sub_type' : 'resturant'} ,
                '便利商店' : {'radius' : 500 , 'ranging' : 4 , 'place_type' : 'resturant' , 'place_sub_type' : 'con'} ,
                '停車場' : {'radius' : 1000 , 'ranging' : 3 , 'place_type' : 'station' , 'place_sub_type' : 'parking'} ,
                '夜市' : {'radius' : 2000 , 'ranging' : 2 , 'place_type' : 'sightseeing' , 'place_sub_type' : 'nightmarket'} ,
                '觀光景點' : {'radius' : 3000 , 'ranging' : 4 , 'place_type' : 'sightseeing' , 'place_sub_type' : 'sightseeing'} ,
                '火車站' : {'radius' : 5000 , 'ranging' : 1 , 'place_type' : 'station' , 'place_sub_type' : 'station'} ,
                }

# city property
center_of_city = {
    "Tainan" : {'location' : {'lat': 22.9913113, 'lng': 120.198012} ,
                'city_en_to_cn' : '台南' ,
                'popular_food' : ['牛肉湯','肉燥飯','鹹粥','鱔魚意麵'] ,
                'city_range' : {'lat' : [22.887709 ,23.413328] , 'lng' : [120.033587 ,120.656311]},
                'scrape_inform' : basic_scrape} ,
    "Hsinchu" : {'location' : {'lat': 24.8015877, 'lng': 120.9715883} ,
                 'city_en_to_cn' : '新竹' ,
                 'popular_food' : ['米粉' , '貢丸'] ,
                 'city_range' : {'lat' : [24.428411 ,24.946137] , 'lng' : [120.878891 ,121.412232]},
                 'scrape_inform' : basic_scrape},
    "Hualien" : {'location' : {'lat': 23.9927385, 'lng': 121.6013407} ,
                 'city_en_to_cn' : '花蓮' ,
                 'popular_food' : ['扁食'] ,
                 'city_range' : {'lat' : [23.099277 ,24.370550] , 'lng' : [120.989121 ,121.647408]},
                 'scrape_inform' : basic_scrape},
    "Yilan" : {'location' : {'lat': 24.6783841, 'lng': 121.7745634} ,
               'city_en_to_cn' : '宜蘭' ,
               'popular_food' : ['糕渣' , '鴨賞'] ,
               'city_range' : {'lat' : [24.312153 ,24.866411] , 'lng' : [121.316842 ,121.885963]},
               'scrape_inform' : basic_scrape},
}

# URL of booking.com
BOOKING_URL = 'https://www.booking.com'
BASE_BOOKING_URL = BOOKING_URL + '/searchresults.zh-tw.html'

# secret key path
KEY_PATH = 'C:/Users/h5904/PycharmProjects/TravelProject/travelproject/docs/API_KEY.txt' # TODO : set as enviroment variables
SECRET_KEY_PATH = 'C:/Users/h5904/PycharmProjects/TravelProject/travelproject/docs/SECRET_KEY.txt'
ACCESS_TOKEN_PATH = 'C:/Users/h5904/PycharmProjects/TravelProject/travelproject/docs/keys/CHANNEL_ACCESS_TOKEN.txt'
SECRET_PATH = 'C:/Users/h5904/PycharmProjects/TravelProject/travelproject/docs/keys/CHANNEL_SECRET.txt'

#BASE path of project
BASE_PATH = os.path.dirname(os.path.dirname(__file__))  # base path => ../travelproject/



if __name__ == '__main__':

    config = configparser.ConfigParser()
    '''config['path'] = {}

    path = config['path']
    path['GOOGLE_MAP_API_KEY'] = read_key(KEY_PATH)
    path['DJANGO_SECRET_KEY'] = read_key(SECRET_KEY_PATH)
    path['CHANNEL_ACCESS_TOKEN'] = read_key(ACCESS_TOKEN_PATH)
    path['CHANNEL_SECRET'] = read_key(SECRET_PATH)

    with open('config.ini', 'w') as configfile:
        config.write(configfile)'''

    config.read('config.ini')
    print(config.sections())



