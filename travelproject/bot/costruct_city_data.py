import os

from bot.google_map_scraper import GoogleMap_Scraper
from bot.tools import *
from bot.density_analysis import local_density
from bot.constants import *
from bot.save_load import *

set_env_attr()  # set env attrs
from bot.models import *

# City prop. and scrape params
admin_area = 'Hualien'
store_types = center_of_city[admin_area]['scrape_inform']

# check city data folder exist
store_folder_path = os.path.join(BASE_PATH ,
                                 'city_data',
                                 admin_area)
if not os.path.isdir(store_folder_path):
    os.mkdir(store_folder_path)


# search center
try:
    search_center = center_of_city[admin_area]['location']
except KeyError:
    print(f'Not contain {admin_area} area !')


# popular food
popular_food = center_of_city[admin_area]['popular_food']
criteria = store_types['餐廳']
for food in popular_food:
    store_types.update({food : criteria})


# step 1
def place_scraper(store_types, admin_area):
    
    if not admin_area:
        raise NameError('No admin_area assigned !!!')

    # Firstly , grab all type stores and storage into store_objects_all
    print("Now in stage 1 ~ grab all type stores and storage into store_objects_all  ")
    print(f' The store types: {store_types}')

    objects = {}
    for keyword , store_param  in store_types.items():

        print(f' Now scrape {keyword} data ~ , the params is {store_param}')
        gmap_scraper = GoogleMap_Scraper()
        objs = gmap_scraper.moving_store_scraper(keyword = keyword   ,
                                                 search_center = search_center ,
                                                 admin_area = admin_area ,
                                                 radius = store_param['radius'] ,
                                                 ranging = store_param['ranging']  ,
                                                 place_type = store_param['place_type'] ,
                                                 place_sub_type = store_param['place_sub_type'],
                                                 )
        objects.update({
            store_param['place_sub_type'] : objs
        })

    # check the store path exist or not.
    dict_path = os.path.join(store_folder_path, 'dict_data')
    density_path = os.path.join(store_folder_path, 'density_data')

    if not os.path.isdir(dict_path):
        os.mkdir(dict_path)
    if not os.path.isdir(density_path):
        os.mkdir(density_path)


    for place_sub_type , places in objects.items():

        print(f' tpye : {place_sub_type}')
        print('\n')

        place_dict_list = []
        for place_obj in places:

            place_dict = place_obj.__dict__
            place_dict_list.append(place_dict) # store the dict to list to generate pkl file.

            print(place_dict)
            print('\n')

        # store to pkl file
        print(f'Now writing {place_sub_type} type data to pkl file!')
        save_pkl(os.path.join(dict_path , f'{admin_area}_{place_sub_type}_dict') , place_dict_list)


# step 2
def construct_hotel_data(admin_area):
    
    all_hotel_objects = Hotel.objects.filter(admin_area=admin_area)
    for idx , hotel in enumerate(all_hotel_objects):
        print(f' Now in [{len(all_hotel_objects)}/{idx+1}] : {hotel.name}')
        hotel.main_construct_step()

    # remember to add nearby hotel for resturant objects!!
    for resturant in Resturant.objects.filter(admin_area=admin_area):
        resturant.add_nearby_hotel()


# step 3
def construct_density_matrix(store_types):


    density_path = os.path.join(store_folder_path, 'density_data')
    if not os.path.isdir(density_path):
        os.mkdir(density_path)


    for keyword , store_param in  store_types.items():

        print(f' Now scrape {keyword} data ~ , the params is {store_param}')

        place_sub_type = store_param['place_sub_type']
        data_objects = Place.objects.filter(place_sub_type = place_sub_type)
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

        # save density data to pkl file.
        save_pkl(os.path.join(density_path, f'{admin_area}_{place_sub_type}_dict'), density)

    # construct grid to lat ,lng array object
    Array_3d.create_array_object(arr=gridtolatlng,
                                 name='gridtolatlng',
                                 admin_area=admin_area)
    save_pkl(os.path.join(density_path, f'{admin_area}_gridtolatlng_dict'), gridtolatlng)
    


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    if not admin_area or not store_types:
        raise NameError('No admin_area store_type assigned !!!')
    
    # Firstly , grab all type stores and storage into store_objects_all
    print("Now in stage 1 ~ grab all type stores and storage into store_objects_all  ")

    #place_scraper(store_types, admin_area)

    # Secondly , to compare the name of hotels between booking.com and gmaps and filter
    print("Now in stage 2 ~ compare the name of hotels between booking.com and gmaps and filter ")

    #construct_hotel_data(admin_area)

    # Thirdly , construct density data of all type of stores
    print("Now in stage 3 ~ construct density data of all type of stores ")

    construct_density_matrix(store_types)
