from django.shortcuts import render
import configparser
import os
import random
import matplotlib.pyplot as plt
import pyimgur

from bot.async_scraper import async_get_search_result_by_resturant
from bot.models import *
from bot.recommend import find_best_hotels
from bot.constants import *
from bot.generate_template import button_template_generator , carousel_template_generator
from bot.string_comparing import find_common_word_2str
from bot.density_analysis import get_place_latlng_by_gmaps
from bot.object_filter import filter_store_by_criteria
from bot.google_map_scraper import  GoogleMap_Scraper , check_place_in_range
from bot.tools import lat_lng_to_x_y , x_y_to_lat_lng
from bot.plot import save_price_trend_img

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
    LocationMessage ,

    # Send messages
    TextSendMessage, # send text reply
    FlexSendMessage, # send flex-template reply
    LocationSendMessage, # send location map
    ImageSendMessage,

)

# TODO　list :
# 1. 抓取其他縣市的 data 進 SQL
# 2.

# Some params
NEARBY_CRITERIA = 500

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



# handle the following event
@handler.add(FollowEvent)
def handle_follow(event):

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=follow_message)
    )

# handle the location event
@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):

    try:
        client_obj = Line_client.objects.get(user_id=event.source.user_id,
                                             query_date=datetime.date.today())
    except:
        client_obj = Line_client.create_obj_by_dict(user_id = event.source.user_id,
                                                    query_date=datetime.date.today())
    type_header = client_obj.type_header


    if type_header == 'place_name_input':

        message = event.message
        latlng , address = [message.longitude, message.latitude] , message.address
        print(f'DEBUG in handle_location : {latlng}')
        in_range = check_place_in_range(latlng , client_obj.admin_area)

        if in_range:

            save_attr_to_database(type_header, client_obj, address)
            return_postback(event,
                            client_obj=client_obj,
                            type_header=type_header,
                            latlng=latlng)
        else:
            '''
             Not saving attrs here!
            '''
            # if not in admin_area range , re-send message.
            type_header = type_header_backward(client_obj)
            other_msg = f'您的給的位置不在 {client_obj.admin_area} 區域內喔! 請確認您的位置在{client_obj.admin_area}區域內~'
            return_message(event,
                           client_obj=client_obj,
                           type_header=type_header,
                           other_msg=other_msg)

    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='請重新搜尋~')
        )

# handle the text and sticker event
@handler.add(MessageEvent, message=[TextMessage , StickerMessage])
def handle_message(event):

    '''
        # function: handling the message event

        :param event: line-bot event object

        :return: None
    '''

    if isinstance(event.message, StickerMessage):
        msg = event.message.keywords[0] if event.message.keywords else 'None'
    else:
        msg = event.message.text  # parse messages from event object

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

                # get place lat lng directly , and check in admin_area range or not
                place_latlng = get_place_latlng_by_gmaps(msg)
                latlng = [place_latlng[0] , place_latlng[1]]
                in_range = check_place_in_range(latlng , client_obj.admin_area)

                if in_range:
                    save_attr_to_database(type_header, client_obj, msg)
                    return_postback(event,
                                    client_obj=client_obj,
                                    type_header=type_header)
                else:

                    '''
                     Not saving attrs here!
                    '''
                    # if not in admin_area range , re-send message.
                    type_header = type_header_backward(client_obj)
                    other_msg = f'您的給的位置不在 {client_obj.admin_area} 區域內喔! 請重新輸入位置~'
                    return_message(event,
                                   client_obj=client_obj,
                                   type_header=type_header,
                                   other_msg=other_msg)


            # in self-preparing 'hotel_name_input' stage , check the input name exist or not
            elif type_header == 'hotel_name_input' :

                # check if this hotel name exist in hotel list
                selected_hotel = get_similar_name_hotel(msg)

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

                    # if haven't found similar hotel , re-send message.
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

    :param event: line-bot event object
    :param client_obj: client object contained detail information of client itself.
    :param type_header: the type header stage now.
    :param other_msg: the additional message want to be mixed in message.

    :return: None

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
        contents = '請輸入你所在位置(例如:民宿,飯店,景點..)或地址~ ,或直接傳送您的地點~ , 完成後請靜待5~15秒鐘等待資料抓取~ (如沒回應 , 請點按"再查一次"的按鈕!)'

    elif next_type_header == 'hotel_name_input':
        contents = '請輸入你想住的飯店~ , 輸入完成後請靜待 5~8 秒鐘等待資料抓取~ (如沒回應 , 請再輸入一次!)'

    elif next_type_header == 'sightseeing':
        contents = '請輸入你想去的景點 ~ (如沒想去的地方 , 直接輸入"無") , 輸入完成後請靜待3~5秒鐘等待資料抓取~'

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


# handle the postback button event
@handler.add(PostbackEvent)
def handle_postback(event):

    '''
    # function: handling the postback event

    :param event: line-bot event object

    :return: None
    '''

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

        other_msg = greeting_message if type_header == 'entering_message' else ''
        save_attr_to_database(type_header, client_obj, None )  # saving data to database if data_key exist in object attr
        return_postback(event,
                        client_obj=client_obj,
                        type_header=type_header,
                        other_msg=other_msg)

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

            # TODO: 一個小 Bugs , 如果在重新查詢後的 place_name_input , 按到了先前查詢的Resturant結果,會直接往另一個 fork : datetime selection 方向去!


    # BREAK POINT 1. 'datetime' and 'place_name_input' , if 'FoodOrHotel' == "N"
    # BREAK POINT 2. 'silence' and 'hotel_name_input' , if NeedRecommendOrNot == "N"
    # POSTBACK -> MESSAGE : if 'food' type (next is 'sightseeing')
    # "fork" to return message
    elif (type_header == 'NeedRecommendOrNot' and pre_postback_data == "N") or \
         (type_header == 'FoodOrHotel' and pre_postback_data == "找美食") or \
         type_header == "food":

        save_attr_to_database(type_header , client_obj , pre_postback_data)
        return_message(event,
                       client_obj=client_obj,
                       type_header=type_header)


    elif type_header == 'recommend':

        save_attr_to_database(type_header, client_obj, pre_postback_data)

        if 'MapShow' in pre_postback_data:
            return_location(event,
                            client_obj=client_obj,
                            type_header=type_header,
                            pre_postback_data=pre_postback_data)
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

        if 'MapShow' in pre_postback_data:
            return_location(event,
                            client_obj=client_obj,
                            type_header=type_header,
                            pre_postback_data=pre_postback_data)

        # for returning tp re-search food
        elif 'ReturnPlaceNameInput' in pre_postback_data:

            type_header = type_header_backward(client_obj, target_type='FoodOrHotel')
            return_message(event,
                           client_obj=client_obj,
                           type_header=type_header)

        # for returning to find food or find hotel
        elif 'ReturnFoodOrHotel' in pre_postback_data:

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

        if 'MapShow' in pre_postback_data:

            return_location(event,
                            client_obj=client_obj,
                            type_header=type_header,
                            pre_postback_data=pre_postback_data)

        elif 'PlotPriceTrend' in pre_postback_data:

            # Using pyimgur :  https://ithelp.ithome.com.tw/questions/10193987

            return_PriceTrend(event,
                              client_obj,
                              type_header)

        # for returning to recommend list
        elif 'ReturnRecommend' in pre_postback_data:

            # if it's not recommend mode originally , keep going collecting user data.
            if 'recommend' not in client_obj.type_record:
                type_header = type_header_backward(client_obj, target_type='num_people')
            else:
                type_header = type_header_backward(client_obj, target_type='sightseeing')

            return_postback(event,
                            client_obj=client_obj,
                            type_header=type_header)

        # for returning to beginning of search
        elif 'ReturnSearch' in pre_postback_data:

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
    '''
    # function : return the message

    :param event: line-bot event object
    :param client_obj: client object contained detail information of client itself.
    :param type_header: the type header stage now.
    :param other_msg: the additional message want to be mixed in message.

    :return: None
    '''

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


        latlng = other_msg.get('latlng')
        if latlng:
            place_name_or_latlng = latlng
        else:
            place_name_or_latlng = client_obj.place_name_input

        # (已解決, 備忘): 這邊會發生LineBotAPI error !!! Root cause : 因 other_msg 不是 string , 故下面 send message 會出錯

        dict_list = get_nearby_resturant(RandomChoose = 4,
                                         admin_area = client_obj.admin_area,
                                         rating_threshold = 4.0,
                                         place_name_or_latlng = place_name_or_latlng)

        contents = carousel_template_generator(temp_type=next_type_header,
                                               dict_list=dict_list)

    # if next stage is "food_recommend_hotel" , use hotel name to find hotel object ;
    # then use date ,rooms and people as input to object.construct_instant_attr
    elif next_type_header == 'food_recommend_hotel':

        hotel_name = client_obj.recommend.split('_')[1]
        dict_list = get_nearby_resturant(RandomChoose = 4,
                                         rating_threshold = 4.0,
                                         hotel_name = hotel_name)

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
    if isinstance(other_msg , str):
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

    if type_header in ['recommend','food_recommend_place','food_recommend_hotel']:

        pre_postback_data = other_msg.get('pre_postback_data')
        place_name = pre_postback_data.split('_')[1]
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


# return Price-trend Image-message of hotel
def return_PriceTrend(event,
                      client_obj, # 可直接在 reply function 中取用 client 即時 data !
                      type_header,
                      **other_msg):

    config_imgur = configparser.ConfigParser()
    config_file = os.path.join(os.path.dirname(__file__),'config_imgur.ini')
    config_imgur.read(config_file)

    CLIENT_ID = config_imgur['secret']['client_id']
    CLIENT_SECRET = config_imgur['secret']['client_secret']

    if type_header == 'instant':

        dates , prices , room_recommends = [] , [] , []
        dict_list = get_hotel_instance(client_obj , long_range_trend=True)

        for dict in dict_list:

            dates.append(dict.get('queried_date'))
            price = '已售完!' if not dict.get('price') else dict.get('price')
            prices.append(price)
            room_recommends.append(dict.get('room_recommend'))

        return_message = ''
        for price , date , room_recommend in zip(prices, dates , room_recommends):
            if price == '已售完!':
                price_date = f'日期 : {date} , {price} '
            else:
                price_date =  f'{date}:{room_recommend} ,共{str(price)}元'
            return_message += price_date + '\n'

        '''
        queried_date = client_obj.queried_date
        hotel_name = client_obj.recommend if client_obj.recommend else client_obj.hotel_name_input
        img_path = save_price_trend_img(dates , prices ,hotel_name=hotel_name,queried_date=queried_date)
        im = pyimgur.Imgur(client_id=CLIENT_ID,client_secret=CLIENT_SECRET)
        uploaded_img = im.upload_image(img_path , title = 'Uploaded with PyImgur')
        img_URL = uploaded_img.link
        '''


    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
           text = return_message
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
    target_sightseeing = [client_obj.sightseeing] if client_obj.sightseeing not in ['無' , '沒有'] else []
    target_food = [client_obj.food] if client_obj.food != '沒特別想吃的' else []
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
    dict_list = []
    for hotel in select_hotels:

        hotel_pics= list(hotel.picture.all())
        hotel_pics = random.sample(hotel_pics , k=2)
        hotel_pics_url = [pic.pics for pic in hotel_pics]

        dict = hotel.__dict__
        dict.update({'hotel_pics_url':hotel_pics_url})
        dict_list.append(dict)

    return dict_list


def get_hotel_instance(client_obj, long_range_trend = False):

    if getattr(client_obj , 'recommend'):
        selected_name = getattr(client_obj , 'recommend')
        selected_name = selected_name.split('_')[1]

    elif getattr(client_obj , 'hotel_name_input'):
        selected_name = getattr(client_obj , 'hotel_name_input')

    else:
        raise ValueError('No fitting name of hotel!!')

    selected_hotel = Hotel.objects.get(source_name=selected_name) # get target hotel object
    queried_date = getattr(client_obj , 'queried_date')
    num_rooms = getattr(client_obj , 'num_rooms')
    num_people = getattr(client_obj , 'num_people')

    day_range = 7 if long_range_trend else 3

    instant_objs = selected_hotel.construct_instant_attr(queried_date = queried_date ,
                                                         day_range=day_range,
                                                         num_people = num_people ,
                                                         num_rooms = num_rooms)

    pic_link = getattr(selected_hotel , 'pic_link')

    dict_list = []

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
                         rating_threshold = GMAP_RATING_THRESHOLD ,
                         NEARBY_CRITERIA = NEARBY_CRITERIA,
                         admin_area = None ,
                         hotel_name = None ,
                         place_name_or_latlng = None):


    # get nearby resturants
    maps = GoogleMap_Scraper.init_gmaps() # initialize gmaps API
    if not hotel_name and not place_name_or_latlng:
        raise ValueError('No hotel or place assigned!')

    if hotel_name:

        nearby_resturants , select_hotel = get_nearby_resturant_search_result_by_hotel(hotel_name,
                                                                                       rating_threshold)
        place_x_y = [select_hotel.lng , select_hotel.lat]

    elif place_name_or_latlng:

        # if is not latlng(list type) , scrape lat lng from gmap api
        if not isinstance(place_name_or_latlng, list):

            place_x_y = get_place_latlng_by_gmaps(place_name_or_latlng , maps = maps)

        else:
            place_x_y = place_name_or_latlng

        if not place_x_y:
            raise ValueError("Not exist such place!!")

        nearby_resturants = get_nearby_resturant_search_result_by_place(place_x_y,
                                                                        rating_threshold,
                                                                        admin_area)

        print(f'DEBUG nearby_resturants  : {admin_area} , {[resturant.name for resturant in nearby_resturants]}')


    # if can't find any or insufficient number of nearby resturants , using gmaps place_nearby to compensate it.
    compensate_num = RandomChoose - len(nearby_resturants)
    if len(nearby_resturants) < RandomChoose:

        print(f'DEBUG in insufficient about {compensate_num} resturants !!!')

        place_latlng = x_y_to_lat_lng(place_x_y)
        while True and NEARBY_CRITERIA<1000000:

            print(f'DEBUG NEARBY_CRITERIA now : {NEARBY_CRITERIA}')
            result = maps.places_nearby(keyword='餐廳',
                                        location=place_latlng,
                                        radius=NEARBY_CRITERIA,
                                        language='zh-TW')  # get stores list nearby
            result = result['results']
            if len(result) >= 0 :
                break

            NEARBY_CRITERIA = 2*NEARBY_CRITERIA

        select_num = min(compensate_num , len(result)) # if the num of search result < num need to compensate , set select num equal to min of them

        for place_inform in random.sample( result , select_num ):

            # scrape near_by resturants and store into SQL
            store_obj = GoogleMap_Scraper.extract_and_store_place_inform_to_database(maps = maps,
                                                                                     place_inform = place_inform,
                                                                                     admin_area = admin_area,
                                                                                     place_type = 'resturant',
                                                                                     place_sub_type = 'resturant')

            if store_obj not in nearby_resturants:
                nearby_resturants.append(store_obj)

    else:
        nearby_resturants = random.sample( nearby_resturants , RandomChoose )

    print(f'DEBUG in nearby_resturants : {nearby_resturants}')

    # collecting the Google search result dicts
    dict_list_exist , dict_list_not_exist = [] , []
    # for existing search result  , get the data from database
    for resturant_obj in nearby_resturants:

        print(f'DEBUG in exist resturants name : {resturant_obj.name}')
        resturant_search_obj = resturant_obj.resturant_search.all()
        print(f'DEBUG in exist resturants search obj : {resturant_search_obj}')

        if resturant_search_obj:

            result = resturant_search_obj[0]
            res_dic = {'result_url' : getattr(result, 'result_url'),
                       'preview_pic_url' : getattr(result, 'preview_pic_url'),
                       'name': resturant_obj.name ,
                       'rating': resturant_obj.rating,
                       'position_xy': [resturant_obj.lng , resturant_obj.lat]
                        }

            dict_list_exist.append(res_dic)
    # TODO: 解決 remove nearby_resturant delete 會造成跳過某個 element 的 bug!!
    nearby_resturants = [resturant for resturant in nearby_resturants if resturant not in dict_list_exist ]
    print(f'DEBUG in not exist resturants : {nearby_resturants}')


    # for non-existing search result  , store url into Resturant_search objects to database.
    dict_list_not_exist += async_get_search_result_by_resturant(nearby_resturants) # async scrape web_preview of all restuant
    dict_list_not_exist = [dic for dic in dict_list_not_exist if dic] # exclude empty dict
    for dict in dict_list_not_exist:

        name = dict.get('name')
        result_url = dict.get('result_url')
        preview_pic_url = dict.get('preview_pic_url')

        resturant_obj = Resturant.objects.get(name=name)
        print(f'DEBUG in name : {name}')
        search_obj = Resturant_search.create_obj_by_dict(result_url=result_url,
                                                         preview_pic_url=preview_pic_url)
        resturant_obj.resturant_search.add(search_obj)  # construct foreign-key between resturant_obj & search_obj.


    # TODO : store the search result into database.

    # calculate the distance from hotel
    dict_list_all = dict_list_exist + dict_list_not_exist
    print(f'DEBUG in dict_list : {dict_list_all}')
    for dict in dict_list_all:

        resturant_x_y = dict.get('position_xy')
        distance_resturant = distance(place_x_y , resturant_x_y)
        dict.update({'distance' : distance_resturant})

        print(f'DEBUG in distance : {place_x_y},{resturant_x_y}')



    return dict_list_all


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

    return nearby_resturants , select_hotel

def get_nearby_resturant_search_result_by_place(place_x_y,
                                                rating_threshold,
                                                admin_area):



    All_resturants = Resturant.objects.filter(admin_area=admin_area)

    nearby_resturants = filter_store_by_criteria(All_resturants,
                                                center=place_x_y,
                                                criteria=2*NEARBY_CRITERIA,
                                                scan_shape='circle')

    nearby_resturants = [resturant for resturant in nearby_resturants
                         if resturant.rating >= rating_threshold and resturant.place_sub_type != 'con'] # filter by rating and not contains 'convenience stores'


    return nearby_resturants
