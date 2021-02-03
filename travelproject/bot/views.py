from django.shortcuts import render
import configparser
import os
import random

from bot.async_scraper import async_get_search_result_by_resturant
from bot.models import *
from bot.recommend import find_best_hotels
from bot.constants import center_of_city
from bot.generate_template import button_template_generator , carousel_template_generator
from bot.string_comparing import find_common_word_2str
from bot.density_analysis import get_place_latlng_by_gmaps
from bot.object_filter import filter_store_by_criteria

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from linebot import (
    LineBotApi, WebhookParser , WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from linebot.models import (

    MessageEvent, # message  event
    PostbackEvent, # postback event
    FollowEvent, # follow event

    # Receive message
    TextMessage ,
    StickerMessage ,

    # Send messages
    TextSendMessage, # send text reply
    FlexSendMessage, # send flex-template reply
    LocationSendMessage, # send location map

    # Template of message
    ButtonsTemplate, # reply template of button
    CarouselTemplate , # reply template of carousel
    ImageCarouselTemplate , # reply template of image carousel

    # Action in template
    MessageTemplateAction, # detail message action in template
    PostbackTemplateAction, # detail postback action in template
    DatetimePickerTemplateAction # detail datetime action in template
)

# TODO　list :
# 1. 抓取其他縣市的 data 進 SQL
# 2.


# Line bot settings
config = configparser.ConfigParser()
config_file = os.path.join(os.path.dirname(__file__), 'config.ini') # https://stackoverflow.com/questions/29426483/python3-configparser-keyerror-when-run-as-cronjob
config.read(config_file)

LINE_CHANNEL_ACCESS_TOKEN = config['secret']['channel_access_token']
LINE_CHANNEL_SECRET = config['secret']['channel_secret']
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN) # set line bot api
handler = WebhookHandler(LINE_CHANNEL_SECRET) # set handler

# Default greeting message:
follow_message = '歡迎使用旅遊推薦 APP ~ ,請任意輸入文字以開始搜尋 (要重新查詢可隨時輸入 "重新搜尋" !) '
greeting_message = '歡迎使用旅遊推薦 APP ~ (要重新查詢可隨時輸入 "重新搜尋" !)' # greeting words


# Priority of stage process:
priority = ['entering_message' ,
            'admin_area' ,
            'FoodOrHotel' ,
            'queried_date' ,
            'num_rooms' ,
            'num_people' ,
            'NeedRecommendOrNot' ,
            'silence' ,
            'food' ,
            'sightseeing' ,
            'recommend' ,
            ] # indicate the priority of process ; and also assigns the template type in postback message

next_type_hash = {pre : after for pre , after  in zip(priority[:len(priority)-1] , priority[1:len(priority)])}
next_type_hash.update({'hotel_name_input' : 'instant' ,
                       'place_name_input' : 'food_recommend_place' }) # update for BREAK POINT 'NeedRecommendOrNot' fork.

# acceptable type define
message_accept_type = ['entering_message' ,
                       'sightseeing' ,
                       'hotel_name_input' ,
                       'place_name_input' ,
                       'food_recommend_place']

postback_accept_type = ['admin_area' ,
                        'queried_date' ,
                        'FoodOrHotel' ,
                        'num_rooms' ,
                        'num_people' ,
                        'NeedRecommendOrNot' ,
                        'silence' ,
                        'food' ,
                        'recommend' ,
                        'food_recommend_hotel' ,
                        'instant']

@csrf_exempt
def callback(request):

    if request.method == 'POST':

        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')

        try:
            handler.handle( body , signature )

        except InvalidSignatureError:
            print("DEBUG : InvalidSignatureError!!!")
            return HttpResponseForbidden()
        except LineBotApiError:
            print("DEBUG : LineBotApiError!!!")
            return HttpResponseBadRequest()

        return HttpResponse()

    else:
        print("DEBUG : HttpResponseBadRequest!!!")
        return HttpResponseBadRequest()


# 簡略講一下這邊 function 運作模式 :
# 1. 首先 event 進來 server, handle_ function 會先 parse event message and data , 並將 data store 進 database ;
# 2. 接著判別是哪種 type 的 event , 並利用 reply_ function 選擇要回復的訊息 or 要回復的 template type , 進行回傳 client
# 3. 最後 client 接收到訊息 or template , 再進行回覆 server (loop back to 1.)
@handler.add(FollowEvent)
def handle_follow(event):

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=follow_message)
    )

@handler.add(MessageEvent, message=[TextMessage , StickerMessage])
def handle_message(event):

    # got client object
    # In the beginning of entering apps ,
    # try to get existing Line_client ; if not exist , initial Line_client object
    # TODO　: 這邊要決定一個client obj 刪除時機的機制 , 不然會造成我今天查詢到一半掛機 , 再回來查 type_header 不會從頭來的窘境XD
    # TODO : 應該可設置成, 十分鐘內要是沒查詢 , 就直接清空 line_client 的所有資料 (但 user_id 一樣留著 ,只清空 attrs)
    try:
        client_obj = Line_client.objects.get(user_id=event.source.user_id,
                                             query_date=datetime.date.today())
    except:
        client_obj = Line_client.create_obj_by_dict(user_id = event.source.user_id,
                                                    query_date=datetime.date.today())


    # get request event back ; if type_header and attr "entering_message" not exist , means it's just entering the apps.
    # so , set type_header as 'entering_message'
    if not client_obj.type_header and not client_obj.entering_message:
        client_obj.type_header = type_header = 'entering_message'
        client_obj.type_record.append('entering_message') # record the "path" of type

    else:
        type_header = client_obj.type_header # find the empty client attributes , it's actually the type_header now!


    print('DEBUG handle_message type header: ', type_header)


    msg = event.message.text # parse messages from event object
    if msg in ['重新搜尋','重新選擇','重選','重搜','重新']:

        # in every type stage , every time you key in "重新搜尋" or "re-search" ,
        # it will return to beginning of search

        '''
         Not saving attrs here!
        '''
        type_header = type_header_backward(client_obj , target_type='entering_message')
        other_msg = '請重新選擇您要去的縣市~'
        return_postback(event,
                        client_obj=client_obj,
                        type_header=type_header,
                        other_msg=other_msg)

    else:

        # 這邊處理一種誤傳 message (本來是 postback button 卻傳 message )狀況
        # check the type is acceptable to message event; if not , it's belong to postback event
        if type_header in message_accept_type:

            # if type == entering_message or sightseeing or hotel name input , transfer to return postback
            if type_header in ['entering_message' , 'sightseeing']:

                other_msg = greeting_message if type_header == 'entering_message' else ''

                save_attr_to_database(type_header, client_obj, msg) # saving data to database if data_key exist in object attr
                return_postback(event ,
                                client_obj = client_obj ,
                                type_header = type_header ,
                                other_msg = other_msg)


            # in self-preparing 'place_name_input' stage , save attr and transfer to return postback
            elif type_header == 'place_name_input' :

                # TODO : 這裡可多一個 place 是否在 admin area 內的判斷!
                place_latlng = get_place_latlng_by_gmaps(msg)
                lng , lat = place_latlng[0] , place_latlng[1]
                lat_range = center_of_city[client_obj.admin_area]['city_range']['lat']
                lng_range = center_of_city[client_obj.admin_area]['city_range']['lng']
                in_range = lng_range[0]<=lng<=lng_range[1] and lat_range[0]<=lat<=lat_range[1]

                if in_range:
                    save_attr_to_database(type_header, client_obj, msg)
                    return_postback(event,
                                    client_obj=client_obj,
                                    type_header=type_header)
                else:
                    '''
                     Not saving attrs here!
                    '''
                    type_header = type_header_backward(client_obj)
                    other_msg = f'您的給的位置不在 {client_obj.admin_area} 區域內喔! 請重新輸入位置~'
                    return_message(event,
                                   client_obj=client_obj,
                                   type_header=type_header,
                                   other_msg=other_msg)


            # in self-preparing 'hotel_name_input' stage , check the input name exist or not
            elif type_header == 'hotel_name_input' :

                selected_hotel = get_similar_name_hotel(msg) # check if this hotel name exist in hotel list

                if selected_hotel:

                    # to return "instant" postback next
                    save_attr_to_database(type_header , client_obj , selected_hotel.source_name)
                    return_postback(event,
                                    client_obj=client_obj,
                                    type_header=type_header)
                else:
                    '''
                     Not saving attrs here!
                    '''
                    type_header = type_header_backward(client_obj)
                    other_msg = '找不到您輸入的飯店喔 ,請確認名稱 ~ '
                    return_message(event,
                                   client_obj=client_obj,
                                   type_header=type_header,
                                   other_msg = other_msg)


            else:
                save_attr_to_database(type_header, client_obj, msg)
                return_message(event ,
                               client_obj = client_obj ,
                               type_header = type_header  )

        else:

            # 這邊處理一種誤傳 message (本來是 postback button)狀況
            # return type_header for "1 stage" , re-send postback event
            type_header = type_header_backward(client_obj)
            return_postback(event,
                            client_obj=client_obj,
                            type_header=type_header)

# return text message
def return_message(event,
                   client_obj,
                   type_header,
                   **other_msg
                   ):


    '''
    # function : return the message

    # next_type_header : the type will return to client side

    '''
    contents = None

    # special handle for BREAK POINT "NeedRecommendOrNot" ; if got "N" in 'NeedRecommendOrNot' stage , "fork" to 'hotel_name_input'

    if type_header == 'FoodOrHotel' and getattr(client_obj , type_header) == '找美食':
        next_type_header = client_obj.type_header = 'place_name_input'
        client_obj.type_record.append('place_name_input') # record the "path" of type

    elif type_header == 'NeedRecommendOrNot' and getattr(client_obj , type_header) == 'N':
        next_type_header = client_obj.type_header = 'hotel_name_input'
        client_obj.type_record.append('hotel_name_input') # record the "path" of type

    else:
        next_type_header = client_obj.type_header = next_type_hash.get(type_header)
        client_obj.type_record.append(next_type_hash.get(type_header))

    client_obj.save()



    print('DEBUG return_message next_type_header & client_obj.type_record ', next_type_header , client_obj.type_record)



    if not next_type_header:
        raise ValueError('No next type exist!!!')

    if next_type_header == 'place_name_input':
        contents = '請輸入你所在位置(例如:民宿,飯店,景點..)或地址~ , 輸入完成後請靜待5~8秒鐘等待資料抓取~ (如沒回應 , 請再輸入一次!)'

    elif next_type_header == 'hotel_name_input':
        contents = '請輸入你想住的飯店~ , 輸入完成後請靜待3~5秒鐘等待資料抓取~ (如沒回應 , 請再輸入一次!)'

    elif next_type_header == 'sightseeing':
        contents = '請輸入你想去的景點~ , 輸入完成後請靜待3~5秒鐘等待資料抓取~'

    if not contents:
        raise ValueError(" No content assign !! ")


    reply_action = [TextSendMessage(text=contents)]
    if other_msg:
        for _ , msg in other_msg.items():
            if msg:
                reply_action.insert(0, TextSendMessage(text=msg))  # insert other msg in front of button reply

    line_bot_api.reply_message(
        event.reply_token,
        reply_action
    )

    '''
    you can add another next_type_header judge here . 
    '''


@handler.add(PostbackEvent)
def handle_postback(event):

    # carousal :　https://github.com/xiaosean/Line_chatbot_tutorial/blob/master/push_tutorial.ipynb

    # got client object
    try:
        client_obj = Line_client.objects.get(user_id=event.source.user_id,
                                             query_date=datetime.date.today())
    except:
        client_obj = Line_client.create_obj_by_dict(user_id = event.source.user_id,
                                                    query_date=datetime.date.today())

    # TODO(怪怪?) : 這邊防止剛進來手殘按到之前的 button .
    if not client_obj.type_header and not client_obj.entering_message:
        client_obj.type_header = type_header = 'entering_message'
        client_obj.type_record.append('entering_message')
        pre_postback_data = None

    else:
        # Got a post event back , and parse the current type and data
        type_header = event.postback.data.split('&')[0]   # get type header from postback data ; NOTE THAT 這邊為了避免 postback to postback 誤觸情況 , 取 template type 來跟 client_obj.type_header 來做比對
        pre_postback_data = event.postback.params['date'] if type_header == 'queried_date' else event.postback.data.split('&')[1]  # get data from postback data


    # 這邊處理幾種 postback button 誤觸狀況
    # 1. 目前是要回 message , 卻誤觸更先前的 postback button
    # 2. 要按目前的 postback button , 卻誤觸更先前的 postback button
    # 3. 為1,2的延伸 , 倒回誤觸的 postback stage(見1,2解法)後 , 又誤觸了"誤觸前"原本應該要按的 postback button
    #    EX : 我原本在 recommend , 按到 num_rooms ; 那現在倒回 num_rooms 後 , 我又按到 recommend button XDD


    if type_header != client_obj.type_header:

        # 解決 1 ,2 的作法 (type header 在 client_obj.type_header 之前):
        # 直接倒退回誤觸的 stage (type header) , 重新get資訊.
        # 這麼做的好處蠻直觀 , 如果不甚滿意先前的選擇 , 可直覺地拉回去重選 ~
        if type_header in client_obj.type_record:
            _ = type_header_backward(client_obj , type_header)

        # 解決 3 的作法 (type header 在 client_obj.type_header 之後):
        # 這裡處理手法類似給 button 但 send message 的處置 => 於目前的stage(client_obj.type_header)直接倒回 1 stage 重 send .
        else:
            type_header = type_header_backward(client_obj)
            return_postback(event,
                            client_obj=client_obj,
                            type_header=type_header)



    # BREAK POINT 1. 'datetime' and 'place_name_input' , if 'FoodOrHotel' == "N"
    # BREAK POINT 2. 'silence' and 'hotel_name_input' , if NeedRecommendOrNot == "N"
    # POSTBACK -> MESSAGE : if 'food' type (next is 'sightseeing')
    # "fork" to return message
    if (type_header == 'NeedRecommendOrNot' and pre_postback_data == "N") or \
       (type_header == 'FoodOrHotel' and pre_postback_data == "找美食") or \
        type_header == "food":

        save_attr_to_database(type_header , client_obj , pre_postback_data)
        return_message(event,
                       client_obj=client_obj,
                       type_header=type_header)


    elif type_header == 'recommend':

        action_type = pre_postback_data.split('_')[0]  # extract action
        save_attr_to_database(type_header, client_obj, pre_postback_data)

        if action_type == 'MapShow':
            return_location(event,
                            client_obj=client_obj,
                            type_header=type_header)
        else:
            return_postback(event,
                            client_obj=client_obj,
                            type_header=type_header)


    # If it goes to the 'leaf' of the selection process ,
    # choose to return to 'more recommend' or 'beginning of search'

    elif type_header == 'food_recommend_place':

        '''
         Not saving attrs here!
        '''

        # for returning tp re-search food
        if 'return_PlaceNameInput' in pre_postback_data:

            type_header = type_header_backward(client_obj, target_type='FoodOrHotel')
            return_message(event,
                           client_obj=client_obj,
                           type_header=type_header)

        # for returning to find food or find hotel
        elif 'return_FoodOrHotel' in pre_postback_data:

            type_header = type_header_backward(client_obj, target_type='admin_area')
            other_msg = '請重新選擇您要找飯店還是找美食~'
            return_postback(event,
                            client_obj=client_obj,
                            type_header=type_header,
                            other_msg=other_msg)


    elif type_header in ['instant','food_recommend_hotel']:

        '''
         Not saving attrs here!
        '''

        # for returning to recommend list
        if 'return_recommend' in pre_postback_data:

            # if it's not recommend mode originally , keep going collecting user data.
            if 'recommend' not in client_obj.type_record:
                type_header = type_header_backward(client_obj, target_type='num_people')
            else:
                type_header = type_header_backward(client_obj, target_type='sightseeing')
            other_msg = ''

        # for returning to beginning of search
        elif 'return_search' in pre_postback_data:

            type_header = type_header_backward(client_obj, target_type='entering_message')
            other_msg = '請重新選擇您要去的縣市~'


        return_postback(event,
                        client_obj=client_obj,
                        type_header=type_header,
                        other_msg=other_msg)

    # else , directly return postback .
    else:

        # [Exception] because the BREAK POINT 'instant' and 'food_recommend_hotel' is both return the same postback
        # So need not to do further judgement in this place.

        save_attr_to_database(type_header, client_obj, pre_postback_data)
        return_postback(event,
                        client_obj=client_obj,
                        type_header=type_header) # Do reply function


# return postback (template) message
def return_postback(event,
                    client_obj, # 可直接在 reply function 中取用 client 即時 data !
                    type_header,
                    **other_msg
                    ):
    contents = None


    # special handle the BREAK POINT "instant" and "food_recommend_hotel"
    if type_header == 'recommend':

        recommend_data = client_obj.recommend
        if 'FoodRecommend' in recommend_data:
            next_type_header = client_obj.type_header = 'food_recommend_hotel'
            client_obj.type_record.append('food_recommend_hotel')
        elif 'HotelRecommend' in recommend_data:
            next_type_header = client_obj.type_header = 'instant'
            client_obj.type_record.append('instant')

    else:
        next_type_header = client_obj.type_header = next_type_hash.get(type_header, None)  # got next type template
        client_obj.type_record.append(next_type_hash.get(type_header, None))

    client_obj.save() # save the update on type_header


    print('DEBUG return_postback client_obj.type_record ', client_obj.type_record , client_obj.type_header)


    if not next_type_header:
        raise ValueError('No next type exist!!!')

    # if next stage "recommend" , use client data to call find_best_hotel() to find best 5 hotels
    if next_type_header == 'recommend':

        # next_type_header of "sightseeing" 會從這傳入
        dict_list = get_recommend_hotels(client_obj)
        contents = carousel_template_generator(temp_type=next_type_header,
                                               dict_list=dict_list)

    # if next stage is "food_recommend_place" , use place name to find resturant object ;
    elif next_type_header == 'food_recommend_place':

        place_name = client_obj.place_name_input
        dict_list = get_nearby_resturant(RandomChoose = 4,
                                         admin_area = client_obj.admin_area,
                                         rating_threshold = 4.0,
                                         place_name = place_name)

        contents = carousel_template_generator(temp_type=next_type_header,
                                               dict_list=dict_list)

    # if next stage is "food_recommend_hotel" , use hotel name to find hotel object ;
    # then use date ,rooms and people as input to object.construct_instant_attr
    elif next_type_header == 'food_recommend_hotel':

        hotel_name = client_obj.recommend.split('_')[1]
        dict_list = get_nearby_resturant_search_result_by_hotel(hotel_name)
        contents = carousel_template_generator(temp_type=next_type_header,
                                               dict_list=dict_list)

    # if next stage is "instant" , use hotel name to find hotel object ;
    # then use date ,rooms and people as input to object.construct_instant_attr
    elif next_type_header == 'instant':

        dict_list = get_hotel_instance(client_obj)
        contents = carousel_template_generator(temp_type=next_type_header,
                                               dict_list=dict_list)

    # if next stage is "food" , # special handle for food template about food display.
    elif next_type_header == 'food':

        contents = button_template_generator(temp_type=next_type_header,
                                             food=center_of_city[client_obj.admin_area]['popular_food']
                                             )

    # else , directly return template as contents.
    else:
        contents = button_template_generator(temp_type=next_type_header)


    if not contents:
        raise ValueError(" No content assign !! ")

    #print('DEBUG postback_reply: ', contents , 'DEBUG postback_reply: next_type_hash' ,type_header)


    reply_action = [FlexSendMessage(alt_text='FlexTemplate',contents=contents)]
    if other_msg:
        for _ , msg in other_msg.items():
            if msg:
                reply_action.insert(0 , TextSendMessage(text=msg)) # insert other msg in front of button reply

    line_bot_api.reply_message(
        event.reply_token,
        reply_action
    )

# return location message
def return_location(event,
                    client_obj, # 可直接在 reply function 中取用 client 即時 data !
                    type_header,
                    **other_msg):

    if type_header == 'recommend':

        place_name = client_obj.recommend.split('_')[1]
        lat , lng , address = get_latlng_address(place_name)


    line_bot_api.reply_message(
        event.reply_token,
        LocationSendMessage(
            title='Location',
            address=address,
            latitude=lat,
            longitude=lng
        )
    )



def get_latlng_address(place_name):

    place_object = Place.objects.filter(name = place_name)
    if not place_object:
        place_object = Hotel.objects.filter(source_name = place_name) # if hotel objects

    place_object = place_object[0]
    lat = getattr(place_object , 'lat')
    lng = getattr(place_object, 'lng')
    address = getattr(place_object, 'address')

    return lat , lng , address

# base method to get recommend hotels
def get_recommend_hotels(client_obj):

    admin_area = client_obj.admin_area
    target_sightseeing = client_obj.sightseeing
    target_food = client_obj.food
    silence_demand = True if client_obj.silence == 'Silence' else False

    d_rs = Array_2d.objects.get(admin_area=admin_area, name='resturant')
    d_cn = Array_2d.objects.get(admin_area=admin_area, name='con')
    d_h = Array_2d.objects.get(admin_area=admin_area, name='hotel')

    select_hotels, _ = find_best_hotels(d_rs, d_cn, d_h,
                                        admin_area=admin_area,
                                        silence_demand=silence_demand,
                                        target_sightseeing=target_sightseeing,
                                        target_food=target_food,
                                        topN=50,
                                        num_to_find=4,
                                        gmap_rating_threshold=4.0,
                                        booking_rating_threshold=8.0
                                        )

    dict_list = [hotel.__dict__ for hotel in select_hotels ]

    return dict_list


def get_hotel_instance(client_obj):

    if getattr(client_obj , 'recommend'):
        selected_name = getattr(client_obj , 'recommend')
        selected_name = selected_name.split('_')[1]

    elif getattr(client_obj , 'hotel_name_input'):
        selected_name = getattr(client_obj , 'hotel_name_input')

    else:
        raise ValueError('No fitting name of hotel!!')

    selected_hotel = Hotel.objects.get(source_name=selected_name)
    queried_date = getattr(client_obj , 'queried_date')
    num_rooms = getattr(client_obj , 'num_rooms')
    num_people = getattr(client_obj , 'num_people')

    instant_objs = selected_hotel.construct_instant_attr(queried_date = queried_date ,
                                                         num_people = num_people ,
                                                         num_rooms = num_rooms)
    pic_link = getattr(selected_hotel , 'pic_link') # TODO : 這邊注意會抓到沒 pic 的 non-booking hotel!

    dict_list = []
    #print([type(obj.queried_date) for obj in instant_objs])
    for ins_obj in sorted(instant_objs , key = lambda x : x.queried_date):
        ins_dict = ins_obj.__dict__
        ins_dict.update({'pic_link': pic_link})
        dict_list.append(ins_dict)

    #print(f" DEBUG dict_list  : {dict_list}")

    return dict_list


def save_attr_to_database(type_header, client_obj, data):

    #function : store the client_obj attr to database
    if type_header in client_obj.__dict__:
        setattr(client_obj, type_header, data)
        client_obj.save()
    else:
        raise ValueError(f'No such attribute : {type_header} exist in {type(client_obj)} !')


def get_similar_name_hotel(selected_hotel):

    '''
    #function : find the hotel with similar name

    :param selected_hotel: the name of hotel want to search
    :return: the hotel "objects" with similar name to selected hotel
    '''

    selected_name, max_length, max_char_hotel = selected_hotel, 0, None
    for hotel in Hotel.objects.all():

        # only get the hotel with room_source
        if hotel.room_source:

            max_len_similar, max_len_chars = find_common_word_2str(selected_name, hotel.name)
            if max_len_similar > max_length:
                max_length = max_len_similar
                max_char_hotel = hotel

    selected_hotel = max_char_hotel if max_length >=2 else None

    return selected_hotel


def type_header_backward(client_obj , target_type = None):

    '''
    # function: back to the previous stage of type

    :param client_obj:  the client object
    :param target_type : the type stage want to return
    :return: the previous stage of type
    '''

    # if not assign type header , default backward 1 stage to previous type
    if not target_type:

        client_obj.type_record.pop()  # remove current type
        type_header = client_obj.type_header = client_obj.type_record[-1]  # get last element of type record (previous type) after rm cur type as cur type
        client_obj.save()  # save change

    # if assign type , back to that type stage
    else:

        type_record = client_obj.type_record
        if target_type not in type_record:
            raise ValueError('Target type not in type record !')

        target_idx = type_record.index(target_type)
        type_record = type_record[:target_idx+1] # remove type after target type
        type_header = client_obj.type_header = type_record[-1] # get now type header

        client_obj.type_record = type_record
        client_obj.save() # save change

    return type_header


def get_nearby_resturant(RandomChoose ,
                         admin_area ,
                         rating_threshold = 4.0 ,
                         hotel_name = None ,
                         place_name = None , ):

    if not hotel_name and not place_name:
        raise ValueError('No hotel or place assigned!')

    if hotel_name:
        nearby_resturants = get_nearby_resturant_search_result_by_hotel(hotel_name,
                                                                        rating_threshold)
    elif place_name:
        nearby_resturants = get_nearby_resturant_search_result_by_place(place_name,
                                                                        rating_threshold,
                                                                        admin_area)

    if len(nearby_resturants) >= RandomChoose:
        select_resturant = random.choices(nearby_resturants , k = RandomChoose)
    else:
        select_resturant = nearby_resturants

    print(f'DEBUG select_resturant : {select_resturant}')

    if not select_resturant:
        return []

    dict_list = async_get_search_result_by_resturant(select_resturant)

    return dict_list


def get_nearby_resturant_search_result_by_hotel(hotel_name,
                                                rating_threshold):
    try:
        select_hotel = Hotel.objects.filter(source_name=hotel_name)
        select_hotel = select_hotel[0]  # only get one of the result
    except:
        raise NameError('No such hotel exist!')

    nearby_resturant = select_hotel.nearby_resturant.all()

    nearby_resturants = []
    for res_obj in nearby_resturant:
        if res_obj.rating > rating_threshold and \
                res_obj.place_sub_type != 'con' and \
                res_obj not in nearby_resturants:
            nearby_resturants.append(res_obj)

    return nearby_resturants

    # TODO : 此處有重複抓取的 BUGS !!!

def get_nearby_resturant_search_result_by_place(place_name,
                                                rating_threshold,
                                                admin_area):

    place_latlng = get_place_latlng_by_gmaps(place_name)
    print(f"DEBUG latlng : {place_latlng}")
    All_resturants = Resturant.objects.filter(admin_area=admin_area)

    nearby_resturants = filter_store_by_criteria(All_resturants,
                                                center=place_latlng,
                                                criteria=300,
                                                scan_shape='circle')

    nearby_resturants = [resturant for resturant in nearby_resturants
                         if resturant.rating >= rating_threshold and resturant.place_sub_type != 'con']

    return nearby_resturants
