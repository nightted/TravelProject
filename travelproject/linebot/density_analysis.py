import numpy as np
import math
from functools import partial

from .google_map_scraper import rating_modify , grid_generator
from .save_load import load_pkl
from .tools import distance


# GLOBAL PARAMETER
grid_to_latlng = load_pkl('grid_to_latlng/grid_to_latlng') # grid row-column idx to lng-lat coordinate
lng_1 = 102.516520*1000 # 1 longitude to meters
lat_1 = 110.740000*1000 # 1 latitude to meters


# Calculate local density of stores
def local_density(
        data_objects,  # form = [ object1 , object2  , ..... ]
        rating_depent=False,
        group_idx=None,  # if it's none setting , start point is defalut as "Tainan Train Station"
        start_point= {'lat': 22.9913113, 'lng': 120.198012},  # start point of scan (Default : 春川煎餅)
        jump_distance=100,  # interval of scan spot
        ranging=20,  # scan range
        scan_distance=300,  # scan radius of circle or side length of rectangle
        scan_shape="circle"  # shape of scan area
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

    # initialize density list ,Rho ,start point
    density = []
    MAX_Rho, MAX_position = 0, None  # max Rho and position

    # initialize grids , judge function
    scan_mode = 'full_cover' if ranging > 0 else 'normal'  # if ranging = 0 , single point scan , using normal mode for grid
    grid_positions = grid_generator(start_point, radius=jump_distance, ranging=ranging,
                                    mode=scan_mode)  # set search grids initialization
    grid_positions = [[position["lng"], position["lat"]] for position in grid_positions]
    # x[0] present position , x[1] present rating!

    for now_position in grid_positions:
        judge_func = partial(filter_by_criteria,
                             center=now_position,
                             criteria=scan_distance,
                             scan_shape=scan_shape)  # use partial func to pre-init params pos => https://wiki.jikexueyuan.com/project/explore-python/Functional/partial.html
        filter_objs = list(filter(judge_func, data_objects))  # get # of points inside circle or rectangle
        # TODO (Done by 11/14): 這地方直接綁 store object 似乎更好? 直接 filter( judge_func , object ) 出來 , output 是符合條件的 objects !!!
        # 也不會有 judge function 那邊 x[0] 這種還要給 index 的狀況出現 !! 可改成 lambda x , pos : distance( object.location ,pos) < criteria
        # 這樣 lambda function 就可以獨立出來 ,跟 store_filter_by_radius function 做結合!!!
        store_counts = [rating_modify(obj.rating) / 512 if rating_depent else 1 for obj in
                        filter_objs]  # point[1] is the rating score (consider into Rho calculate) ;if not consider rating_depent ,set as 1
        Rho = sum(store_counts) / (math.pi * (scan_distance / 1000) ** 2) if scan_shape == "circle" else sum(
            store_counts) / ((2 * scan_distance / 1000) ** 2)  # calculate density

        # store data
        density.append([now_position, Rho])
        (MAX_Rho, MAX_position) = (Rho, now_position) if Rho > MAX_Rho else (MAX_Rho, MAX_position)  # store max value

    print(f'MAX_Rho = {MAX_Rho} , MAX_position = {MAX_position}')

    return density_matrix_form(density), MAX_Rho, MAX_position


def filter_by_criteria(obj, center, criteria, scan_shape='rectan'):
    # Judge if whether it's hotel object,
    # if so , check room_source exsit or not ; if not , set as True (belong to resturant or con)
    if hasattr(obj, 'room_source'):
        selectable = True if getattr(obj, 'room_source') else False
    else:
        selectable = True

    if scan_shape == "circle":
        return obj if distance([obj.lng, obj.lat], center) < criteria else None
    elif scan_shape == 'rectan':
        return obj if abs(obj.lng - center[0]) * lng_1 < criteria and abs(
            obj.lat - center[1]) * lat_1 < criteria and selectable else None


# finding the top10 hightest density position "consider hotels distribution"
def search_peak(**kwargs):
    '''
    function : search peaks from density grid maps

    **kwargs : the density maps you want to consider , ex : (density_rs = density_rs , density_h = density_h .. )

    return : peaks with [ position_x(grid) ,position_y(grid) , density of resturant center , scors of center]

    '''

    weights = {
        'rs': 1,
        'cn': 0.5,
        'h': 0.25
    }

    # intial data of train_station
    station_position = [Tainan_train_station[0].lng, Tainan_train_station[0].lat]  # r square inverse ?

    # initialize data of density
    peaks = []
    density_stack = np.array([density for _, density in kwargs.items()])
    density_name = [name.split('_')[1] for name in kwargs.keys()]
    shape_W_L = density_stack.shape[1]

    for i in range(shape_W_L):
        for j in range(shape_W_L):

            surrounding = [[k, l] for k in range(i - 1, i + 2) for l in range(j - 1, j + 2) if (k != i or l != j) and (
                        shape_W_L > k > 0 and shape_W_L > l > 0)]  # find surranding 8 positions
            density_surrounding = [density_stack[:, pos_x, pos_y] for pos_x, pos_y in surrounding]

            score_surroundig = []
            for densitys in density_surrounding:
                score = 0
                for name, density in zip(density_name, densitys):
                    score += weights[name] * density
                score_surroundig.append(score)

            density_center = density_stack[:, i, j]
            score = 0
            for name, density in zip(density_name, density_center):
                score += weights[name] * density
            score_center = score

            if len(list(filter(lambda x: x < score_center, score_surroundig))) == 8:
                peaks.append([i,
                              j,
                              density_center[0],  # resturant
                              density_center[1],  # con
                              density_center[2],  # hotel
                              distance(grid_to_latlng[i][j], station_position) / 1000,
                              score_center / (distance(grid_to_latlng[i][j], station_position) / 1000)])
            else:

                continue

    return peaks