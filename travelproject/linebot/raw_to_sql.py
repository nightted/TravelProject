from django.test import TestCase
from django.conf import settings

import pickle
import os
import django
from linebot.tools import get_digits

# [NOTE!] : 這邊解法 from https://blog.csdn.net/kong_and_whit/article/details/104167178?utm_medium=distribute.pc_relevant_t0.none-task-blog-BlogCommendFromBaidu-1.not_use_machine_learn_pai&depth_1-utm_source=distribute.pc_relevant_t0.none-task-blog-BlogCommendFromBaidu-1.not_use_machine_learn_pai
#           另外 content root path 要改成 django 的 root (travelproject) , 而不是 Venv 的 root !!!
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "travelproject.settings")
django.setup()

from linebot.models import Hotel , Resturant , Station , Sightseeing , Place , Comment , Picture

DICT_PATH = 'C:/Users/h5904/PycharmProjects/TravelProject/travelproject/city data/Tainan/dict data/Tainan_all_objects_dict'

def save_pkl(path, data):
    with open(path, "wb") as pkl:
        pickle.dump(data, pkl)

def load_pkl(path):
    with open(path, "rb") as pkl:
        data = pickle.load(pkl)
    return data

def set_sql_data(type):

    Tainan_all_objects = load_pkl(DICT_PATH)
    stores_dict = Tainan_all_objects[type]

    for store_dict in stores_dict:
        hash_type[type].create_obj_by_dict(**store_dict) # create store objs

if __name__  == '__main__' :


    hash_type = {
        'resturant': Resturant,
        'train': Station,
        'hotel': Hotel,
        'beefsoup': Resturant,
        'EelNoodles': Resturant,
        'gruel': Resturant,
        'nightmarket': Sightseeing,
        'con': Resturant,
        'sightseeing': Sightseeing,
        'porkrice': Resturant
    }

    set_sql_data('hotel')

