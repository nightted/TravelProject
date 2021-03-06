import pickle
import os
from bot.tools import *

set_env_attr()  # set env attrs
from bot.models import *

DICT_PATH = 'C:/Users/tedchang/PycharmProjects/TravelProject/travelproject/city_data/Tainan/'

def save_pkl(path, data):
    with open(path, "wb") as pkl:
        pickle.dump(data, pkl)

def load_pkl(path):
    with open(path, "rb") as pkl:
        data = pickle.load(pkl)
    return data

def set_sql_data(data_path , types , hash_types , city = None ):

    load_data = load_pkl(data_path)

    # if is list of dicts
    if isinstance(load_data , list):
        for data in load_data:
            hash_types[types].create_obj_by_dict(**data) # create store objs

    # if is numpy array
    if type(load_data).__module__ == np.__name__:
        if not city:
            raise NameError('Array data requires city as attribute!')

        data = load_data.tolist()
        hash_types[types].create_array_object(
            admin_area = city,
            name = types,
            arr = data
        ) # remember the type is "LIST" !

def city_data_toSQL( city , base_path = DICT_PATH ):

    hash_sub_types = {
        'train': Station,
        'hotel': Hotel,
        'nightmarket': Sightseeing,
        'sightseeing': Sightseeing,
        'resturant': Resturant,
        'beefsoup': Resturant,
        'eelnoodles': Resturant,
        'gruel': Resturant,
        'con': Resturant,
        'porkrice': Resturant
    }

    for types in hash_sub_types.keys():

        data_path = os.path.join(base_path , 'dict_data' , f'{city}_{types}_dict')
        try:
            set_sql_data(data_path=data_path,
                         types=types ,
                         hash_types=hash_sub_types
                         )
        except KeyError:
            print(f'Not contain this type {types} data!')

def density_data_toSQL(city  , base_path = DICT_PATH ):

    hash_types = {
        'beefsoup' : Array_2d ,
        'con' : Array_2d ,
        'eelnoodles' : Array_2d ,
        'gruel' : Array_2d ,
        'hotel' : Array_2d ,
        'porkrice' : Array_2d ,
        'resturant' : Array_2d ,
        'gridtolatlng' : Array_3d
    }

    for types in hash_types.keys():

        data_path = os.path.join(base_path , 'density_data' , f'Tainan_{types}_density')
        try:
            set_sql_data(data_path=data_path,
                         types=types,
                         hash_types=hash_types,
                         city=city)
        except KeyError:
            print(f'Not contain this type {types} data!')

if __name__  == '__main__' :

    density_data_toSQL(city='Tainan')





