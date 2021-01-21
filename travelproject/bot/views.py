from django.shortcuts import render
import time as t
import datetime

from bot.models import *
from bot.recommend import find_best_hotels
from bot.tools import read_key
from bot.constants import ACCESS_TOKEN_PATH , SECRET_PATH , center_of_city
from bot.generate_template import button_template_generator , carousel_template_generator
from bot.string_comparing import find_common_word_2str

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
next_type_hash.update({'hotel_name_input' : 'instant'}) # update for BREAK POINT 'NeedRecommendOrNot' fork.

# acceptable type define
message_accept_type = ['entering_message' ,
                       'sightseeing' ,
                       'hotel_name_input']
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

@handler.add(MessageEvent, message=[TextMessage , StickerMessage])
def handle_message(event):

    # got client object
    # In the beginning of entering apps ,
    # try to get existing Line_client ; if not exist , initial Line_client object
    # TODO　: 這邊要決定一個client obj 刪除時機的機制 , 不然會造成我今天查詢到一半掛機 , 再回來查 type_header 不會從頭來的窘境XD
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
    msg = event.message.text # parse messages from event object

    print('DEBUG handle_message type header: ', type_header)

    # 這邊處理一種誤傳 message (本來是 postback button)狀況
    # check the type is acceptable to message event; if not , it's belong to postback event
    if type_header in message_accept_type:

        # if type == entering_message or sightseeing or hotel name input , transfer to return postback
        if type_header in ['entering_message','sightseeing']:

            other_msg = greeting_message if type_header == 'entering_message' else {}

            save_attr_to_database(type_header, client_obj, msg) # saving data to database if data_key exist in object attr
            return_postback(event ,
                            client_obj = client_obj ,
                            type_header = type_header ,
                            other_msg = other_msg)

        elif type_header == 'hotel_name_input' :

            selected_hotel = get_similar_name_hotel(msg) # check if this hotel name exist in hotel list

            if selected_hotel:
                save_attr_to_database(type_header , client_obj , selected_hotel.source_name)
                return_postback(event,
                                client_obj=client_obj,
                                type_header=type_header)
            else:

                type_header = get_pre_type_header(type_header, client_obj)
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

        # TODO: 這邊有個 BUG XD , 假設現在是 'hotel_name_input' 後的 'instant' , 但這邊不小心輸入了 message , 就會造成 'instant' 倒回 'recommend'

        # return type_header for "1 stage" , re-send postback event
        type_header = get_pre_type_header(type_header, client_obj)
        return_postback(event,
                        client_obj=client_obj,
                        type_header=type_header)

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
    if type_header == 'NeedRecommendOrNot' and getattr(client_obj , type_header) == 'N':
        next_type_header = client_obj.type_header = 'hotel_name_input'
        client_obj.type_record.append('hotel_name_input') # record the "path" of type

    # special handle for BREAK POINT "recommend" ; stage type == 'recommend' but in message type , "fork" to 'food_recommend'
    # TODO : 這邊邏輯頗髒XD
    elif type_header == 'recommend':
        next_type_header = client_obj.type_header = 'food_recommend'
        client_obj.type_record.append('food_recommend')

    else:
        next_type_header = client_obj.type_header = next_type_hash.get(type_header)
        client_obj.type_record.append(next_type_hash.get(type_header))

    client_obj.save()



    print('DEBUG return_message type header and next_type_header: ', type_header , next_type_header)


    if not next_type_header:
        raise ValueError('No next type exist!!!')

    if next_type_header == 'hotel_name_input':
        contents = '請輸入你想住的飯店~ (如沒回應 , 請再輸入一次!)'

    elif next_type_header == 'food_recommend':
        pass # TODO : find near_by resturant by obj.recommend hotel and do google search finding blog about those food

    elif next_type_header == 'sightseeing':
        contents = '請輸入你想去的景點~'

    if not contents:
        raise ValueError(" No content assign !! ")


    reply_action = [TextSendMessage(text=contents)]
    if other_msg:
        for _ , msg in other_msg.items():
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

    # 這邊防止剛進來手殘按到之前的 button .
    if not client_obj.type_header and not client_obj.entering_message:
        client_obj.type_header = type_header = 'entering_message'
        client_obj.type_record.append('entering_message')
        pre_postback_data = None

    else:
        # Got a post event back , and parse the current type and data
        type_header = event.postback.data.split('&')[0]   # get type header from postback data ; NOTE THAT 這邊為了避免 postback to postback 誤觸情況
        pre_postback_data = event.postback.params['date'] if type_header == 'queried_date' else event.postback.data.split('&')[1]  # get data from postback data

    # 這邊處理兩種 postback button (本來是 message or postback button) 誤觸狀況 :
    # Firstly, check the type header from postback is == from client.obj
    if type_header == client_obj.type_header:

        # if NeedRecommendOrNot == "N" or food type , "fork" to return message
        if (type_header == 'NeedRecommendOrNot' and pre_postback_data == "N") or \
            type_header == "recommend" and 'FoodRecommend' in pre_postback_data or \
            type_header == "food":

            # 這邊如果是 'recommend' 下會有兩種狀況 ; 一種是要 recommend hotel ; 另一種是要 recommend food
            # 這兩種都是在 'recommend' 儲存 hotel source_name ,
            # 唯一差別是一種是 send postback , 一種是 send message
            save_attr_to_database(type_header , client_obj , pre_postback_data)
            return_message(event,
                           client_obj=client_obj,
                           type_header=type_header)

        else:
            save_attr_to_database(type_header, client_obj, pre_postback_data)
            return_postback(event,
                            client_obj=client_obj,
                            type_header=type_header) # Do reply function

    else:

        # TODO : 這邊有另一個 BUG XDD ; 如果 'hotel_name_input' 下 , 按到 postback button , 則倒回這邊 'hotel_name_input' 不在 priority list 裡!

        # Secondly , if not the same type between type header from postback and from client.obj
        # return type_header for "1 stage" , re-send postback(or message) event

        type_header = client_obj.type_header # let type_header equal to client_obj.type_header if these 2 are not the same type at this time
        type_header = get_pre_type_header(type_header, client_obj)

        # And then to check what type actually it is.
        if type_header in postback_accept_type:
            return_postback(event,
                           client_obj=client_obj,
                           type_header=type_header)
        else:
            return_message(event,
                           client_obj=client_obj,
                           type_header=type_header)



def return_postback(event,
                    client_obj, # 可直接在 reply function 中取用 client 即時 data !
                    type_header,
                    **other_msg
                    ):

    # pre_postback_data like: 'Y_6_3_2020-02-12_花蓮_'
    # special handle the CHECK POINT "NeedRecommendOrNot"

    contents = None

    next_type_header = client_obj.type_header = next_type_hash.get(type_header, None)  # got next type template
    client_obj.type_record.append(next_type_hash.get(type_header, None))
    client_obj.save() # save the update on type_header

    print('DEBUG return_postback type header and next_type_header: ', type_header ,  next_type_header)

    if not next_type_header:
        raise ValueError('No next type exist!!!')

    # if next stage "recommend" , use client data to call find_best_hotel() to find best 5 hotels
    if next_type_header == 'recommend':

        # next_type_header of "sightseeing" 會從這傳入

        dict_list = get_recommend_hotels(client_obj)
        contents = carousel_template_generator(temp_type=next_type_header,
                                               dict_list=dict_list)

    # if next stage "instant" , use hotel name to find hotel object ;
    # then use date ,rooms and people as input to object.construct_instant_attr
    elif next_type_header == 'instant':

        # next_type_header of "recommend" or "hotel_name_input" 會從這傳入!!
        # note that , need to pass "source_name" into get_hotel_instance !

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


    reply_action = [FlexSendMessage(alt_text='FlexTemplate',contents=contents)]
    if other_msg:
        for _, msg in other_msg.items():
            reply_action.insert(0 , TextSendMessage(text=msg)) # insert other msg in front of button reply

    line_bot_api.reply_message(
        event.reply_token,
        reply_action
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

    if getattr(client_obj , 'recommend'):
        selected_name = getattr(client_obj , 'recommend')

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
    for ins_obj in instant_objs:
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
        pass


def get_similar_name_hotel(selected_hotel):

    '''
    #function : find the hotel with similar name

    :param selected_hotel: the name of hotel want to search
    :return: the hotel with similar name to selected hotel
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


def get_pre_type_header(type_header , client_obj):

    '''
    # function: back to the previous stage of type

    :param type_header:  the stage of type now client in
    :param client_obj:  the client object
    :return: the previous stage of type
    '''

    client_obj.type_record.pop() # remove current type
    type_header = client_obj.type_header = client_obj.type_record[-1] # get last element of type record (previous type) after rm cur type as cur type
    client_obj.save() # save change

    return type_header
