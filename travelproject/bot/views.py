from django.shortcuts import render
import time as t

from bot.models import *
from bot.recommend import find_best_hotels
from bot.tools import read_key
from bot.constants import ACCESS_TOKEN_PATH , SECRET_PATH
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

# Default messages:
greeting_message = '歡迎使用旅遊推薦 APP ~'


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


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    print("IN event handler!!!!")
    if event.message.text:

        contents = button_template_generator(temp_type='travel_location')

        line_bot_api.reply_message(
            event.reply_token ,
            [
                TextSendMessage(text=greeting_message),
                FlexSendMessage(
                    alt_text='FlexTemplate',
                    contents=contents,
                )
            ]
        )


@handler.add(PostbackEvent)
def handle_postback(event):

    # TODO : transfer the event to postback_action.py
    # carousal :　https://github.com/xiaosean/Line_chatbot_tutorial/blob/master/push_tutorial.ipynb

    if event.postback.data.split('&')[0] == "location":

        # 這邊重點是我要把 , 前一層的 postback 參數 (ex : P&花蓮) ,
        # 傳入 button_template_generator 中 , 與 button 裡的 data combine.

        pre_postback_data = event.postback.data.split('&')[1] # EX : got '花蓮'
        contents = button_template_generator(temp_type='travel_date' ,
                                             pre_postback_data=pre_postback_data)

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(
                alt_text='FlexTemplate',
                contents=contents ,
            )
        )

    if event.postback.data.split('&')[0] == "date":
        pass

    if event.postback.data.split('&')[0] == "people":
        pass

    if event.postback.data.split('&')[0] == "yesOrno":
        pass

    if event.postback.data.split('&')[0] == "recommend":
        pass




    print("DEBUG : ", 'OUT!!!!!!!!!!!!!!!!')

    '''answer = get_recommend_hotels(
        queried_date='2021-02-14',
        admin_area='Tainan',
        target_sightseeing=['安平古堡'],
        target_food=['牛肉湯'],
        num_rooms=1,
        num_people=2
    )
'''



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