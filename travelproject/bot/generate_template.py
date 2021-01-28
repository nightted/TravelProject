from bot.constants import *


def generate_rating_star(rating , font_size = None , font_color = None):

    font_size = "xs" if not font_size else font_size
    font_color = "#8c8c8c" if not font_color else font_color

    gold_star = {
                  "type": "icon",
                  "size": font_size,
                  "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
                }

    gray_star = {
                  "type": "icon",
                  "size": font_size,
                  "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gray_star_28.png"
                }

    true_rating = str(rating) + '星級' if rating else '無星等評比'
    text = {
             "type": "text",
             "text": true_rating,
             "size": font_size,
             "color": font_color,
             "margin": "md",
             "flex": 0
           }

    content_gold = [gold_star for i in range(int(rating))]
    content_gray = [gray_star for i in range(5-int(rating))]

    return content_gold + content_gray + [text]

def generate_list_button(generate_list ,
                         temp_type ,
                         #pre_postback_data = None
                         ):

    '''
    # function : generate single button for button_template_generator function

    :param generate_list: the buttons list want to generate
    :param temp_type: template type
    :param pre_postback_data: the postback data in previous template (relative to current type : temp_type)

    :return:
    '''

    '''if not pre_postback_data:
        pre_postback_data = '''''

    def helper(ele ,
               temp_type ,
               #pre_postback_data
               ):

        content = {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": str(ele),
                        # combine the pre_postback_data with the current button data
                        "data": f"{temp_type}&{ele}" # EX : location&花蓮_
                    }
                 }

        return content

    content_number = [helper(ele , temp_type) for ele in generate_list]
    #print('DEBUG : ' , content_number)

    return content_number


def button_template_generator(
                              temp_type ,
                              **kwargs
                              ):

    '''
    # function : handle type of template and combine the pre_postback_data into template data

    :param temp_type: the type of template want to return
    :param pre_postback_data: the postback data in previous template (relative to current type : temp_type)
    :param kwargs: for "recommend" step usage , store the hotel information.

    :return: template with buttons
    '''

    if temp_type == 'admin_area':

        button = {
                    "type": "bubble",
                    "hero": {
                        "type": "image",
                        "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_1_cafe.png",
                        "size": "full",
                        "aspectRatio": "320:213",
                        "aspectMode": "cover"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                          {
                            "type": "text",
                            "text": "想去哪個縣市玩呢?",
                            "size": "xxl",
                            "style": "italic",
                            "weight": "bold",
                            "decoration": "none"
                          }
                        ]
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": generate_list_button(generate_list=['Tainan' , 'Yilan' , 'Hualien'] ,
                                                         temp_type=temp_type
                                                         ),
                        "flex": 0,
                        "spacing": "xs"
                    }
        }

    elif temp_type == 'queried_date':

        button = {
                    "type": "bubble",
                    "hero": {
                        "type": "image",
                        "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_1_cafe.png",
                        "size": "full",
                        "aspectRatio": "320:213",
                        "aspectMode": "cover"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "幾號去玩呢?",
                                "size": "xxl",
                                "style": "italic",
                                "weight": "bold",
                                "decoration": "none"
                            }
                        ]
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "button",
                                "action": {
                                    "type": "datetimepicker",
                                    "label": "選個日期吧!",
                                    "mode": "date",
                                    "initial": "2021-02-01",
                                    "data": f"{temp_type}&None",
                                    "max": "2022-02-01",
                                    "min": "2021-01-01"
                                }
                            }
                        ],
                        "flex": 0,
                        "spacing": "xs"
                    }
        }

    elif temp_type == 'num_rooms':

        button = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_1_cafe.png",
                "size": "full",
                "aspectRatio": "320:213",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "要訂幾間房?",
                        "size": "xxl",
                        "style": "italic",
                        "weight": "bold",
                        "decoration": "none"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": generate_list_button(generate_list=list(range(1,6)) , # default # options = 5
                                                 temp_type=temp_type
                                                 ),
                "flex": 0,
                "spacing": "xs"
            }
        }

    elif temp_type == 'num_people':

        button = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_1_cafe.png",
                "size": "full",
                "aspectRatio": "320:213",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "幾個人要去?",
                        "size": "xxl",
                        "style": "italic",
                        "weight": "bold",
                        "decoration": "none"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": generate_list_button(generate_list=list(range(1, 10)) , # default # options = 10
                                                 temp_type=temp_type
                                                 ),
                "flex": 0,
                "spacing": "xs"
            }
        }

    elif temp_type == 'NeedRecommendOrNot':

        button = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_1_cafe.png",
                "size": "full",
                "aspectRatio": "320:213",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "要幫您推薦飯店&民宿嗎?",
                        "size": "lg",
                        "style": "italic",
                        "weight": "bold",
                        "decoration": "none"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "horizontal",
                "contents": generate_list_button(generate_list=['Y','N'] , # default options : Yes or No
                                                 temp_type=temp_type
                                                 )
            }
        }

    elif temp_type == 'silence':

        button = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_1_cafe.png",
                "size": "full",
                "aspectRatio": "320:213",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "喜歡鬧區還是安靜?",
                        "size": "lg",
                        "style": "italic",
                        "weight": "bold",
                        "decoration": "none"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "horizontal",
                "contents": generate_list_button(generate_list=['Hot','Silence'] , # default options : Yes or No
                                                 temp_type=temp_type
                                                 )
            }
        }

    elif temp_type == 'food':

        if 'food' in kwargs:
            food = kwargs.get('food', [] )

        if not food:
            raise ValueError('No foods in list!')

        button = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_1_cafe.png",
                "size": "full",
                "aspectRatio": "320:213",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "想吃甚麼食物?",
                        "size": "lg",
                        "style": "italic",
                        "weight": "bold",
                        "decoration": "none"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": generate_list_button(generate_list=food,  # default options : Yes or No
                                                 temp_type=temp_type) + [{
                                                                            "type": "button",
                                                                            "action": {
                                                                                "type": "postback",
                                                                                "label": '沒特別想吃的',
                                                                                # combine the pre_postback_data with the current button data
                                                                                "data": f"{temp_type}&None" # EX : location&花蓮_
                                                                            }
                                                                         }]


            }
        }

    elif temp_type == 'recommend':

        # Those property all got from selected hotels attributes
        if not kwargs:
            raise ValueError('No hotel atrributes assigned!')

        source_name = kwargs.get('source_name',None)
        source_rating = kwargs.get('source_rating') if kwargs.get('source_rating') else '無評分'
        star = kwargs.get('star') if kwargs.get('star') else 0
        pic_link = kwargs.get('pic_link',None)


        button = {
              "type": "bubble",

              "size": "micro",

              "hero": {
                            "type": "image",
                            "url": pic_link ,
                            "size": "full",
                            "aspectMode": "cover",
                            "aspectRatio": "320:213"
              },

              "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                              {
                                "type": "text",
                                "text": source_name,
                                "weight": "bold",
                                "size": "sm",
                                "wrap": True
                              },
                              {
                                "type": "text",
                                "text": 'booking 上評分 : ' + str(source_rating) ,
                                "weight": "bold",
                                "size": "sm",
                                "wrap": True
                              },
                              {
                                "type": "box",
                                "layout": "baseline",
                                "contents": generate_rating_star(star)
                              },
                            ],
                            "spacing": "sm",
                            "paddingAll": "13px"
              },

              "footer": {

                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "button",
                                    "style": "link",
                                    "height": "sm",
                                    "action": {
                                        "type": "postback",
                                        "label": "看當天房況!",
                                        # 這邊 postback data 是要找出 filtered Hotel instance ,
                                        # 並 call instance method : construct_instance_attr (args : queried_date , num_people , num_room) !
                                        "data": f"{temp_type}&HotelRecommend_{source_name}",
                                    }
                                },
                                {
                                    "type": "button",
                                    "style": "link",
                                    "height": "sm",
                                    "action": {
                                        "type": "postback",
                                        "label": "看附近美食?",
                                        "data": f"{temp_type}&FoodRecommend_{source_name}"  # special change the header name
                                    }
                                }
                            ],

                            "flex": 0
              }



        }

    elif temp_type == 'food_recommend':

        # Those property all got from selected hotels attributes
        if not kwargs:
            raise ValueError('No hotel atrributes assigned!')

        no_pic_url = 'https://lh3.googleusercontent.com/proxy/AgokJAXz_DxQLSWuEHpe5vHj0i1LzdoFJ_iBFjytNm708vp1plRL9LmAWLKV53TZbQz2dg87-9Hca0baV4fb1AgZ10xvVsj_lfLE'
        result_url = kwargs.get('result_url')
        preview_pic_url = kwargs.get('preview_pic_url')
        name = kwargs.get('name')
        rating = kwargs.get('rating')


        button = {
              "type": "bubble",

              "size": "micro",

              "hero": {
                            "type": "image",
                            "url": 'http://pic.pimg.tw/oxygen0301/1402290190-4016645192_m.jpg',
                            "size": "full",
                            "aspectMode": "cover",
                            "aspectRatio": "320:213"
              },

              "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                              {
                                "type": "text",
                                "text": name,
                                "weight": "bold",
                                "size": "sm",
                                "wrap": True
                              },
                              {
                                "type": "text",
                                "text": 'Google 上評分 : ' + str(rating) ,
                                "weight": "bold",
                                "size": "sm",
                                "wrap": True
                              }
                            ],
                            "spacing": "sm",
                            "paddingAll": "13px"
              },

              "footer": {

                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "button",
                                    "style": "link",
                                    "height": "sm",
                                    "action": {
                                        "type": "postback",
                                        "label": "看其他飯店?",
                                        # 這邊 postback data 是要找出 filtered Hotel instance ,
                                        # 並 call instance method : construct_instance_attr (args : queried_date , num_people , num_room) !
                                        "data": f"{temp_type}&return_recommend",
                                    }
                                },
                                {
                                    "type": "button",
                                    "style": "link",
                                    "height": "sm",
                                    "action": {
                                        "type": "uri",
                                        "label": "看食記!",
                                        "uri": result_url # special change the header name
                                    }
                                }
                            ],

                            "flex": 0
              }



        }

    elif temp_type == 'instant':

        # Those property all got from selected hotels attributes
        if not kwargs:
            raise ValueError('No hotel atrributes assigned!')

        price = kwargs.get('price',None)
        price = str(price) if price else "太夯了!!已售完!!"

        room_recommend = kwargs.get('room_recommend',None)
        room_remainings = kwargs.get('room_remainings',None)
        queried_date = kwargs.get('queried_date',None)

        instant_hrefs = kwargs.get('instant_hrefs',None) # TODO : 這邊還是有bug!
        instant_hrefs = BOOKING_URL + instant_hrefs if instant_hrefs else BASE_BOOKING_URL
        instant_hrefs = instant_hrefs[:-27] + instant_hrefs[-26:] # 去除 "\n" XD

        pic_link = kwargs.get('pic_link', None)

        print(f' DEBUG in template : {instant_hrefs}')

        button = {
            "type": "bubble",
            "size": "micro",
            "hero": {
                "type": "image",
                "url": pic_link,
                "size": "full",
                "aspectMode": "cover",
                "aspectRatio": "320:213"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": str(queried_date),
                        "weight": "bold",
                        "size": "sm",
                        "wrap": True
                    },
                    {
                        "type": "text",
                        "text": room_recommend,
                        "weight": "bold",
                        "size": "sm",
                        "wrap": True
                    }
                    ,
                    {
                        "type": "text",
                        "text": room_remainings,
                        "weight": "bold",
                        "size": "sm",
                        "wrap": True
                    },
                    {
                        "type": "text",
                        "text": "$" + str(price) + "TWD",
                        "weight": "bold",
                        "size": "sm",
                        "wrap": True
                    }
                ],
                "spacing": "sm",
                "paddingAll": "13px"
            },

            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [

                    {
                    "type": "button",
                    "style": "link",
                    "height": "sm",
                    "action": {
                        "type": "uri",
                        "label": "快上網站訂房!!!",
                        "uri": instant_hrefs
                        }

                    },

                    {
                        "type": "button",
                        "style": "link",
                        "height": "sm",
                        "action": {
                            "type": "postback",
                            "label": "想看看其他的推薦?",
                            "data": f'{temp_type}&return_recommend'
                        }
                    },
                    {
                        "type": "button",
                        "style": "link",
                        "height": "sm",
                        "action": {
                            "type": "postback",
                            "label": "重新搜尋?",
                            "data": f'{temp_type}&return_search'
                        }
                    }
                ],

                "flex": 0
            }

        }

    if not button:
        raise ValueError('No suitable template type exist!!')

    return button


def carousel_template_generator( temp_type ,
                                 dict_list,
                                ):
    '''
    dict_list are objects' dict!
    e.g. : [
        { name : XX , room_source : OO} ,
        { name : AA , room_source : BB} ,
        ...
    ]
    '''
    print(f"DEBUG : IN carousel_template_generator , temp_type = {temp_type}" )

    carousel_contents = {
        "type": "carousel",
        "contents": [button_template_generator(temp_type=temp_type , **kwargs )
                     for kwargs in dict_list]
    }

    return carousel_contents


