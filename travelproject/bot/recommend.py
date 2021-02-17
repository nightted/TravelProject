import time as t
import random

from bot.density_analysis import *
from bot.object_filter import filter_store_by_criteria
from bot.tools import set_env_attr , distance

set_env_attr()  # set env attrs TODO : 後續 deploy 要處理這邊的環境變數設置 !!!
from bot.models import *
from bot.constants import *


'''
This functions are for hotel recommendations by store density and demand of silence or sightseeing positions
'''

def find_hotel_by_points_and_rating( point ,
                                     admin_area ,
                                     search_radius = NEARBY_CRITERIA ,
                                     gmap_rating_threshold = GMAP_RATING_THRESHOLD,
                                     booking_rating_threshold = BOOKING_RATING_THRESHOLD):

    def threshold_judge(hotel):

        source_rating = getattr(hotel, 'source_rating', None)
        if not source_rating:
            return True if getattr(hotel, 'rating') >= gmap_rating_threshold else False

        else:
            return True if float(source_rating) >= booking_rating_threshold else False


    hotel_objects_data = Hotel.objects.filter(admin_area = admin_area) # get all hotels from that administrative area
    hotels = filter_store_by_criteria(hotel_objects_data,
                                      center=point,
                                      criteria=search_radius,
                                      scan_shape='circle')

    hotels = list(filter(threshold_judge, hotels)) if  hotels else None # filter by booking_rating

    return hotels


# remember to load density data first!
# (Done) : 這邊 **density input 形式可以在弄得簡潔一點 , 傳入 density "list" 就好 , 不需要 dict
def find_best_hotels(*density_objects ,
                     admin_area ,
                     silence_demand=False ,
                     target_sightseeing=None ,
                     target_food=None ,
                     num_to_find = 4 , # can't set too large . the while loop won't terminate XDD!
                     topN = 50 ,
                     gmap_rating_threshold = 4.0 ,
                     booking_rating_threshold = 8.0 ,
                     ):
    '''
    # function : to find the best hotels by several criteria

    :param density_objects: the type of density you want to consider in selection process
    :param admin_area: administrative name of the area
    :param silence_demand: if you want a silence place to sleep XD
    :param target_sightseeing: the sightseeing you want to visit
    :param target_food: the food you want to eat
    :param num_to_find: the number of hotel recommendations you want to get
    :param topN: the number of top score density points you want to get in selection process
    :param gmap_rating_threshold: gmap rating less than this won't be selected
    :param booking_rating_threshold: booking rating less than this won't be selected

    :return:
    '''
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
        for food in target_food:
            for key_food in hash_name_obj_density.keys():
                if find_common_word_2str(food, key_food)[0] >= 2:
                    select_food.append(key_food) # add food into list to calculate density
                    target_food.remove(food)


        select_food = list(set(select_food))
        if select_food:

            food_names = [ hash_name_obj_density[food] for food in select_food ] # get food names
            food_density_objects = [ Array_2d.objects.get(name = food_name) for food_name in food_names ]  # get food density objs
            density_objects = [*density_objects, *food_density_objects] # combine with input density

        #print(f'DEBUG find hotel : len of density : {len(density_objects)}')

        if len(target_food) > 0:

            target_sightseeing  = target_food + target_sightseeing if target_sightseeing else target_food # if some target food not found in  hash_name_obj_density , add it into target_sigtseeing list to further finding

    t2 = t.time()

    # get density peak by customer demand
    top_peaks = search_peak(*density_objects,
                            admin_area = admin_area,
                            silence_demand = silence_demand,
                            target_sightseeing = target_sightseeing,
                            topN = topN
                            )


    t3 = t.time()

    # get closest hotels around those peaks
    peaks = [location for location , _ in top_peaks] # get peaks
    #scores = [score for _ , score in top_peaks] # get scores of these peaks

    best_hotels , best_points , loop_times = [] , [] , 1
    while len(best_hotels) < num_to_find:

        select_point = random.sample( peaks , 1)[0] #(Done) random select 1 point form topN points ; selection weights from point score calculate before
        select_hotel = find_hotel_by_points_and_rating( select_point ,
                                                        admin_area ,
                                                        gmap_rating_threshold = gmap_rating_threshold ,
                                                        booking_rating_threshold = booking_rating_threshold)  # get the closest randomN hotels

        select_hotel = random.sample(select_hotel , 1)[0] if select_hotel else None # random select 1 hotels

        if select_hotel and select_hotel not in best_hotels:
            best_hotels.append(select_hotel)
            best_points.append(select_point)

        if loop_times > 300:

            # TODO : 可能造成都找不到 hotel 的狀況!
            print('Too many loop too run , take a rest!') # 防呆 XDD
            break

        loop_times += 1

    # peaks = [ [ [lng1,lat1] , score1 ] , [ [lng2,lat2] , score2 ] , ...]

    t4 = t.time()

    print( f"t1~t2 = {t2 - t1} , t2~t3 = {t3 - t2} , t3~t4 = {t4 - t3} ")

    return best_hotels, best_points


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
                                         target_sightseeing = ['赤崁樓'],
                                         target_food = ['肉燥飯'] ,
                                         topN = 50 ,
                                         num_to_find = 3 ,
                                         gmap_rating_threshold = 4.0,
                                         booking_rating_threshold = 8.0
                                         )

    for hotel in select_hotels:
        print(f'Select hotel : {hotel.name} ')
        for nearby_r in hotel.nearby_resturant.all():
            if nearby_r.place_sub_type != 'con' and nearby_r.place_sub_type == 'porkrice' and nearby_r.rating >= 4.0 :
                d_h = hotel.return_location()
                d_r = nearby_r.return_location()
                print(f'The food nearby : {nearby_r.name} , the rating is {nearby_r.rating} , the distance is {distance(d_h,d_r)}')
        print('\n')

    t3 = t.time()

    for hotel in select_hotels:

        # queried date format must be ['2021-02-10' , '2021-02-11']  rather than '2021-02-10' ?????
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
