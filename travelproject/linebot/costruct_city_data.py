import googlemaps
from linebot.google_map_scraper import moving_store_scraper , read_key



# PATH
key_path = 'API_KEY/API_KEY.txt'

# INITIALIZE DATA
#name_transform = load_pkl('store data/Hotel_name_transform.pickel')
#grid_to_latlng = load_pkl('grid_to_latlng/grid_to_latlng')
#data_all_objects = load_pkl('store data/data_all_objects') # this wil replace by SQL

# GLOBAL PARAMETER
lng_1 = 102.516520*1000 # 1 longitude to meters
lat_1 = 110.740000*1000 # 1 latitude to meters

# Store_types
store_types = {
                 'data_hotel': '飯店',
                }

store_objects_all = { type_name : None for _ , type_name in store_types.items() }


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    # INITIALIZE G-MAP
    GOOGLE_API_KEY = read_key(key_path)
    maps = googlemaps.Client(key=GOOGLE_API_KEY)
    position = ['春川煎餅']
    result = maps.geocode(position)
    location = result[0]['geometry']['location']

    # firstly , grab all type stores and storage into store_objects_all
    for type_name , chinese_name  in store_types.items():
        store_objects_all[type_name] = moving_store_scraper(maps = maps ,
                                                         keyword = chinese_name   ,
                                                         search_center = location ,
                                                         radius = 500 ,
                                                         ranging = 0  ,
                                                         store_type = type_name.split('_')[1] )
    for hotel in store_objects_all['data_hotel']:
        print(hotel)

    # next to compare the name of hotels between booking.com and gmaps and filter



    # next to construct detail information of all avaliable hotels