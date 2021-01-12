from bot.google_map_scraper import moving_store_scraper  , init_gmaps
from bot.tools import *
from bot.density_analysis import local_density
from bot.constants import *

set_env_attr()  # set env attrs
from linebot.models import *

# City prop.
admin_area = 'Hualien'

try:
    search_center = center_of_city[admin_area]['location']
except KeyError:
    print(f'Not contain {admin_area} area !')

# All scrape type of stores
store_types = {
    '飯店' : {'radius' : 500 , 'ranging' : 0 , 'place_type' : 'hotel' , 'place_sub_type' : 'hotel'} , # TODO (備忘) : need to construct hotel first due to manytomany field !!!!!
    '餐廳' : {'radius' : 500 , 'ranging' : 0 , 'place_type' : 'resturant' , 'place_sub_type' : 'resturant'} ,
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
