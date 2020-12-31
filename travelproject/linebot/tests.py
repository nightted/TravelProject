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

def save_pkl(path, data):
    with open(path, "wb") as pkl:
        pickle.dump(data, pkl)

def load_pkl(path):
    with open(path, "rb") as pkl:
        data = pickle.load(pkl)
    return data

if __name__  == '__main__' :


    abs_file_paths = {}
    Tainan_all_objects = {}

    cur_path = 'C:/Users/h5904/PycharmProjects/TravelProject/travelproject/city data/Tainan/dict data/Tainan_all_objects_dict'
    Tainan_all_objects = load_pkl(cur_path)
    
    dicts = Tainan_all_objects['hotel']

    #for dict in dicts:
    #    print(dict)
    #    store_obj = Hotel.create_obj_by_dict(**dict)

    #for obj in Place.objects.all():
    #    if obj.place_type == 'Hotel':
    #        obj.delete()

    print(len(Hotel.objects.all()))
    print(len(Comment.objects.all()))
    print(len(Picture.objects.all()))

