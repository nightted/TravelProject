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
    TextMessage,

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

# Default params:
greeting_message = '歡迎使用旅遊推薦 APP ~' # greeting words
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

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    msg = event.message.text # got message first
    # In the beginning of entering apps ,
    # try to get existing Line_client ; if not exist , initial Line_client object
    try:
        client_obj = Line_client.objects.get(user_id=event.source.user_id,
                                             query_date=datetime.date.today())
    except:
        client_obj = Line_client.create_obj_by_dict(user_id = event.source.user_id,
                                                    query_date=datetime.date.today())

    # TODO: BUG HERE , 要是不小心在途中輸入文字內容 , 就會抓到先前已存在的 Line_client object , 進而造成此處 type_header 錯位 !!
    type_header = find_type_header(client_obj) # find the empty client attributes , it's actually the type_header now!


    print('DEBUG : ' , type_header)
    setattr(client_obj , type_header , msg )
    client_obj.save()

    if type_header == 'entering_message':
        return_postback(event ,
                        client_obj = client_obj ,
                        type_header = type_header)

    return_message(event ,
                   client_obj = client_obj ,
                   type_header = type_header  )

    # STORAGE WORK IN THIS BLOCK !!!


def return_message(event,
                  client_obj,
                  type_header
                  ):

    # transform from type "food" -> type "sightseeing" , need to transfer to message instead of postback type return
    next_type_header = next_type_hash.get(type_header)
    if next_type_header == 'sightseeing':
        contents = '請輸入你想去的景點~'

    else:
        raise ValueError("No content assigned!!")

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

    # Got a post event back , and parse the postback template type and data
    type_header = event.postback.data.split('&')[0] # EX : 'location' (previous type of request template)
    pre_postback_data = event.postback.data.split('&')[1]  # EX : '花蓮_' (previous type postback_data )

    # got client object
    client_obj = Line_client.objects.get(user_id=event.source.user_id,
                                         query_date=datetime.date.today())
    # pre_postback_data like: '[安平古堡]_[牛肉湯]_Hot_Y_6_3_2020-02-12_花蓮_'

    # This block for LOCATION update
    if type_header == "admin_area":

        print("DEBUG : IN admin_area!!!!")
        setattr(client_obj , type_header , pre_postback_data)

    # This block for DATE update
    elif type_header == "queried_date":
        setattr(client_obj , type_header , pre_postback_data)

    # This block for ROOMS update
    elif type_header == "num_rooms":
        setattr(client_obj , type_header , pre_postback_data)

    # This block for PEOPLE update
    elif type_header == "num_people":
        setattr(client_obj , type_header , pre_postback_data)

    # This block for NeedRecommendOrNot update
    elif type_header == "NeedRecommendOrNot":
        setattr(client_obj , type_header , pre_postback_data)

    # This block for SILENCE update
    elif type_header == "silence":
        setattr(client_obj , type_header , pre_postback_data)

    # This block for FOOD update
    elif type_header == "food":
        setattr(client_obj , type_header , pre_postback_data)

        return_message(event,
                       client_obj = client_obj,
                       type_header = type_header)  # TODO (MARK)

    elif type_header == None:
        raise ValueError('No template type found!')

    client_obj.save()

    return_postback(event, client_obj, type_header) # Do reply function

    print("DEBUG : ", 'OUT!!!!!!!!!!!!!!!!')


def return_postback(event ,
                   client_obj, # 可直接在 reply function 中取用 client 即時 data !
                   type_header ,
                   ):

    # pre_postback_data like: 'Y_6_3_2020-02-12_花蓮_'
    # special handle the CHECK POINT "NeedRecommendOrNot"
    if type_header == 'NeedRecommendOrNot':
        NeedOrNot = client_obj.NeedRecommendOrNot
    else:
        NeedOrNot = None

    next_type_header = next_type_hash.get(type_header, None)  # got next type template
    if not next_type_header:
        raise ValueError('No next type exist!!!')

    if (not NeedOrNot or NeedOrNot == 'Y') and next_type_header != 'recommend':

        print("DEBUG : IN postback_reply!!!!")
        # if not at CHECK POINT "NeedRecommendOrNot" or truly need recommend and NOT at last 'recommend' layer;
        # if truly need recommendation ,
        # keep collecting more (silence , food , sightseeing) data for hotel recommendations.

        if next_type_header == 'food':
            contents = button_template_generator(temp_type=next_type_header,
                                                 food = center_of_city[client_obj.admin_area]['popular_food']
                                                 )
        else:
            contents = button_template_generator(temp_type=next_type_header)



    # 接下來這邊有兩種情況 type 會用到 carousel ;
    # 1. NeedRecommendOrNot : 直接輸入 hotel 名稱 , 找 5 instance 並用 carousel 回傳
    # 1. recommend : 直接輸入 hotel 名稱 , 找 5 instance 並用 carousel
    elif NeedOrNot == 'N':
        # NO need recommend , collecting HOTEL NAME (data like: 'HotelName_Y_6_3_2020-02-12_花蓮_')
        # and filter it from hotel objects  , queried_date
        # than use construct_instant_attr method,
        # to update room status days before and after queried_date.

        pass # message 輸入 hotel 並 scrape hotel instance information , 並弄成 dicts 丟進 dict_list 裡
        contents = carousel_template_generator(temp_type='instance',
                                               dict_list = None )

    elif next_type_header == 'recommend':

        pass # 用 client obj data 來 find 推薦 hotels , 並弄成 dicts 丟進 dict_list 裡
        contents = carousel_template_generator(temp_type=next_type_header,
                                               dict_list=None)

    else:
        raise ValueError(" No content assign !!")

    #print('DEBUG postback_reply: ', contents , 'DEBUG postback_reply: next_type_hash' ,type_header)
    print("DEBUG : IN postback_reply 222!!!!")
    line_bot_api.reply_message(
        event.reply_token,
        FlexSendMessage(
            alt_text='FlexTemplate',
            contents=contents,
        )
    )

# base method to get recommend hotels
def get_recommend_hotels(queried_date ,
                         admin_area ,
                         target_sightseeing ,
                         target_food ,
                         num_rooms ,
                         num_people
                         ):

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

    rt_h = []
    for hotel in select_hotels:
        print(f'Select hotel : {hotel.name} ')
        rt_h.append(hotel.name)

        '''for nearby_r in hotel.nearby_resturant.all():
            if nearby_r.place_sub_type != 'con' and nearby_r.place_sub_type == 'porkrice' and nearby_r.rating >= 4.0:
                d_h = hotel.return_location()
                d_r = nearby_r.return_location()
                print(
                    f'The food nearby : {nearby_r.name} , the rating is {nearby_r.rating} , the distance is {distance(d_h, d_r)}')'''

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