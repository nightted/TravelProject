import numpy as np
import math
from functools import partial
import seaborn as sns

from linebot.google_map_scraper import rating_modify , grid_generator , init_gmaps
from linebot.save_load import load_pkl
from linebot.tools import set_env_attr , distance

set_env_attr()  # set env attrs
from linebot.models import *


# GLOBAL PARAMETER
lng_1 = 102.516520*1000 # 1 longitude to meters
lat_1 = 110.740000*1000 # 1 latitude to meters
center_of_city = {
    "Tainan" : {'lat': 22.9913113, 'lng': 120.198012} ,
    "Hsinchu" : {'lat': 24.8015877, 'lng': 120.9715883},
} # search center (lat , lng) of cities



# filter method
def filter_by_criteria(obj, center, criteria, scan_shape='rectan'):
    """
    # function : To filter object fitted criteria

    :param obj: object to check if fit criteria
    :param center: search center
    :param criteria: search "radius"
    :param scan_shape: searc shape

    :return: criteria fitted object
    """

    # Judge if whether it's hotel object,
    # if so , check room_source exsit or not ; if not , set as True (belong to resturant or con)
    if hasattr(obj, 'room_source'):
        selectable = True if getattr(obj, 'room_source') else False  # for handling hotel type store
    else:
        selectable = True

    if scan_shape == "circle":
        return obj if distance([obj.lng, obj.lat], center) < criteria and selectable else None
    elif scan_shape == 'rectan':
        return obj if abs(obj.lng - center[0]) * lng_1 < criteria and abs(obj.lat - center[1]) * lat_1 < criteria and selectable else None


def filter_store_by_criteria(objs , center, criteria, scan_shape='rectan'):

    judge_func = partial(filter_by_criteria,
                         center=center,
                         criteria=criteria,
                         scan_shape=scan_shape)  # use partial func to pre-init params pos => https://wiki.jikexueyuan.com/project/explore-python/Functional/partial.html

    filtered_stores = list(map(judge_func, objs))  # get # of points inside circle or rectangle
    filtered_stores = list(filter(None.__ne__, filtered_stores))  # filter None objects

    return filtered_stores

# Calculate local density of stores
def local_density(
                    data_objects,  # form = [ object1 , object2  , ..... ]
                    rating_dependent = False,  # use modified rating score or not
                    jump_distance = 100,  # interval of scan spot
                    ranging = 40,  # scan range
                    scan_distance = 300,  # scan radius of circle or side length of rectangle
                    scan_shape = "rectan"  # shape of scan area
                ):


    # transform density array to matrix
    def density_matrix_form(density_array):

        '''
        now data process direction :
        y axis : lat
        x axis : lng
          --------- y axis (j) ------->
          |
          x

          a
          x
          i
          s

          (i)
          |
          V
        '''
        # get the length of grid square
        d = np.zeros((int((len(density_array)) ** 0.5), int((len(density_array)) ** 0.5)))  # density matrix
        p = np.zeros((int((len(density_array)) ** 0.5), int((len(density_array)) ** 0.5))).tolist()  # position matrix
        i, j = 0, -1

        for idx, (posi, densi) in enumerate(sorted(density_array, key=lambda x: x[0])):

            if idx == 0:
                dummy_x = posi[0]
            if dummy_x == posi[0]:  # if lng not change ,only change the write-in row(j+)
                j += 1
            else:  # if lng change , change the write-in column(i+)
                i += 1
                j = 0
                dummy_x = posi[0]
            d[i][j] = densi
            p[i][j] = posi  # how to rotate 90 degree ???
        p = np.array(p)

        return np.rot90(d, k=1), np.rot90(p, k=1, axes=(0, 1))  # rotate 90' counterclockwise to fit x-y direction

    if not data_objects:
        raise NameError('No place objects in list!!')

    # initialize start point
    admin_area = data_objects[0].admin_area # get admin area from first place obj
    start_point = center_of_city[admin_area]

    # initialize density list ,Rho ,start point
    density = []
    MAX_Rho, MAX_position = 0, None  # max Rho and position

    # initialize grids , judge function
    scan_mode = 'full_cover' if ranging > 0 else 'normal'  # if ranging = 0 , single point scan , using normal mode for grid
    grid_positions = grid_generator(start_point,
                                    radius = jump_distance,
                                    ranging = ranging,
                                    mode = scan_mode)  # set search grids initialization
    grid_positions = [[position["lng"], position["lat"]] for position in grid_positions]


    for now_position in grid_positions:
        # (Done by 11/14): 這地方直接綁 store object 似乎更好, 直接 filter( judge_func , object ) 出來 , output 是符合條件的 objects !!!
        # 也不會有 judge function 那邊 x[0] 這種還要給 index 的狀況出現 !! 可改成 lambda x , pos : distance( object.location ,pos) < criteria
        # 這樣 lambda function 就可以獨立出來 ,跟 store_filter_by_radius function 做結合!!!
        filter_objs = filter_store_by_criteria(data_objects,
                                               center=now_position,
                                               criteria=scan_distance,
                                               scan_shape=scan_shape)

        store_counts = [rating_modify(obj.rating) / 512 if rating_dependent else 1  for obj in filter_objs]  #if consider rating_dependent, rating/512 to modify ratings ; if not ,set as 1
        Rho = sum(store_counts) / (math.pi * (scan_distance / 1000) ** 2) if scan_shape == "circle" else sum(store_counts) / ((2 * scan_distance / 1000) ** 2)  # calculate density

        # store data
        density.append([now_position, Rho])
        (MAX_Rho, MAX_position) = (Rho, now_position) if Rho > MAX_Rho else (MAX_Rho, MAX_position)  # store max value

    print(f'MAX_Rho = {MAX_Rho} , MAX_position = {MAX_position}')

    return density_matrix_form(density), MAX_Rho, MAX_position



# finding the top10 hightest density position "consider hotels distribution"
def search_peak(*density_objects,
                admin_area ,
                silence_demand=False,
                target_sigtseeings=None
                ):
    '''
    #function : search peaks from density grid maps

    city : city to search (e.g. Tainan , Hsinchu ..)

    silence_demand : if True , choose place 鬧中取靜XD .

    target_sigtseeings : target sightseeing customer want to go , type as : ['sightseeing1','sightseeing2']

    **densitys : the basic density "objects" you want to consider , ex : ('resturant' = density_restruant , 'hotel' = density_hotel .. )

    return : peaks with [ position_x(grid) ,position_y(grid) , density of resturant center , scors of center]

    '''

    if not admin_area:
        raise NameError('Need to assign admin_area!!')

    # ---------- INITIALIZE ----------
    # init of grid to lat , lng transform matrix
    grid_to_latlng = Array_3d.objects.get(name = 'gridtolatlng' , admin_area = admin_area).array

    # the minimum score of point to find (it's too far out of city if score less than this value!)
    demand_threshold = 3

    # the weights of basic density(for local popularity) , including: hotel , resturant , con_store density
    basic_weights = {
        'resturant': 1,
        'con': 0.5,
        'hotel': 0.25
    }

    # the weights of special food(You want to eat!) density , such : porkrice , eulnooles , beefsoup ..
    food_weights = 5

    # corrected weight for silence demand (from get min -> max ,so add negative weight -1)
    corrections = [1] * len(density_objects) if not silence_demand else [-1] * len(basic_weights) + [1] * (len(density_objects) - len(basic_weights))

    # initialize data of train_station and sightseeing (for 1/r wighting use)
    stations = Station.objects.filter(place_sub_type = 'station' , admin_area = admin_area)
    station_position = [[station.lng, station.lat] for station in stations ]
    sightseeing_positions = get_latlng_directly(target_sigtseeings , admin_area) if target_sigtseeings else []
    all_positions = station_position + sightseeing_positions # combine

    # initialize data of density
    density_name = [ density_obj.name for density_obj in density_objects ]  # all the name of densitys => [resturant , eelnoodles , ..]
    density_stack = np.array([density_obj.array for density_obj in density_objects])  # stack the all the densitys
    shape_W_L = density_stack.shape[1]

    # main loop for finding peaks
    peaks , excludes = [] , []
    for i in range(shape_W_L):
        for j in range(shape_W_L):

            if [i , j] not in excludes: # if not excludes points

                # find surrounding 8 positions
                surrounding = [[k, l] for k in range(i - 1, i + 2) for l in range(j - 1, j + 2) if (k != i or l != j) and (shape_W_L > k >= 0  and shape_W_L > l >= 0)]

                # score of surroundings
                density_surroundings = [density_stack[:, pos_x, pos_y] for pos_x, pos_y in surrounding]
                score_surrounding = []
                for density_surrounding in density_surroundings:
                    score = 0
                    for correction, name, density in zip(corrections, density_name, density_surrounding):
                        score += correction * basic_weights.get(name, food_weights) * density
                    score_surrounding.append(score)

                # score of center
                density_center = density_stack[:, i, j]
                score = 0
                for correction, name, density in zip(corrections, density_name, density_center):
                    score += correction * basic_weights.get(name, food_weights) * density
                score_center = score

                # if center larger than all surroundings and larger than minimum threshold , keep the point
                if len(list(filter(lambda x: x < score_center, score_surrounding))) == 8 and abs(score_center) > demand_threshold:

                    excludes = excludes + surrounding # store the excludes points ( if the points is a peak , the surrounding points must not be peaks !)

                    current_position = grid_to_latlng[i][j]
                    positions_distance = list(map(lambda x : distance(current_position , x), all_positions))  # distance from current position to all_positions
                    positions_distance_weighting = sum([1000.0 / distance for distance in positions_distance])  # calculate 1/r weights for all_positions

                    peaks.append([list(grid_to_latlng[i][j]), score_center * positions_distance_weighting])
                    # peaks = [ [ [lng1,lat1] , score1 ] , [ [lng2,lat2] , score2 ] , ...]
                else:
                    continue

            else:
                continue

    # sort peaks by scores
    peaks = sorted(peaks, reverse=True, key=lambda x: x[1])
    peaks = [peak_inform[0] for peak_inform in peaks]  # extract positions only

    return peaks


def get_latlng_directly( positions , admin_area ):
    # In Django ORM , adjust to find in Class.object.all()

    position_latlng = []
    for position_name in positions:

        place = Place.objects.filter(name = position_name , admin_area = admin_area) #search from place
        if not place:
            maps = init_gmaps()
            res = maps.geocode(position_name)
            location = res[0]['geometry']['location']
            position_latlng.append([location['lng'], location['lat']])

        else:
            position_latlng = position_latlng + [ [p.lng , p.lat] for p in place ]

    return position_latlng

