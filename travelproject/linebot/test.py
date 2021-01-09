import time
import matplotlib.pyplot as plt

from linebot.density_analysis import *

set_env_attr()
from linebot.models import *

def test_hotel_available(day_range , hotel , num_people , num_rooms):

    price = []
    for d in range(10,31,2*day_range + 1):

        res = async_get_hotel_information_by_date( target_day = f'2021-01-{d}',
                                                 day_range = day_range ,
                                                 num_people = num_people ,
                                                 num_rooms = num_rooms ,
                                                 hotel_name = hotel,
                                                 destination_admin = '台南',
                                                 instant_information = True )

        for ele in sorted(res, reverse=False, key=lambda x: x['queried_date']):

            print(f" 日期 : {ele['queried_date']}  , 推薦房源 : {ele['room_recommend']} , {ele['room_remainings']} , 一晚 {ele['price']} TWD !")

            if ele['price']:
                price.append(ele['price'])
        time.sleep(5)

    plt.plot(price)
    plt.show()

    return res

def test_hotel_instant( test_len ):

    test_hotel = []
    all_hotels = Hotel.objects.all()

    for hotel in all_hotels:
        if hotel.room_source == 'booking':
            test_hotel.append(hotel)
        if len(test_hotel) > test_len :
            break

    for htl in test_hotel:
        print(f'now in hotel : {htl.name}')
        htl.construct_instant_attr(
                                    date='2021-01-10' ,
                                    day_range=2,
                                    num_rooms=1,
                                    num_people=2
                                  )


if __name__ == '__main__':

    '''loc_center = '新竹火車站'
    maps = init_gmaps()
    #res = maps.geocode(loc_center)[0]
    #location = res['geometry']['location']
    location = {'lat': 24.8015877, 'lng': 120.9715883}

    all = moving_store_scraper(
                                keyword = '火車站',
                                search_center = location,
                                admin_area = 'Hsinchu',
                                radius = 50,
                                ranging = 0,
                                next_page_token=None,
                                objects=None,
                                place_type='station',
                                place_sub_type='station',
                                mode="max_area"
                            )

    print("Finish Google search step!")

    for p in all:
        print(p.__dict__)'''


    '''parkings = Place.objects.filter(admin_area='Tainan', place_sub_type='parking')
    out , MAX_Rho, MAX_position = local_density(parkings , rating_dependent=False)
    density = out[0]
    print(density.shape)
    Array_2d.create_array_object(name='parking' , arr = density , admin_area='Tainan')'''


    print(Hotel.objects.all())


'''class Resturant(Place):
    nearby_hotel = models.ManyToManyField(Hotel, related_name='nearby_hotel')

    @classmethod
    def create_obj_by_dict(cls, **store_dict):
        # basic attribute

        admin_area = store_dict.get('admin_area')
        filter_store_by_criteria(Hotel.objects.filter(admin_area=admin_area))

        obj = cls(**store_dict)
        if obj not in cls.objects.all():
            obj.save()  # if not has same data in database , update it .
        return obj'''

