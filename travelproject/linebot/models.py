from django.db import models
from django.contrib.postgres.fields import ArrayField

import numpy as np
from datetime import datetime

from linebot.async_scraper import async_get_hotel_information_by_date
from linebot.booking_scraper import get_detail_hotel_information
from linebot.string_comparing import find_common_word_2str
from linebot.tools import distance


# from ORM object to hotel object ...
# May be it can combine with Hotel class


class Place(models.Model):

    # basic property
    place_type = models.CharField(max_length=100)
    place_sub_type = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    lng = models.FloatField(default = 0)
    lat = models.FloatField(default = 0)
    rating = models.FloatField(default = 0)
    admin_area = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    place_id = models.TextField(blank=True)

    __hash__ = models.Model.__hash__  # [NOTE!] : https://github.com/AliLozano/django-messages-extends/pull/26 to solve the problem of can't delete objects

    def __repr__(self):
        return f'[{self.place_type} / {self.place_sub_type}] : {self.name} is at [{self.lng},{self.lat}] in {self.admin_area} and rating {self.rating} in googlemap '

    def __eq__(self, other):
        return self.name == other.name and self.place_id == other.place_id # judge 2 places by comparing their name and place-id

    class meta:
        abstract = True

class Resturant(Place):

    @classmethod
    def create_obj_by_dict(cls, **store_dict):
        # basic attribute
        obj = cls(**store_dict)
        obj.save() # update to database

        return obj

class Station(Place):

    @classmethod
    def create_obj_by_dict(cls, **store_dict):
        # basic attribute
        obj = cls(**store_dict)
        obj.save()  # update to database

        return obj

class Sightseeing(Place):

    @classmethod
    def create_obj_by_dict(cls, **store_dict):
        # basic attribute
        obj = cls(**store_dict)
        obj.save()  # update to database

        return obj

class Hotel(Place):

    # source property
    room_source = models.CharField(max_length=20, null=True, blank=True)
    source_name = models.CharField(max_length=100, null=True, blank=True)
    # detail property
    detail_href = models.TextField(null=True, blank=True)
    comment_num = models.IntegerField(default=0, null=True, blank=True)
    star = models.IntegerField(default=0, null=True, blank=True)
    source_rating = models.FloatField(default=0, null=True, blank=True)
    pic_link = models.TextField(null=True, blank=True)

    @classmethod
    def create_obj_by_dict(cls, **store_dict):

        # init not contain room_source information , need add it .

        if 'pics' in store_dict and 'comments' in store_dict:

            pics = store_dict.pop('pics')
            comments = store_dict.pop('comments')
            obj = cls(**store_dict)
            obj.save()

            for pic in pics:
                obj.picture.create(pics = pic)
            for comment in comments:
                obj.comment.create(comments = comment)

        else:
            obj = cls(**store_dict)
            obj.save()

        # create ORM objects
        # default no room_source information due to construction step arrangement.
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



        else:
            print(f"Can't find this hotel {self.name}'s information !")

        self.save() # saving the change to database


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
                    for pic_url  in pics:
                        self.picture.create(pic_url = pic_url)
                    for comment_content in comments:
                        self.comment.create(comment_content=comment_content)

                    # To get all foreign objects can use : Class.related_name_of_foreignkey.all()
                    # Webpage : https://carsonwah.github.io/15213187968523.html

                else:
                    print('[WARNING] Not contains more information !')

            elif self.room_source == 'agoda':
                pass

            elif self.room_source == 'Hotel.com':
                pass

        else:
            print('[WARNING] Need to get room_source and source_name !')


    def construct_instant_attr(self, date=None , day_range=2):

        if getattr(self, 'room_source', None) and getattr(self, 'source_name', None):

            # Instant property (from booking or agoda ..)
            if self.room_source == 'booking':

                if not date:
                    raise NameError('Need to assign date ! ')

                # if the day in range is before today , re-range day_range
                if datetime(date) - datetime.timedelta(days=day_range) < datetime.now():
                    day_range = datetime(date) - datetime.now()

                self.date = date
                # get hotel information async to increase scrape speed , rtype : list of dicts : [{} , {} ... ]
                instant_inform = async_get_hotel_information_by_date(target_day=self.date,
                                                                     hotel_name=self.source_name,
                                                                     destination_admin=self.admin_area,
                                                                     day_range=day_range,
                                                                     instant_information=True)

                self.instant_inform = {instant_dict['date']: instant_dict for instant_dict in
                                       instant_inform}  # store instant information (+/- 2 days) in dicts

                # 此處用在第一次建立 hotel objects 時所用

            elif self.room_source == 'agoda:':
                pass
            else:
                pass

        else:
            print('[WARNING] Need to get room_source and source_name !')

# comment and pics only for hotel datasheet
class Comment(models.Model):

    #https: // stackoverflow.com / questions / 53884140 / django - multi - table - inheritance - alternatives -
    #for -basic - data - model - pattern
    comments = models.TextField(blank=True)
    store = models.ForeignKey(Hotel , on_delete=models.CASCADE , related_name='comment')

class Picture(models.Model):

    pics = models.TextField(blank=True)
    store = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='picture')

class Array_2d(models.Model):

    name = models.CharField(max_length=20)
    array = ArrayField(
                        ArrayField(
                                    models.FloatField(default=0)
                                  )
                      )

    @classmethod
    def create_array_object(cls ,name , arr):

        # if it's np array , transform to list
        if type(arr) != list:
            arr = arr.tolist()

        return cls(name = name ,array = arr)

    def get_array(self):
        return self.array

    def get_np_array(self):
        return np.array(self.array)


class Array_3d(models.Model):

    name = models.CharField(max_length=20)
    array = ArrayField(
                        ArrayField(
                                    ArrayField(
                                            models.FloatField(default=0)
                                        )
                                  )
                      )

    @classmethod
    def create_array_object(cls ,name , arr):

        # if it's np array , transform to list
        if type(arr) != list:
            arr = arr.tolist()

        return cls(name = name ,array = arr)

    def get_array(self):
        return self.array

    def get_np_array(self):
        return np.array(self.array)

