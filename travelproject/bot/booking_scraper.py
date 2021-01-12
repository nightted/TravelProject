import requests
from bs4 import BeautifulSoup
from datetime import datetime

from bot.tools import get_digits, get_date_string
from bot.constants import *

'''
#  This module search and scrape the information of hotels 
'''

#GLOBAL VARIABLE
HEADER_URL = "https://www.booking.com"

# send request and return soup result
def send_request(url, method='GET', data=None, headers=None):

    if method == "GET":
        res = requests.get(url, headers=headers)
    elif method == "POST":
        res = requests.post(url, data=data, headers=headers)
    else:
        print("[WARNING] No request method assigned!")

    res = res.content
    soup = BeautifulSoup(res, 'html.parser')

    return soup


# INPUT type scrape_time : ['2020-12-09' ,'2020-12-10']
def get_header_payload(scrape_time,
                       target_hotel=None,
                       place_id=None,
                       destination_admin=None ,
                       num_people = None ,
                       num_rooms = None
                       ):
    '''
    # function : get the headers and payload by scrape time

    target_hotel : if it's not assigned , scrape all "台南" hotel

    '''

    #HEADERS
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
        # can be generate fake agent ??
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'error_url': "https://www.booking.com/index.zh-tw.html?aid=1288258;label=metagha-link-mapresultsTW-hotel-2468603_dev-desktop_los-1_bw-18_dow-Monday_defdate-0_room-0_lang-zh_curr-TWD_gstadt-2_rateid-0_aud-0_cid-_gacid-6642513825_mcid-10_ppa-0_clrid-0_ad-1_gstkid-0;sid=ab79516c4eea1e96b378b9c2338022ce;sb_price_type=total;srpvid=f1b826d7eb680028&;",
        'content-security-policy-report-only': "report-uri https://csp-receiver.booking.com/csp_violation?type=report&tag=112&pid=040f2610ef80010a&e=UmFuZG9tSVYkc2RlIyh9YRdubXl3m7MIPItwv4TRRzARPrDvNuzlrbfIvmyYAyhkeKKOaHLiHXalz9oYwBjSNw&f=2&s=0; frame-ancestors 'none';",
        'Referer': 'https://www.booking.com/index.zh-tw.html?aid=376396&label=booking-name-yefrPbbyS%2AFIINHgyCnmNgS267725091255%3Apl%3Ata%3Ap1%3Ap22%2C563%2C000%3Aac%3Aap%3Aneg%3Afi%3Atikwd-65526620%3Alp1012818%3Ali%3Adec%3Adm%3Appccp%3DUmFuZG9tSVYkc2RlIyh9YfqnDqqG8nt1O4nYvDr1lms&sid=99dd5960476d5bf057cf94fe33e3deb6&srpvid=6d1e3723a19e0104&click_from_logo=1',
        'Host': 'www.booking.com',
        'Upgrade-Insecure-Requests': '1',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'max-age=0',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Connection': 'keep-alive'
    }



    # PAYLOAD DATA

    # location data
    if target_hotel:

        payload_destination = {
            'ss': target_hotel,
            'ssne': destination_admin,  # place you want to search (encode)
            'ssne_untouched': destination_admin,  # place you want to search (encode)
            'dest_type': 'hotel',
            'dest_id': None,  # place id you want to search
        }


    elif place_id:

        payload_destination = {
            'ss': destination_admin,
            'ssne': destination_admin,  # place you want to search (encode)
            'ssne_untouched': destination_admin,  # place you want to search (encode)
            'dest_type': 'region',
            'dest_id': None,  # place id you want to search
            'place_id': place_id
        }

    else:
        raise NameError('Need to assign hotel name or place id !')


    # request data (from client)
    check_in_time = scrape_time[0].split('-')
    check_out_time = scrape_time[1].split('-')

    payload_client = {
        'checkin_year': check_in_time[0],
        'checkin_month': check_in_time[1],
        'checkin_monthday': check_in_time[2],
        'checkout_year': check_out_time[0],
        'checkout_month': check_out_time[1],
        'checkout_monthday': check_out_time[2],
        'group_adults': str(num_people),  # number of people
        'group_children': '0',  # number of children
        'no_rooms': str(num_rooms),  # number of rooms
    }

    # website data
    payload_website = {
        'aid': '1288258',  # need or not?
        'label': 'gen173nr-1DCAEoggI46AdIM1gEaOcBiAEBmAEwuAEXyAEM2AED6AEBiAIBqAIDuAKJ6b39BcACAdICJGNhNDI0OWE4LWI3OTEtNGJmZi1hYzc3LWQ2NTgyNzFlNTlmYdgCBOACAQ',
        # need or not?
        'sid': '496ffe4644cfaa958be35e8693a2ba9c',  # need or not?
        'sb': '1',  # need or not?
        'src': 'searchresults',
        'src_elem': 'sb',  # need or not?
        'is_ski_area': '0',  # need or not?
        'from_sf': '1',  # ???
        'ac_langcode': 'xt',
    }

    payload = {**payload_destination ,
               **payload_client ,
               **payload_website}

    return payload, headers


# check target information in search result or not
def check_alive_or_not(search_result,
                       msg_if_none=None,
                       text=True,
                       tag=None,
                       ):
    '''
    # function : deal with the find result from soup ; if result is None , return default msg

    msg_if_none : if search result is None , return this msg

    text : if True , get text in tag ; if False , get tag property

    tag : if not none , get property of that tag
    '''
    if not search_result:
        if msg_if_none:
            return msg_if_none
        else :
            return None
    else:
        if not text and not tag:
            raise NameError("Need to assign tag if not finding text!!")

        if len(search_result) > 1:
            search_result = [result.text for result in search_result ]
            search_result = ' + '.join(search_result)

            return search_result

        return search_result.text if text else search_result[tag]


# get information of hotels
def get_hotel_information(
                          date=None ,
                          num_people = 2 ,
                          num_rooms = 1 ,
                          hotel_name=None,
                          instant_information=False,
                          destination_admin=None,
                          place_id=None,
                          url=BASE_BOOKING_URL
                        ):
    '''

    #function : main function of scraping from booking.com ,
                to get hotel information including non-instant or instant data by hotel_name or place id

    date : day to check-in and check-out , ex: ['2020-12-10','2020-12-11']

    num_people : number of people to check in

    num_rooms : number of rooms to book

    hotel_name : name of hotel in "booking or agoda" website

    instant_information : if True , get instant information ( price , avaliable number of rooms , room_recommend

    destination_admin : administration of this area (e.g. Tainan , Hsinchu)

    place_id : place id of hotel in gmaps (represent accurate position information like address)


    '''

    city_en_to_cn = {
        'Tainan' : '台南' ,
        'Hsinchu' : '新竹' ,
        'Yilan' : '宜蘭' ,
        'Hualien' : '花蓮'
        # continue to update ....
    }

    if not destination_admin:
        raise NameError('Need to know administrative area !')

    if not hotel_name and not place_id:
        raise NameError('Need to assign hotel_name or place_id !')

    if instant_information and not date:
        raise NameError('Instant information need to assign date!')

    if not instant_information:
        # 這邊是為了抓non-instant information
        # 為了避掉周末會沒房源,可能會造成 gmaps & booking 房源名字比對時的錯誤(如果沒房源會抓不到那間飯店!)
        if datetime.now().isoweekday() in [5, 6, 7]:
            date = [get_date_string(delta_day=17), get_date_string(delta_day=18)]
        else:
            date = [get_date_string(delta_day=0), get_date_string(delta_day=1)]

    destination_admin = city_en_to_cn[destination_admin] # header need to pass chinese word as argument
    payload, headers = get_header_payload(
                                              scrape_time = date ,
                                              target_hotel=hotel_name ,
                                              place_id=place_id ,
                                              destination_admin=destination_admin ,
                                              num_people = num_people ,
                                              num_rooms = num_rooms
                                          )


    NotFinish, retry = True, 0
    while NotFinish:

        soup = send_request(url, method='POST', data=payload, headers=headers)

        try:
            soup_content = soup.find_all("div", {'class': "sr_item_content sr_item_content_slider_wrapper"})[0]
            soup_pic = soup.find_all("div", {'class': "sr_item_photo sr_card_photo_wrapper"})[0]
            NotFinish = False

        except IndexError:
            retry += 1
            if retry > 3:
                return {}  # retry too many time , return empty dicts

            print(f'Soup content error , retry {retry} times!')

    return extract_informations_from_soup(date , soup_content, soup_pic, instant_information)


# extract information from soup
def extract_informations_from_soup( date , soup_content, soup_pic, instant_information=False):
    '''
    # function : extract information from soup

    soup_content , soup_pic : content of soup

    instant_information : if True , get instant information ( price , avaliable number of rooms , room_recommend )
    '''

    # p class="simple_av_calendar_no_av sold_out_msg"
    if instant_information:
        ### get below <div class="sr_item_content sr_item_content_slider_wrapper ">

        room_soldout = bool(soup_content.find('p', {'class': "simple_av_calendar_no_av sold_out_msg"}))
        if room_soldout:
            return {
                    'queried_date' : date[0] , #get check-in date
                    'instant_hrefs': None ,
                    'room_recommend': '太夯了!!已售完!!',
                    'room_remainings': '太夯了!!已售完!!' ,
                    'hot': '太夯了!!已售完!!',
                    'price': None ,
            }
        # print(soup_content.prettify())

        hotel_instant_hrefs = soup_content.find('a', {'class': "js-sr-hotel-link hotel_name_link url"})['href'].strip("\n")  # get room_hrefs

        hotel_room_recommend = check_alive_or_not(soup_content.find('div', {'class': "room_link"}).find('strong'))
        if not hotel_room_recommend :

            sub_soup_content = soup_content.find_all('div', {'class': "room_link"})
            if sub_soup_content:
                hotel_room_recommend = [sub_content.find('span' , {'role' : 'link'}).text.rstrip("\n").strip("\n") for sub_content in sub_soup_content]
                hotel_room_recommend = ' + '.join(hotel_room_recommend)
            else:
                hotel_room_recommend = '快上網站看看!'

        hotel_room_remainings = check_alive_or_not(soup_content.find('span', {'class': "only_x_left"}), msg_if_none='房源還很充足!').rstrip("\n").strip("\n")  # get remaining rooms (instant information) 不是每個hotel都有此block !!!!!
        hotel_hot = check_alive_or_not(soup_content.find('div', {'class': 'rollover-s1 lastbooking'}),msg_if_none='快上網站訂房!').rstrip("\n").strip("\n")  # get the hot of hotels (instant information) 不是每個hotel都有此block !!!!!
        hotel_price = int(get_digits(str(soup_content.find('div', {'class': "bui-price-display__value"})).split('TWD')[1])[0])

        '''if hotel_price == 1022:
            print(
                str(soup_content.find('div', {'class': "bui-price-display__value"}))
            )'''

        # !!BUGS: price 部分有 /xa0124 encode 的問題
        return {
                'queried_date' : date[0] ,
                'instant_hrefs': hotel_instant_hrefs ,
                'room_recommend': hotel_room_recommend,
                'room_remainings': hotel_room_remainings,
                'hot': hotel_hot,
                'price': hotel_price,  # remove /xa0
        }


    else:
        ### get below <div class="sr_item_content sr_item_content_slider_wrapper ">
        hotel_hrefs = soup_content.find('a', {'class': "js-sr-hotel-link hotel_name_link url"})['href'].strip("\n")  # get

        # these items below may not exist
        hotel_rating = check_alive_or_not(soup_content.find("div", {'class': "bui-review-score__badge"}))

        hotel_comment_num = check_alive_or_not(soup_content.find('div', {"class": "bui-review-score__text"})) # get # of comments
        hotel_comment_num = get_digits(hotel_comment_num)[0] if hotel_comment_num else None

        hotel_star = check_alive_or_not(soup_content.find('span', {'class': "bui-rating bui-rating--smaller"}),text=False, tag='aria-label')  # get star of hotel
        hotel_star = get_digits(hotel_star)[0] if hotel_star else None

        ### get below <div class="sr_item_photo sr_card_photo_wrapper" id="hotel_5621655">
        hotel_pic_link = soup_pic.find('img', {'class': "hotel_image"})['data-highres']  # get hotel review pic


        return {"href": hotel_hrefs,
                "comment_num": hotel_comment_num,
                "stars": hotel_star,
                "pic_link": hotel_pic_link,
                "source_rating": hotel_rating
                }


def get_detail_hotel_information(hotel_name=None, place_id=None, destination_admin=None):
    '''
    Function : getting booking information together by "hotel_name" or "place_id"

    # hotel_name : hotel_name in google maps

    # place_id : place id in google maps

    # retrun_name : return name and inform dict or not
    '''

    if not hotel_name and not place_id:
        raise NameError('Need to offer name of hotel or place_id!')

    inform_dict = get_hotel_information(hotel_name=hotel_name,
                                        place_id=place_id,
                                        destination_admin=destination_admin)

    if inform_dict:
        href = inform_dict['href']
        new_url = HEADER_URL + href
        soup_sub = send_request(new_url, method="GET")

        # soup of commnet part
        soup_comment = soup_sub.find_all('p', {'class': 'trackit althotelsReview2 fixed_review_height fixed_review_top_align review_content'})
        comments = [item.text.rstrip("\n").strip("\n") for item in soup_comment]

        # soup of pics part
        soup_pic = soup_sub.find_all("a", {'class': 'bh-photo-grid-item'})
        pics = [item['href'] for item in soup_pic]

        # soup of latlng part
        latlng_booking = soup_sub.find('a', {'id': "hotel_sidebar_static_map"})
        latlng_booking = latlng_booking['data-atlas-latlng'].split(',')
        latlng_booking = [float(latlng_booking[1]), float(latlng_booking[0])]

        # soup of booking name part
        name_booking = soup_sub.find('h2', {'id': 'hp_hotel_name'}).text.split('\n')[2]
        #print(f' in func : {name_booking}')

        detail_inform_dict = {
            'comments': comments,
            'pics': pics,
            'latlng_booking': latlng_booking,
            'name_booking': name_booking
        }

    else:
        detail_inform_dict = {}

    return inform_dict, detail_inform_dict