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

def generate_list_button(generate_list , type_suffix , pre_postback_data):

    if not pre_postback_data:
        pre_postback_data = ''

    def helper(ele):

        content = {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": str(ele),
                        "data": f"{type_suffix}&{ele}_{pre_postback_data}" # EX : location&花蓮&
                    }
                 }

        return content

    content_number = [helper(ele) for ele in generate_list]
    #print('DEBUG : ' , content_number)

    return content_number


def button_template_generator(
                              temp_type ,
                              pre_postback_data = None,
                              **room_status_query
                              ):

    if temp_type == 'travel_location':

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
                        "contents": generate_list_button(['台南' , '宜蘭' , '花蓮'] , temp_type.split('&')[1]),
                        "flex": 0,
                        "spacing": "xs"
                    }
        }

    elif temp_type == 'travel_date':

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
                                    "data": "action=sell&itemid=2&mode=date",
                                    "max": "2022-02-01",
                                    "min": "2021-01-01"
                                }
                            }
                        ],
                        "flex": 0,
                        "spacing": "xs"
                    }
        }

    elif temp_type == 'travel_rooms':

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
                                                 type_suffix=temp_type.split('&')[1] ,
                                                 pre_postback_data=pre_postback_data),
                "flex": 0,
                "spacing": "xs"
            }
        }

    elif temp_type == 'travel_people':

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
                "contents": generate_list_button(list(range(1, 10)) , temp_type.split('&')[1]),  # default # options = 5
                "flex": 0,
                "spacing": "xs"
            }
        }

    elif temp_type == 'travel_yesOrno':

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
                "contents": generate_list_button(['要!','我有候選人了!'],temp_type.split('&')[1]),  # default options : Yes or No
            }
        }

    elif temp_type == 'travel_recommend':

        if not room_status_query:
            raise NameError('No args input for recommend template')

        # This property is coming from postback button in previous step!
        queried_date = room_status_query.get('queried_date', None)
        admin_area = room_status_query.get('admin_area', None)
        num_rooms = room_status_query.get('num_rooms', None)
        num_people = room_status_query.get('num_people', None)

        # Those property all got from selected hotels attributes
        place_name = room_status_query.get('place_name' , None)
        img_url = room_status_query.get('img_url', None)
        rating = room_status_query.get('rating', None)



        button = {
              "type": "bubble",

              "size": "micro",

              "hero": {
                            "type": "image",
                            "url": img_url ,
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
                                        "data": place_name + "&" + admin_area + "&" + queried_date + "&" + num_people + "&" + num_rooms
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

def carousel_template_generator(queried_date ,
                                place_names ,
                                img_urls ,
                                ratings ,
                                ):

    carousel_contents = {
        "type": "carousel",
          "contents": [button_template_generator(temp_type='travel_recommend' ,
                                                 queried_date=queried_date,
                                                 place_name=place_name,
                                                 img_url=img_url,
                                                 rating=rating) for place_name , img_url , rating in zip(place_names,
                                                                                                         img_urls,
                                                                                                         ratings)]


}
