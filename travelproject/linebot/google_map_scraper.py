import time as t
from linebot.models import Hotel , Resturant , Station , Sightseeing
from linebot.tools import find_english_char , get_digits

'''
#  This module search and scrape the stores of specific type , the following is the    
1. Build grid search points
2. from the search points , search for nearby stores ()
'''

# GLOBAL PARAMETER
lng_1 = 102.516520*1000 # 1 longitude to meters
lat_1 = 110.740000*1000 # 1 latitude to meters

# The range of lat,lng of Taiwan
Admin_area_range_lng = [120.03786531340755 , 122.00991123709818]
Admin_area_range_lat = [21.871068186336803 , 25.30245194059663]


# TODO : read API_KEY (wait modify)
def read_key(key_path):
    with open(key_path, 'r') as f:
        KEY = f.read()
    return KEY

# Check the place is in target admin_area or not
def check_place_in_range(lnglat, Admin_area_range_lng, Admin_area_range_lat):
    try:
        lng = lnglat['lng']
        lat = lnglat['lat']

    # if the argumaent is None
    except TypeError:
        return True

    return Admin_area_range_lng[0] < lng < Admin_area_range_lng[1] and Admin_area_range_lat[0] < lat < \
           Admin_area_range_lat[1]


# generate grid of position by radius
def grid_generator(location, radius, ranging, mode="max_area"):
    '''
    function : generate search points (grid)

        @ is scan point in grid

        mode 'normal : @--2*r--@--2*r--@--2*r--@--2*r--@
                @--2*r--@--2*r--@--2*r--@--2*r--@

        mode 'max_area' :    @--2*r--@--2*r--@--2*r--
                    --2*r--@--2*r--@--2*r--@

        mode 'full_cover' :  @-r-@-r-@-r-@-r-@
                    @-r-@-r-@-r-@-r-@
    input :
      #location : search center (grid start generating from this point)
      #radius : interval between grid point
      #ranging : number of search points to generate in top,bottom,left,right ( 1 ranging equal to generate 2 points about 1 radius interval in "full-cover" mode)

    rtype :
      #grid : grids of position
    '''

    rg = [i for i in range(ranging, -(ranging + 1), -1)]  # get list between [int , -int]
    grid_delta_lng = radius / lng_1  # unit transform between meter and lat,lng  ( 1000m radius <=> 0.01 lag ,lng )
    grid_delta_lat = radius / lat_1

    lng, lat = location['lng'], location['lat']
    # get the grids
    grid_outer = [{'lng': lng + grid_delta_lng * 2 * lng_delta, 'lat': lat + grid_delta_lat * 2 * lat_delta} for
                  lng_delta in rg for lat_delta in rg]

    if mode == 'max_area':
        grid_inner = [{'lng': dicts['lng'] - grid_delta_lng, 'lat': dicts['lat'] - grid_delta_lat} for dicts in
                      grid_outer]

        return grid_outer + grid_inner

    if mode == 'full_cover':
        grid_inner = [{'lng': dicts['lng'] - grid_delta_lng, 'lat': dicts['lat'] - grid_delta_lat} for dicts in
                      grid_outer]
        grid_down = [{'lng': dicts['lng'], 'lat': dicts['lat'] - grid_delta_lat} for dicts in grid_outer]
        grid_aside = [{'lng': dicts['lng'] - grid_delta_lng, 'lat': dicts['lat']} for dicts in grid_outer]

        return grid_outer + grid_inner + grid_down + grid_aside

    return grid_outer


def extract_address_by_geocode(maps, store_name):
    '''
    function : address extraction

    input :
      #maps : google map client
      #store_name : store you want to extract address

    rtype :
      #address : address of store
    '''

    address, lnglat = geocode_subprocess(maps, store_name)

    if check_place_in_range(lnglat, Admin_area_range_lng, Admin_area_range_lat):
        return address
    else:
        print('[WARNING] This place is not in Taiwan!')

    return None


def geocode_subprocess(maps, store_name):
    '''
    function : sub-process of address extraction

    input :
      #maps : google map client
      #store_name : store you want to extract address

    rtype :
      #address : address of store
      #lnglat : latitude , longitude of store

    '''

    # administrative level :
    # postal_code(區碼) > country(國) > administrative_area_level_1(市) > administrative_area_level_2 > administrative_area_level_3(區) > route(路街巷) > street_number(號) > subpremise(樓)
    administrative_level = {
        "postal_code_suffix": 10,
        "postal_code": 9,
        "country": 8,
        "administrative_area_level_1": 7,
        "administrative_area_level_2": 6,
        "administrative_area_level_3": 5,
        "locality": 4,
        "route": 3,
        "street_number": 2,
        "subpremise": 1,
        "establishment": 0,
        "neighborhood": -1
    }

    # There's 2 condition return empty address and latlng
    # 1. geocoding can't find the store name
    # 2. result of geocoding for administrative level goes wrong

    geo_res = maps.geocode(store_name, language='zh-TW')
    if not geo_res:
        print(f'[WARNING] No such hotel found in geocode : {store_name}!')
        return None, None

    try:
        address = [level_ad['long_name'] for level_ad in sorted(geo_res[0]['address_components']
                                                                , reverse=True
                                                                , key=lambda x: administrative_level[x['types'][0]])
                   if not find_english_char(level_ad['long_name'])]  # get address by administrative level
    # if the administrative level goes wrong
    except KeyError:
        print('Something wrong with the address!')
        return None, None

    address = ''.join(address)  # combine address by administrative level
    address = address + get_digits(geo_res[0]['formatted_address'])[
        0] + '號' if '號' not in address else address  # if not contain '號' ,get No. in formatted_address
    address = address[3:]  # remove 7XX postal code

    lnglat = geo_res[0]['geometry']['location']

    return address, lnglat


# get store information with location , keyword , search radius
def store_scraper(maps,
                  keyword,
                  location,
                  location_admin,
                  radius,
                  next_page_token,
                  objects,
                  place_type=None ,
                  place_sub_type=None
                                        ):
    '''
    function : get stores with keyword in some radius

    input:
      #keyword : keyword of store you want to search

      #location : search center

      #location_admin : administrative name of area

      #radius : search radius

      #next_page_token : to get data of page 20~40 , 40~60

      #objects : objects already storage (list)

      #place_type : main type of place (Restaurant , Station , Sightseeing , Hotel)

      #place_sub_type : sub type of place (EEL , porkrice ...)

    rtype:
      #next_page_token : to get data of page 20~40 , 40~60

      #objects : store or hotel objects found

    '''
    class_hash = {
        'hotel': Hotel,
        'resturant': Resturant,
        'station': Station,
        'sightseeing': Sightseeing,
    }

    if not place_type:
        raise NameError('No store type assigned!')

    if objects == None:
        objects = []

    res = maps.places_nearby(page_token=next_page_token, keyword=keyword, location=location, radius=radius,
                             language='zh-TW')  # get stores list nearby
    for store_inform in res['results']:

        lat_lng = store_inform['geometry']['location']
        lat, lng = lat_lng['lat'], lat_lng["lng"]
        name = store_inform['name']
        place_id = store_inform['place_id']
        rating = store_inform.get('rating', None)

        # exclude stores not contains ratings
        if rating:

            # TODO : Handling address representation in this part (這邊試著把它打包起來XD).
            try:
                # In this part , there's 2 kind of ERROR here
                # 1. The address we got contains English words (We need chinese!!!)
                # 2. Can't get the address directly from store_inform dictionary (KeyError)
                # when encounters this 2 condition , use the geocode() to get address again.
                address = store_inform['plus_code']['compound_code'].split(' ')[-1] + store_inform['vicinity']
                if find_english_char(address):
                    # In this part , there's also 2 kind of WARNINGs here
                    # 1. The geocode returned isn't in locality
                    # 2. The geocode can't find any result (including truly not found or admin level fail)
                    # when encounters this 2 condition , use the original address we got.
                    print(f'[ENGLISH ERROR] {name} change to geocode !')
                    extract_address = extract_address_by_geocode(maps, name)
                    address = extract_address if extract_address != None else address

            # if key error when finding address , special handling
            except KeyError:
                print(f'[KEYERROR ERROR] {name} change to geocode !')
                extract_address = extract_address_by_geocode(maps, name)
                address = extract_address if extract_address != None else address

            address = address.split('號')[
                          0] + '號'  # remove following char after '號' and 70X at head , EX : 700中西區海安路256號一樓 => 中西區海安路256號

            information = {
                               'place_type': place_type ,
                               'place_sub_type' : place_sub_type,
                               'name': name,
                               'lng': lng,
                               'lat': lat,
                               'rating': rating,
                               'admin_area': location_admin,
                               'address': address,
                               'place_id': place_id
                           }

            # NOTE THAT , the store_obj generate here is NOT save to database yet !
            try :
                store_obj = class_hash[place_type].create_obj_by_dict(store_dict=information)
            except KeyError:
                raise NameError('Need to specify place CLASS NAME in class_hash table!')

            # ignore overlap objects
            if store_obj not in objects:
                store_obj.save() # store to database
                objects.append(store_obj)

        # discard None-rating store and add new items if it's not already exsit
        else:
            print(f"[WARNING] {name} doesn't contains rating !")
            continue

    next_page_token = res.get('next_page_token', None)  # get if token exsit or return None

    return next_page_token, objects


# get store information with location , keyword , search radius (plus the change pages and move search location)
# 1 ranging is across 2 * radius in each sides
# EX : radius = 1000 , ranging = 1 , so the spanning region is 2000 in top,bottom,left,right directions , total scan area = 4000 X 4000 .
def moving_store_scraper(maps,
                         keyword,
                         search_center,
                         admin_area,
                         radius,
                         ranging,
                         next_page_token=None,
                         objects=None,
                         place_type=None,
                         place_sub_type=None,
                         mode="max_area"):
    '''
    function : get stores with keyword in range of grid

    input:
      #keyword : keyword of store you want to search

      #location : search center

      #radius : search radius

      #next_page_token : to get data of page 20~40 , 40~60

      #objects : objects already storage (list)

      #place_type : main type of place (Restaurant , Station , Sightseeing , Hotel)

      #place_sub_type : sub type of place (EEL , porkrice ...)
    rtype :
      #objects : store or hotel objects found

    '''

    search_points = grid_generator(search_center, radius, ranging, mode=mode)
    for idx, location in enumerate(search_points):

        print(f'finish [{idx + 1}/{len(search_points)}] parts !')
        while True:  # change page
            next_page_token, objects = store_scraper(maps,
                                                     keyword,
                                                     location,
                                                     admin_area,
                                                     radius,
                                                     next_page_token=next_page_token,
                                                     objects=objects,
                                                     place_type=place_type,
                                                     place_sub_type = place_sub_type)
            if next_page_token == None:
                break
            t.sleep(3)  # set time sleep to avoid request too often !
    return objects


def update_new_stores(**kwargs):
    '''
    wait extend ...
    '''
    pass


# store weighting
def rating_modify(rating):
    if 4.8 < rating <= 5.0:
        score = 512.0
    elif 4.6 < rating <= 4.8:
        score = 256.0
    elif 4.4 < rating <= 4.6:
        score = 128.0
    elif 4.2 < rating <= 4.4:
        score = 64.0
    elif 4.0 < rating <= 4.2:
        score = 32.0
    elif 3.8 < rating <= 4.0:
        score = 16.0
    elif 3.6 < rating <= 3.8:
        score = 8.0
    elif 3.4 < rating <= 3.6:
        score = 4.0
    elif 3.2 < rating <= 3.4:
        score = 2.0
    else:
        score = 1.0

    return score


def distance(a, b):
    '''
    get distnace of two point (in unit of meter)
    '''
    a_x, a_y = a[0], a[1]
    b_x, b_y = b[0], b[1]
    delta_x_meter = (a_x - b_x) * lng_1
    delta_y_meter = (a_y - b_y) * lat_1

    return ((delta_x_meter) ** 2 + (delta_y_meter) ** 2) ** 0.5


# grab the store contain some keyword (ex: 扁食)
def grab_keyword_store(data, keyword=''):
    '''
    # function : transform data to numpy

    data : list of store objects

    keyword : to filter keyword in store_name

    '''

    x, y, x_y, rat, name = [], [], [], [], []
    for item in data:
        if keyword in item.name:  # if keyword == None , grab all stores
            x.append(item.location[0])
            y.append(item.location[1])
            x_y.append(item.location)
            # rat.append(rating_modify(item['rating'])) # rating func 要修正XD , EX: 4.8~5.0 => 10 分 , 4.6~4.8 => 9 分 , ... , < 3.0 => 1分
            rat.append(item.rating)
            name.append(item.name)

    return x, y, x_y, rat, name