from density_analysis import *
import time as t
import random
from linebot.tools import set_env_attr

set_env_attr()  # set env attrs
from linebot.models import *



def find_hotel_by_points(points,
                         admin_area ,
                         gmap_rating_threshold=4.0,
                         booking_rating_threshold=8.0):
    def threshold_judge(hotel):

        source_rating = getattr(hotel, 'source_rating', None)
        if not source_rating:
            return True if getattr(hotel, 'rating') >= gmap_rating_threshold else False

        else:
            return True if float(source_rating) >= booking_rating_threshold else False

    hotel_objects_data = Hotel.objects.filter(admin_area = admin_area) # get all hotels from that administrative area

    select_hotels = []
    for point in points:
        hotels, criteria = [], 0
        while len(hotels) < 3 and criteria < 500:
            criteria += 100
            hotels = filter_store_by_criteria(hotel_objects_data,
                                              center=point,
                                              criteria=criteria,
                                              scan_shape='circle')
            hotels = list(filter(threshold_judge, hotels))  # filter booking_rating and star
        select_hotels += hotels

    return select_hotels


# remember to load density data first!

def find_best_hotels(admin_area ,
                     silence_demand=False,
                     target_sigtseeings=None,
                     target_food=None,
                     topN=50,
                     randomN=3,
                     gmap_rating_threshold=4.0,
                     booking_rating_threshold=8.0,
                     **densitys):
    if not densitys:
        raise NameError('No local density assign !')

    hash_name_obj_density = {
        '牛肉': 'density_bs',
        '肉燥': 'density_porkrice',
        '鱔魚': 'density_eel',
        '鹹粥': 'density_gru'
    }

    t1 = t.time()

    # if target food exist , get food key-word and add corresponding density
    if target_food:
        select_food = []
        for key_food in hash_name_obj_density.keys():
            for food in target_food:
                if find_common_word_2str(food, key_food)[0] >= 2:
                    select_food.append(key_food)

        select_food = list(set(select_food))
        food_dict = {hash_name_obj_density[food]: eval(hash_name_obj_density[food]) for food in
                     select_food}  # get food density dicts
        densitys = {**densitys, **food_dict}

    t2 = t.time()

    # get density peak by customer demand
    top_peaks = search_peak(admin_area = admin_area,
                            silence_demand=silence_demand,
                            target_sigtseeings=target_sigtseeings,
                            **densitys)

    # get closest hotels around those peaks
    topN = topN if topN < len(top_peaks) else len(top_peaks)  # choose topN peaks
    select_idx = random.sample(range(topN), randomN)
    select_points = [top_peaks[idx] for idx in select_idx]  # ramdom choose randomN points in topN peaks
    select_hotels = find_hotel_by_points(select_points ,
                                         admin_area ,
                                         gmap_rating_threshold ,
                                         booking_rating_threshold)  # get the closest randomN hotels

    t3 = t.time()
    print(f"t1~t2 = {t2 - t1} , t2~t3 = {t3 - t2}")

    return select_hotels, select_points