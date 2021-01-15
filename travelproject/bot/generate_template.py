from bot.models import *

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

    text = {
             "type": "text",
             "text": str(rating),
             "size": font_size,
             "color": font_color,
             "margin": "md",
             "flex": 0
           }

    content_gold = [gold_star for i in range(int(rating))]
    content_gray = [gray_star for i in range(5-int(rating))]

    return content_gold + content_gray + text

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
                                    "data": f"action=sell&itemid=2&mode=date", # TODO date 怎抓!!!
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
                "contents": generate_list_button(generate_list=food,  # default options : Yes or No
                                                 temp_type=temp_type
                                                 )
            }
        }

    elif temp_type == 'sightseeing':
        pass

    elif temp_type == 'recommend':

        # Those property all got from selected hotels attributes
        if not kwargs:
            raise ValueError('No hotel atrributes assigned!')

        name = kwargs.get('name',None)
        source_rating = kwargs.get('source_rating',None)
        star = kwargs.get('star',None)
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
                                "text": name,
                                "weight": "bold",
                                "size": "sm",
                                "wrap": True
                              },
                              {
                                "type": "text",
                                "text": source_rating + '星級',
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
                                        "label": "快看看你選的日期房況!",
                                        # 這邊 postback data 是要找出 filtered Hotel instance ,
                                        # 並 call instance method : construct_instance_attr (args : queried_date , num_people , num_room) !
                                        "data": None,
                                    }
                                },
                                {
                                    "type": "button",
                                    "style": "link",
                                    "height": "sm",
                                    "action": {
                                        "type": "postback",
                                        "label": "附近有什麼好吃的咧?",
                                        "data": None
                                    }
                                },
                                {
                                    "type": "spacer",
                                    "size": "sm"
                                }
                            ],
                            "flex": 0
              }

        }

    elif temp_type == 'instance':

        # Those property all got from selected hotels attributes
        if not kwargs:
            raise ValueError('No hotel atrributes assigned!')

        price = kwargs.get('price',None)
        room_recommend = kwargs.get('room_recommend',None)
        room_remaining = kwargs.get('room_remaining',None)
        queried_date = kwargs.get('queried_date',None)
        instant_hrefs = kwargs.get('instant_hrefs',None)

        button = {
            "type": "bubble",

            "size": "micro",

            "hero": {
                "type": "image",
                "url": img_url,
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
                        "text": place_name,
                        "weight": "bold",
                        "size": "sm",
                        "wrap": True
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "contents": generate_rating_star(rating)
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
                            "label": "快看看你選的日期房況!",
                            # 這邊 postback data 是要找出 filtered Hotel instance ,
                            # 並 call instance method : construct_instance_attr (args : queried_date , num_people , num_room) !
                            "data": None,
                        }
                    },
                    {
                        "type": "button",
                        "style": "link",
                        "height": "sm",
                        "action": {
                            "type": "postback",
                            "label": "附近有什麼好吃的咧?",
                            "data": None
                        }
                    },
                    {
                        "type": "spacer",
                        "size": "sm"
                    }
                ],
                "flex": 0
            }

        }

    return button


def carousel_template_generator( temp_type ,
                                 dict_list,
                                ):
    '''
    這邊傳入 hotel objects or hotel_instance objects
    並轉換成 dicts ,

    dict_list are objects' dict!
    e.g. : [
        { name : XX , room_source : OO} ,
        { name : AA , room_source : BB} ,
        ...
    ]
    '''



    carousel_contents = {
        "type": "carousel",
        "contents": [button_template_generator(temp_type=temp_type ,
                                               **kwargs )
                     for kwargs in dict_list]


}
