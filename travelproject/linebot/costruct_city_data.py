from linebot.google_map_scraper import moving_store_scraper  , init_gmaps
from linebot.booking_scraper import get_hotel_information  ,get_detail_hotel_information
from linebot.tools import *
from linebot.density_analysis import local_density

set_env_attr()  # set env attrs
from linebot.models import *

# ---------GLOBAL PARAMETER ----------
# The basic prop. of lat , lng , and range of lat,lng of Taiwan
lng_1 = 102.516520*1000 # 1 longitude to meters
lat_1 = 110.740000*1000 # 1 latitude to meters
Admin_area_range_lng = [120.03786531340755 , 122.00991123709818]
Admin_area_range_lat = [21.871068186336803 , 25.30245194059663]

# City prop.
admin_area = 'Hualien'

center_of_city = {
    "Tainan" : {'location' : {'lat': 22.9913113, 'lng': 120.198012} , 'city_en_to_cn' : '台南'} ,
    "Hsinchu" : {'location' : {'lat': 24.8015877, 'lng': 120.9715883} , 'city_en_to_cn' : '新竹'},
    "Hualien" : {'location' : {'lat': 23.9927385, 'lng': 121.6013407} , 'city_en_to_cn' : '花蓮'},
    "Yilan" : {'location' : {'lat': 24.6783841, 'lng': 121.7745634} , 'city_en_to_cn' : '花蓮'},
}
try:
    search_center = center_of_city[admin_area]['location']
except KeyError:
    print(f'Not contain {admin_area} area !')

# All scrape type of stores
store_types = {
    '餐廳' : {'radius' : 500 , 'ranging' : 0 , 'place_type' : 'resturant' , 'place_sub_type' : 'resturant'} ,
    '飯店' : {'radius' : 500 , 'ranging' : 0 , 'place_type' : 'hotel' , 'place_sub_type' : 'hotel'} ,
    '便利商店' : {'radius' : 500 , 'ranging' : 0 , 'place_type' : 'resturant' , 'place_sub_type' : 'con'} ,
    '停車場' : {'radius' : 500 , 'ranging' : 0 , 'place_type' : 'station' , 'place_sub_type' : 'parking'} ,
    '夜市' : {'radius' : 500 , 'ranging' : 0 , 'place_type' : 'sightseeing' , 'place_sub_type' : 'nightmarket'} ,
    '觀光景點' : {'radius' : 500 , 'ranging' : 0 , 'place_type' : 'sightseeing' , 'place_sub_type' : 'sightseeing'} ,
    f"{center_of_city[admin_area]['city_en_to_cn']}火車站" : {'radius' : 500 , 'ranging' : 0 , 'place_type' : 'station' , 'place_sub_type' : 'station'} ,
}

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    if not admin_area:
        raise NameError('No admin_area assigned !!!')

    # Firstly , grab all type stores and storage into store_objects_all
    objects = {}
    for keyword , store_param  in store_types.items():
        objs = moving_store_scraper( keyword = keyword   ,
                                     search_center = search_center ,
                                     admin_area = admin_area ,
                                     radius = store_param['radius'] ,
                                     ranging = store_param['ranging']  ,
                                     place_type = store_param['place_type'] ,
                                     place_sub_type = store_param['place_sub_type'],
                                     )
        objects.update({
            keyword : objs
        })

    for type_name , stores in objects.items():
        print(f' tpye : {type_name}')
        print('\n')
        for store in stores:
            print(store.__dict__)
            print('\n')


    # Secondly , to compare the name of hotels between booking.com and gmaps and filter
    all_hotel_objects = Hotel.objects.filter(admin_area = admin_area)
    for hotel in all_hotel_objects:
        hotel.main_construct_step()


    # Thirdly , construct density data of all type of stores
    for _ , store_param in  store_types.items():
        data_objects = Place.objects.filter(place_sub_type = store_param['place_sub_type'])
        output , max_rho , max_pos  = local_density(data_objects,
                                            rating_dependent=True,
                                            jump_distance=100,
                                            ranging=40,
                                            scan_distance=300)
        density = output[0]
        gridtolatlng = output[1]

        # construct store density array objects
        Array_2d.create_array_object(arr = density,
                                     name = store_param['place_sub_type'],
                                     admin_area=admin_area)
    # construct grid to lat ,lng array object
    Array_3d.create_array_object(arr=gridtolatlng,
                                 name='gridtolatlng',
                                 admin_area=admin_area)
