from django.shortcuts import render
import time as t
import datetime

from bot.models import *
from bot.recommend import find_best_hotels
from bot.tools import read_key
from bot.constants import ACCESS_TOKEN_PATH , SECRET_PATH , center_of_city
from bot.generate_template import button_template_generator , carousel_template_generator

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from linebot import (
    LineBotApi, WebhookParser , WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from linebot.models import (

    MessageEvent, # normal message reply event
    PostbackEvent, # message reply event from PostbackTemplateAction

    # Receive message
    TextMessage ,
    StickerMessage ,

    # Send messages
    TextSendMessage, # send text reply
    TemplateSendMessage, # send template reply
    FlexSendMessage, # send flex-template reply

    # Template of message
    ButtonsTemplate, # reply template of button
    CarouselTemplate , # reply template of carousel
    ImageCarouselTemplate , # reply template of image carousel

    # Action in template
    MessageTemplateAction, # detail message action in template
    PostbackTemplateAction, # detail postback action in template
    DatetimePickerTemplateAction # detail datetime action in template
)

# Line bot settings
# TODO : set token and secret as config.ini and use ConfigParser to read
LINE_CHANNEL_ACCESS_TOKEN = read_key(ACCESS_TOKEN_PATH)
LINE_CHANNEL_SECRET = read_key(SECRET_PATH)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN) # set line bot api
handler = WebhookHandler(LINE_CHANNEL_SECRET) # set handler

# Default greeting message:
greeting_message = '歡迎使用旅遊推薦 APP ~' # greeting words

# Priority of stage process:
priority = ['entering_message' ,
            'admin_area' ,
            'queried_date' ,
            'num_rooms' ,
            'num_people' ,
            'NeedRecommendOrNot' ,
            'silence' ,
            'food' ,
            'sightseeing' ,
            'recommend' ,
            'instant'
            ] # indicate the priority of process ; and also assigns the template type in postback message
next_type_hash = {pre : after for pre , after  in zip(priority[:len(priority)-1] , priority[1:len(priority)])}
next_type_hash.update({'Hotel_name_input' : 'instant'}) # update for BREAK POINT 'NeedRecommendOrNot' fork.

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

def find_type_header(client_obj):

    for key, value in client_obj.__dict__.items():
        if not value:
            return key
    else:
        return None


@handler.add(MessageEvent, message=[TextMessage , StickerMessage])
def handle_message(event):

    message_accept_type = ['entering_message' ,
                           'sightseeing' ,
                           'Hotel_name_input']

    # got client object
    # In the beginning of entering apps ,
    # try to get existing Line_client ; if not exist , initial Line_client object
    try:
        client_obj = Line_client.objects.get(user_id=event.source.user_id,
                                             query_date=datetime.date.today())
    except:
        client_obj = Line_client.create_obj_by_dict(user_id = event.source.user_id,
                                                    query_date=datetime.date.today())


    # TODO :假設目前是要接收 postback button 回傳 ,但 client 不小心弄成 message 回傳 , 要如何導回 postback handle?
    # TODO :設置一個 accept_list , 假設 type_header 不在裡面 , 可先導回 return_postback 並 "倒退 type header" , 以重傳一次 postback button ?
    # TODO :但目前問題是 BREAK POINT 那邊進行 "倒退 type header" 會有些困難在 XDD

    # Got a message event back , and parse current type and data ; if 'NeedRecommendOrNot' , special handle
    if client_obj.NeedRecommendOrNot == "N" and client_obj.silence == None:
        type_header = 'Hotel_name_input'
    else:
        type_header = find_type_header(client_obj) # find the empty client attributes , it's actually the type_header now!

    # got messages
    msg = event.message.text #TODO: instance 這邊要怎傳給 postback ?

    # 這邊檢查避免 type 錯誤的狀況 (明明給 postback button , 卻輸入文字 message )
    if type_header in message_accept_type:

        # saving data to database if data_key exist in object attr
        if type_header in client_obj.__dict__:
            setattr(client_obj , type_header , msg )
            client_obj.save()

        # if type == entering_message or sightseeing or hotel name input , transfer to return postback
        if type_header in ['entering_message','sightseeing','Hotel_name_input']:
            return_postback(event ,
                            client_obj = client_obj ,
                            type_header = type_header)
        else:
            return_message(event ,
                           client_obj = client_obj ,
                           type_header = type_header  )
    else:
        # 倒退 type_header 一格, 重send data
        type_idx = priority.index(type_header)
        type_header = priority[type_idx-1] # return to previous type
        return_postback(event,
                        client_obj=client_obj,
                        type_header=type_header)

def return_message(event,
                   client_obj,
                   type_header
                   ):


    '''
      # NO need recommend , collecting HOTEL NAME (data like: 'HotelName_Y_6_3_2020-02-12_花蓮_')
      # and filter it from hotel objects  , queried_date
      # than use construct_instant_attr method,
      # to update room status days before and after queried_date.

      pass # message 輸入 hotel 並 scrape hotel instance information , 並弄成 dicts 丟進 dict_list 裡
      contents = carousel_template_generator(temp_type='instance',
                                             dict_list = None )
    '''
    contents = None
    # special handle for BREAK POINT "NeedRecommendOrNot"
    if type_header == 'NeedRecommendOrNot' and client_obj.getattr(type_header) == 'N':
        next_type_header = 'Hotel_name_input'
    else:
        next_type_header = next_type_hash.get(type_header)


    if not next_type_header:
        raise ValueError('No next type exist!!!')

    if next_type_header == 'Hotel_name_input':
        contents = '請輸入你想住的飯店~'

    elif next_type_header == 'sightseeing':
        contents = '請輸入你想去的景點~'

    if not contents:
        raise ValueError(" No content assign !! ")

    line_bot_api.reply_message(
        event.reply_token,
        [
            TextSendMessage(text=contents),
        ]
    )

    '''
    you can add another next_type_header judge here . 
    '''


@handler.add(PostbackEvent)
def handle_postback(event):

    # carousal :　https://github.com/xiaosean/Line_chatbot_tutorial/blob/master/push_tutorial.ipynb

    postback_accept_type = [
                            'admin_area' ,
                            'queried_date' ,
                            'num_rooms' ,
                            'num_people' ,
                            'NeedRecommendOrNot' ,
                            'silence' ,
                            'food' ,
                            'recommend' ,
                            'instant']

    # got client object
    client_obj = Line_client.objects.get(user_id=event.source.user_id,
                                         query_date=datetime.date.today())

    # Got a post event back , and parse the current type and data
    type_header = event.postback.data.split('&')[0]  # EX : 'admin' (type of request template)
    pre_postback_data = event.postback.data.split('&')[1]  # EX : '[安平古堡]_[牛肉湯]_Hot_Y_6_3_2020-02-12_花蓮_'

    # saving attr to database
    if type_header in postback_accept_type:

        if type_header in client_obj.__dict__:
            setattr(client_obj , type_header , pre_postback_data)
            client_obj.save()

        # if NeedRecommendOrNot == "N" or food type , transfer to return message
        if (type_header == 'NeedRecommendOrNot' and pre_postback_data == "N") or  type_header == "food" :
            return_message(event,
                           client_obj=client_obj,
                           type_header=type_header)

        else:
            return_postback(event, client_obj, type_header) # Do reply function

    else:
        # 倒退 type_header 一格, 重send data
        type_idx = priority.index(type_header)
        type_header = priority[type_idx - 1] # return to previous type
        return_message(event,
                       client_obj=client_obj,
                       type_header=type_header)

    print("DEBUG : ", 'OUT!!!!!!!!!!!!!!!!')


def return_postback(event ,
                    client_obj, # 可直接在 reply function 中取用 client 即時 data !
                    type_header ,
                    ):

    # pre_postback_data like: 'Y_6_3_2020-02-12_花蓮_'
    # special handle the CHECK POINT "NeedRecommendOrNot"

    contents = None
    next_type_header = next_type_hash.get(type_header, None)  # got next type template

    if not next_type_header:
        raise ValueError('No next type exist!!!')


    # if next stage "recommend" , use client data to call find_best_hotel() to find best 5 hotels
    if next_type_header == 'recommend':

        # next_type_header of "sightseeing" 會從這傳入
        dict_list = get_recommend_hotels(client_obj)# define scrape recommend hotels function!!!
        contents = carousel_template_generator(temp_type=next_type_header,
                                               dict_list=dict_list)

    # if next stage "instant" , use hotel name to find hotel object ;
    # then use date ,rooms and people as input to object.construct_instant_attr
    elif next_type_header == 'instant':

        # next_type_header of "recommend" or "hotel_name_input" 會從這傳入!!
        dict_list = get_hotel_instance(client_obj) # define scrape hotel instant function!!!
        contents = carousel_template_generator(temp_type=next_type_header,
                                               dict_list=dict_list)

    # if not at stage "recommend" or "instant", keep collecting more (silence , food , sightseeing) data for hotel recommendations.
    else:
        if next_type_header == 'food':

            # special handle for food template about food display.
            contents = button_template_generator(temp_type=next_type_header,
                                                 food=center_of_city[client_obj.admin_area]['popular_food']
                                                 )
        else:
            contents = button_template_generator(temp_type=next_type_header)


    if not contents:
        raise ValueError(" No content assign !! ")

    #print('DEBUG postback_reply: ', contents , 'DEBUG postback_reply: next_type_hash' ,type_header)

    line_bot_api.reply_message(
        event.reply_token,
        FlexSendMessage(
            alt_text='FlexTemplate',
            contents=contents,
        )
    )

# base method to get recommend hotels
def get_recommend_hotels(client_obj):

    admin_area = client_obj.admin_area
    target_sightseeing = client_obj.target_sightseeing
    target_food = client_obj.target_food

    d_rs = Array_2d.objects.get(admin_area=admin_area, name='resturant')
    d_cn = Array_2d.objects.get(admin_area=admin_area, name='con')
    d_h = Array_2d.objects.get(admin_area=admin_area, name='hotel')

    select_hotels, _ = find_best_hotels(d_rs, d_cn, d_h,
                                        admin_area=admin_area,
                                        silence_demand=False,
                                        target_sightseeing=target_sightseeing,
                                        target_food=target_food,
                                        topN=50,
                                        num_to_find=3,
                                        gmap_rating_threshold=4.0,
                                        booking_rating_threshold=8.0
                                        )

    dict_list = [hotel.__dict__ for hotel in select_hotels ]

    return dict_list


def get_hotel_instance(client_obj):

    for nearby_r in hotel.nearby_resturant.all():
        if nearby_r.place_sub_type != 'con' and nearby_r.place_sub_type == 'porkrice' and nearby_r.rating >= 4.0:
            d_h = hotel.return_location()
            d_r = nearby_r.return_location()
            print(
                f'The food nearby : {nearby_r.name} , the rating is {nearby_r.rating} , the distance is {distance(d_h, d_r)}')

    #print("DEBUG : ", rt_h)

    for idx, hotel in enumerate(select_hotels):

        ins_hs = []
        # queried date format must be ['2021-02-10' , '2021-02-11']  rather than '2021-02-10' ?????
        instant_objs = hotel.construct_instant_attr(queried_date=queried_date, day_range=2, num_rooms=num_rooms, num_people=num_people)

        for obj in instant_objs:
            ins_h = []
            ins_h += [str(obj.queried_date), '推薦房型 :', obj.room_recommend, obj.room_remainings, '價格(一晚) : ', str(obj.price)]
            ins_h = ' '.join(ins_h)
            ins_hs.append(ins_h)
        ins_hs = '\n'.join(ins_hs)

        rt_h[idx] = rt_h[idx] + ins_hs

    answer = '\n'.join(rt_h)

    return answer