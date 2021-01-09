import time as t
import random

from linebot.density_analysis import *
from linebot.object_filter import filter_store_by_criteria
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
# (Done) : 這邊 **density input 形式可以在弄得簡潔一點 , 傳入 density "list" 就好 , 不需要 dict
def find_best_hotels(*density_objects,
                     admin_area ,
                     silence_demand=False,
                     target_sightseeing=None,
                     target_food=None,
                     topN=50,
                     randomN=3,
                     gmap_rating_threshold=4.0,
                     booking_rating_threshold=8.0,
                     ):

    if not density_objects:
        raise NameError('No local density assign !')

    hash_name_obj_density = {
        '牛肉': 'beefsoup',
        '肉燥': 'porkrice',
        '鱔魚': 'eelnoodles',
        '鹹粥': 'gruel'
    }

    t1 = t.time()

    # if target food exist , get food key-word and add corresponding density
    if target_food:

        select_food = []
        for key_food in hash_name_obj_density.keys():
            for food in target_food:
                if find_common_word_2str(food, key_food)[0] >= 2:
                    select_food.append(key_food) # add food into list to calculate density
                    target_food.remove(food) # remove this food in original list

        select_food = list(set(select_food))
        if select_food:

            food_names = [ hash_name_obj_density[food] for food in select_food ] # get food names
            food_density_objects = [ Array_2d.objects.get(name = food_name) for food_name in food_names ]  # get food density objs
            density_objects = [*density_objects, *food_density_objects] # combine with input density

        if len(target_food) > 0:

            target_sightseeing  = target_food + target_sightseeing if target_sightseeing else target_food # if some target food not found in  hash_name_obj_density , add it into target_sigtseeing list to further finding

    t2 = t.time()

    # get density peak by customer demand
    top_peaks = search_peak(*density_objects,
                            admin_area = admin_area,
                            silence_demand = silence_demand,
                            target_sightseeing = target_sightseeing,
                            )

    t3 = t.time()

    # get closest hotels around those peaks
    topN = topN if topN < len(top_peaks) else len(top_peaks)  # choose topN peaks

    peaks = [location for location , _ in top_peaks[:topN]]
    scores = [score for _ , score in top_peaks[:topN]]

    select_points = random.choices( peaks , weights= scores , k = randomN) # TODO: 這邊似乎可用 peak score 當 random.choices 的 weighting ?
    select_hotels = find_hotel_by_points(select_points ,
                                         admin_area ,
                                         gmap_rating_threshold ,
                                         booking_rating_threshold)  # get the closest randomN hotels

    # peaks = [ [ [lng1,lat1] , score1 ] , [ [lng2,lat2] , score2 ] , ...]

    t4 = t.time()

    '''food_objects = [ Resturant.objects.filter(place_sub_type = food ,admin_area = admin_area) for food in food_names ]
    for select_hotel in select_hotels:

        near_objects = filter_store_by_criteria(food_objects, center=hotel.return_location(), criteria=500) # TODO : 隨機取三家店家 ?'''


    t5 = t.time()

    print( f"t1~t2 = {t2 - t1} , t2~t3 = {t3 - t2} , t3~t4 = {t4 - t3} , t4~t5 = {t5 - t4}" )

    return select_hotels, select_points


if __name__ == '__main__':

    admin_area = 'Tainan'

    t1 = t.time()

    d_rs = Array_2d.objects.get(admin_area = admin_area , name = 'resturant')
    d_cn = Array_2d.objects.get(admin_area = admin_area , name = 'con')
    d_h = Array_2d.objects.get(admin_area = admin_area , name = 'hotel')

    t2 = t.time()

    select_hotels, _ = find_best_hotels( d_rs, d_cn, d_h,
                                         admin_area = admin_area,
                                         silence_demand = False,
                                         target_sightseeing = None,
                                         target_food = ['文章牛肉湯' , '幹咧' , '操咧'],
                                         topN = 50,
                                         randomN = 3,
                                         gmap_rating_threshold = 4.0,
                                         booking_rating_threshold = 8.0
                                         )
    for hotel in select_hotels:
        print(f'Select hotel : {hotel.name}')

    t3 = t.time()

    for hotel in select_hotels:

        instant_objs = hotel.construct_instant_attr(queried_date='2021-02-10' , day_range=2 ,num_rooms=1 , num_people=2)
        for obj in instant_objs:
            print(hotel.source_name , obj.queried_date , '推薦房型 :　', obj.room_recommend , obj.room_remainings , '價格(一晚) : ', obj.price)

    t4 = t.time()

    print(f"t1~t2 = {t2 - t1} , t2~t3 = {t3 - t2} , t3~t4 = {t4 - t3}")



    '''h = Hotel.objects.get(name = 'Journey Hostel 掘旅')
    objs = h.construct_instant_attr(queried_date='2021-02-10',num_people=2,num_rooms=1 ,day_range=3)
    for obj in objs:
        print(obj.queried_date  ,obj.price)'''




    '''admin_area = 'Tainan'
    d_rs = Array_2d.objects.get(admin_area=admin_area, name='resturant').get_np_array()
    r = detect_peaks(d_rs)
    cnt_all = 0
    cnt_t = 0
    for x , row in enumerate(r):
        for y , col in enumerate(row):
            cnt_all+=1
            if col:
                cnt_t+=1
                print(x,y)
    print(cnt_t , cnt_all)'''
