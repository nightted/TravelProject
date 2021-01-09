from django.db import models
from django.contrib.postgres.fields import ArrayField

import numpy as np
import datetime

from linebot.async_scraper import async_get_hotel_information_by_date
from linebot.booking_scraper import get_detail_hotel_information
from linebot.string_comparing import find_common_word_2str
from linebot.tools import distance , day_to_datetime , generate_day_range
from linebot.object_filter import filter_store_by_criteria


# from ORM object to hotel object ...
# May be it can combine with Hotel class

# BASIC class of places
class Place(models.Model):

    # basic property
    place_type = models.CharField(max_length=100)
    place_sub_type = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    lng = models.FloatField(default = 0)
    lat = models.FloatField(default = 0)
    rating = models.FloatField(default = 0)
    admin_area = models.CharField(max_length=100)
    address = models.TextField(null=True , blank=True , default=None )
    place_id = models.TextField(blank=True)

    __hash__ = models.Model.__hash__  # [NOTE!] : https://github.com/AliLozano/django-messages-extends/pull/26 to solve the problem of can't delete objects

    def __repr__(self):
        return f'[{self.place_type} / {self.place_sub_type}] : {self.name} is at [{self.lng},{self.lat}] in {self.admin_area} and rating {self.rating} in googlemap '

    def __eq__(self, other):
        return self.name == other.name and self.place_id == other.place_id # judge 2 places by comparing their name and place-id



class Hotel(Place):

    # source property
    room_source = models.CharField(max_length=20, null=True ,blank=True ,default=None)
    source_name = models.CharField(max_length=100, null=True, blank=True ,default=None)
    # detail property
    detail_href = models.TextField(null=True, blank=True ,default=None)
    comment_num = models.IntegerField(null=True, blank=True ,default=None)
    star = models.IntegerField(null=True, blank=True ,default=None)
    source_rating = models.FloatField(null=True, blank=True ,default=None)
    pic_link = models.TextField(null=True, blank=True ,default=None)

    '''
    #create_obj_by dict function details: 
    
    condition 1 : Directly create objs through existing dicts (contain pics and comments attributes) 
    
    condition 2 : With google-map scraper function , directly create objects by adding "basic" property, 
    
                  other property including source and detail property set as None (NOT contain pics and comments attributes) 
    
    '''
    def return_location(self):
        return [self.lng , self.lat]

    @classmethod
    def create_obj_by_dict(cls, **store_dict):

        # condition 1
        if 'pics' in store_dict and 'comments' in store_dict:

            pics = store_dict.pop('pics')
            comments = store_dict.pop('comments')
            obj = cls(**store_dict)
            obj.save()

            for pic in pics:
                obj.picture.create(pics = pic)
            for comment in comments:
                obj.comment.create(comments = comment)

        # condition 2
        else:
            obj = cls(**store_dict)
            if obj not in cls.objects.all():
                obj.save() # if this object NOT in database , store it

        # return ORM object
        return obj


    def main_construct_step(self, distance_threshold=300.0):

        print(f'The google map name is : {self.name}')

        # First step : Name judgement (gmap name vs. booking name) by sending place_id or gmap name search request
        inform_dict, detail_inform_dict = get_detail_hotel_information(place_id=self.place_id,
                                                                       destination_admin=self.admin_area)

        if inform_dict and detail_inform_dict:

            name_booking = detail_inform_dict['name_booking']
            common_word_count, max_len_chars = find_common_word_2str(self.name, name_booking)
            name_judge = common_word_count >= 2

            '''
            if not name_judge:
              inform_dict , detail_inform_dict = get_detail_hotel_information(hotel_name = self.name , destination_admin = self.admin_area )
              name_booking = detail_inform_dict['name_booking']
              common_word_count , max_len_chars = find_common_word_2str(self.name , name_booking) 
              name_judge = common_word_count >= 2
            '''

            print(f'The booking search name is : {name_booking}')

            # Second step : distance judgement (by place id input and get latlng result)
            latlng_gmap, latlng_booking = [self.lng, self.lat], detail_inform_dict['latlng_booking']
            delta_distance = distance(latlng_gmap, latlng_booking)
            distance_judge = delta_distance < distance_threshold

            print(f'latlng_booking : {latlng_booking} , latlng_gmap : [{self.lng},{self.lat}] ')
            print(f'Distance = {delta_distance} meters')
            print(f'There is {common_word_count} same words {max_len_chars}')

            if name_judge and distance_judge:

                # "PASS" name comparison , construct static property !
                self.room_source = 'booking'
                self.source_name = name_booking
                self.construct_static_attr({**inform_dict, **detail_inform_dict})

                print(f'Booking contain this hotel : {name_booking}')


            else:
                # "NOT PASS" name comparison ,not construct static property here !
                print(f'This hotel {name_booking} is not the same hotel as {self.name}!')

            print('\n')
        else:
            print(f"Can't find this hotel {self.name}'s information !")




    def construct_static_attr(self, store_dict):
        # Detail property (from booking or agoda ..)
        if getattr(self, 'room_source', None) and getattr(self, 'source_name', None):  # check room source exsit

            if self.room_source == 'booking':

                # update static data
                if 'href' and 'source_rating' in store_dict.keys():  # check one of the keys is in dict

                    self.detail_href = store_dict['href']
                    self.comment_num = store_dict['comment_num']
                    self.star = store_dict['stars']
                    self.pic_link = store_dict['pic_link']
                    self.source_rating = store_dict['source_rating']

                    # create foreign key objects for comments and pics
                    pics = store_dict['pics']  # from inner pages , list of pic urls
                    comments = store_dict['comments']  # from inner pages , list of comments
                    for pic  in pics:
                        self.picture.create(pics=pic)
                    for comment in comments:
                        self.comment.create(comments=comment)

                    # To get all foreign objects can use : Class.related_name_of_foreignkey.all()
                    # Webpage : https://carsonwah.github.io/15213187968523.html

                else:
                    print('[WARNING] Not contains more information !')

            elif self.room_source == 'agoda':
                pass

            elif self.room_source == 'Hotel.com':
                pass

            self.save()  # saving the change to database

        else:
            print('[WARNING] Need to get room_source and source_name !')


    def construct_instant_attr(self,
                               queried_date,
                               day_range=2 ,
                               num_people=2 ,
                               num_rooms=1
                               ):
        """
        # function : construct instant information of hotels

        :param date: e.g. "2021-03-25"
        :param day_range:  range of +-day from target day to search
        :param num_people:  number of people to book
        :param num_rooms:  number of rooms to book

        :return: None , directly save data in SQL
        """

        # (Done): 記得要寫 , 要是 instant inforamtion 已存在SQL裡 (例如 queried date 同一天) , 則直接用 SQL data ,不必再抓取

        if getattr(self, 'room_source', None) and getattr(self, 'source_name', None):

            # Instant property (from booking or agoda ..)
            if self.room_source == 'booking':

                if not queried_date:
                    raise NameError('Need to assign date ! ')

                # if the day in range is before today , re-range day_range
                if day_to_datetime(queried_date , format='datetime') - datetime.timedelta(days=day_range) < datetime.datetime.now():
                    day_range = (day_to_datetime(queried_date , format='datetime') - datetime.now()).days

                # try to access exist instant data from SQL
                exist_objs , unfinished_queried_date  = [] , []
                for day in generate_day_range(queried_date , day_range):

                    try:
                        exist_objs.append( Hotel_Instance.objects.get(
                                                                        query_date = datetime.date.today(),
                                                                        queried_date = day,
                                                                        hotel_id = self.pk
                                                                     )
                                          )

                        #print(f' Hotel {self.name} instant obj exist in the date : {day}!')
                    except:
                        #print(f'Hotel {self.name} instant obj not exist in the date : {day}!')
                        unfinished_queried_date.append(day)

                # if SQL not found instant data in some queried dates  , scrape it .
                if unfinished_queried_date:

                    # get hotel information async to increase scrape speed , rtype : list of dicts : [{} , {} ... ]
                    instant_inform = async_get_hotel_information_by_date(
                                                                         target_days = unfinished_queried_date ,
                                                                         num_people = num_people ,
                                                                         num_rooms = num_rooms ,
                                                                         hotel_name = self.source_name ,
                                                                         instant_information=True ,
                                                                         destination_admin = self.admin_area ,
                                                                         )
                    #print(instant_inform)
                    un_exist_objs = []
                    for instant_dict in instant_inform:

                        instant_dict.update({'num_rooms' : num_rooms})
                        instant_obj = Hotel_Instance.create_objects(**instant_dict , hotel = self) # (Done , due to datetime format and datefield auto_now_add) : BUG in Hotel_instance __eq__ function !!!
                        un_exist_objs.append(instant_obj)

                    instant_objs = exist_objs + un_exist_objs  # combine it !

                else:
                    instant_objs = exist_objs

                return instant_objs

            elif self.room_source == 'agoda:':
                pass
            else:
                pass
        else:
            print('[WARNING] Need to get room_source and source_name !')


# hotel_instance only for hotel datasheet
class Hotel_Instance(models.Model):

    # the client information(Auto-update)
    query_date = models.DateField(default=datetime.date.today) # the date the clients makes query action
    num_rooms = models.IntegerField(default=0)

    # the query information
    queried_date = models.DateField(default='') # the date of the hotel is queried
    instant_hrefs = models.TextField(null=True, blank=True, default=None)
    room_recommend = models.CharField(max_length=20)
    room_remainings = models.CharField(max_length=20)
    hot = models.CharField(max_length=100)
    price = models.IntegerField(null=True, blank=True ,default=None)

    #foreign-key
    hotel = models.ForeignKey(Hotel , on_delete= models.CASCADE , related_name='instance')

    @classmethod
    def create_objects(cls , **instant_dict):

        obj = cls(**instant_dict)

        if obj not in cls.objects.all():
            obj.save() # if not has same data in database , update it .
        return obj

    def __eq__(self , other):

        return self.hotel == other.hotel \
               and self.query_date == other.query_date \
               and day_to_datetime(self.queried_date) == other.queried_date \
               and self.price == other.price \
               and self.room_recommend == other.room_recommend


# comment and pics only for hotel datasheet
class Comment(models.Model):

    #https: // stackoverflow.com / questions / 53884140 / django - multi - table - inheritance - alternatives -
    #for -basic - data - model - pattern
    comments = models.TextField(blank=True)
    store = models.ForeignKey(Hotel , on_delete=models.CASCADE , related_name='comment')

class Picture(models.Model):

    pics = models.TextField(blank=True)
    store = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='picture')

class Resturant(Place):

    nearby_hotel = models.ManyToManyField(Hotel, related_name='nearby_hotel')

    # TODO : construct many to many field from resturants to hotels
    @classmethod
    def create_obj_by_dict(cls, **store_dict):
        # basic attribute
        admin_area = store_dict.get('admin_area')
        filter_store_by_criteria(Hotel.objects.filter(admin_area=admin_area))

        obj = cls(**store_dict)
        if obj not in cls.objects.all():
            obj.save()  # if not has same data in database , update it .
        return obj


class Station(Place):

    @classmethod
    def create_obj_by_dict(cls, **store_dict):
        # basic attribute
        obj = cls(**store_dict)
        if obj not in cls.objects.all():
            obj.save()  # if not has same data in database , update it .
        return obj


class Sightseeing(Place):

    @classmethod
    def create_obj_by_dict(cls, **store_dict):
        # basic attribute
        obj = cls(**store_dict)
        if obj not in cls.objects.all():
            obj.save()  # if not has same data in database , update it .
        return obj

class Array_2d(models.Model):

    admin_area = models.CharField(max_length=20 , default= '')
    name = models.CharField(max_length=20)
    array = ArrayField(
                        ArrayField(
                                    models.FloatField(default=0)
                                  )
                      )

    @classmethod
    def create_array_object(cls ,name , arr , admin_area):

        # if it's np array , transform to list
        if type(arr) != list:
            arr = arr.tolist()

        obj = cls.objects.create(name = name ,
                                 array = arr ,
                                 admin_area=admin_area)
        return obj

    def get_array(self):
        return self.array

    def get_np_array(self):
        return np.array(self.array)


class Array_3d(models.Model):

    admin_area = models.CharField(max_length=20 , default= '')
    name = models.CharField(max_length=20)
    array = ArrayField(
                        ArrayField(
                                    ArrayField(
                                            models.FloatField(default=0)
                                        )
                                  )
                      )

    @classmethod
    def create_array_object(cls ,name , arr , admin_area):

        # if it's np array , transform to list
        if type(arr) != list:
            arr = arr.tolist()

        obj = cls.objects.create(name=name,
                                 array=arr,
                                 admin_area=admin_area)
        return obj

    def get_array(self):
        return self.array

    def get_np_array(self):
        return np.array(self.array)

