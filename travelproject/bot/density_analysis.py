import numpy as np
import math
from scipy.ndimage.filters import maximum_filter
from scipy.ndimage.morphology import generate_binary_structure, binary_erosion

from bot.constants import *
from bot.google_map_scraper import rating_modify , grid_generator , init_gmaps
from bot.tools import set_env_attr

set_env_attr()  # set env attrs
from bot.models import *
from bot.tools import lat_lng_to_x_y , x_y_to_lat_lng


# Calculate local density of stores
def local_density(
                    data_objects,  # form = [ object1 , object2  , ..... ]
                    rating_dependent = False,  # use modified rating score or not
                    jump_distance = 100,  # interval of scan spot
                    ranging = 40,  # scan range
                    scan_distance = 300,  # scan radius of circle or side length of rectangle
                    scan_shape = "rectan"  # shape of scan area
                ):

    '''
    # function : calculate local density of place objects

    :param data_objects: place objects you want to construct local density
    :param rating_dependent: consider weights modify of rating or not ; if yes , will modify rating using rating_modify()
    :param jump_distance:  distance between density search grids
    :param ranging: density search range
    :param scan_distance: density search radius
    :param scan_shape: search shape

    :return: density matrix ,  position-lat,lng transform matrix , MAX density , MAX density poistion
    '''

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
    start_point = center_of_city[admin_area]['location'] # center of grids generation

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


def detect_peaks(image):

    """
    Takes an image and detect the peaks using the local maximum filter.
    Returns a boolean mask of the peaks (i.e. 1 when
    the pixel's value is the neighborhood maximum, 0 otherwise)
    """

    # define an 8-connected neighborhood
    neighborhood = generate_binary_structure(2,2)

    #apply the local maximum filter; all pixel of maximal value
    #in their neighborhood are set to 1
    local_max = maximum_filter(image, footprint=neighborhood)==image

    #local_max is a mask that contains the peaks we are
    #looking for, but also the background.
    #In order to isolate the peaks we must remove the background from the mask.

    #we create the mask of the background
    background = (image==0)

    #a little technicality: we must erode the background in order to
    #successfully subtract it form local_max, otherwise a line will
    #appear along the background border (artifact of the local maximum filter)
    eroded_background = binary_erosion(background, structure=neighborhood, border_value=1)

    #we obtain the final mask, containing only peaks,
    #by removing the background from the local_max mask (xor operation)
    detected_peaks = local_max ^ eroded_background

    return detected_peaks

# A 2-D peaks search method from : https://stackoverflow.com/questions/3684484/peak-detection-in-a-2d-array
def maximum_filter_method(density_stack ,
                          density_name,
                          corrections ,
                          grid_to_latlng ,
                          basic_weights ,
                          food_weights = 5
                          ):


    density_stack_weighted = [corr * basic_weights.get(den_name, food_weights) * matrix for corr, den_name, matrix in zip(corrections, density_name, density_stack)]  # get weighted stacking matrix (3D)
    density_stack_weighted = np.sum(density_stack_weighted, axis=0)  # Score : sum over all type of density  (2D)

    #print('DEBUG density_stack_weighted :', density_stack_weighted)

    peaks_binary = detect_peaks(density_stack_weighted) # get peaks binary data (if it's peak ,set as True ; else as False)

    #print('DEBUG max filter :' , peaks_binary )


    # extract lat,lng and calculate score from peaks_binary
    peaks = []
    for idx_r, row in enumerate(peaks_binary):
        for idx_c, col in enumerate(row):
            if col:  # if True , means it's peaks.

                peak_score = density_stack_weighted[idx_r][idx_c]
                peaks.append([list(grid_to_latlng[idx_r][idx_c]), peak_score])
                # peaks = [ [ [lng1,lat1] , score1 ] , [ [lng2,lat2] , score2 ] , ...]

    return peaks

# A 2-D peaks search of greedy method
def iterate_method(density_stack ,
                   density_name,
                   corrections ,
                   grid_to_latlng ,
                   basic_weights ,
                   food_weights = 5 ,
                   ):

    # initialize params
    shape_W_L = density_stack.shape[1]
    peaks, excludes = [], []

    density_stack_weighted = [corr * basic_weights.get(den_name, food_weights) * matrix for corr, den_name, matrix in zip(corrections, density_name, density_stack)]  # get weighted stacking matrix (3D)
    density_stack_weighted = np.sum(density_stack_weighted, axis=0)  # Score : sum over all type of density  (2D)

    # main loops for finding peaks
    for i in range(shape_W_L):
        for j in range(shape_W_L):

            if [i, j] not in excludes:  # if not excludes points

                # find surrounding 4 positions
                surrounding_x = [[k, j] for k in range(i - 1, i + 2) if (k != i) and shape_W_L > k >= 0]
                surrounding_y = [[i, k] for k in range(j - 1, j + 2) if (k != j) and shape_W_L > k >= 0]
                surrounding = surrounding_x + surrounding_y

                score_center = density_stack_weighted[i,j]
                score_surrounding = [density_stack_weighted[x , y] for x , y in surrounding]

                # if center larger than all surroundings and larger than minimum threshold , keep the point
                if len(list(filter(lambda x: x < score_center, score_surrounding))) == 4 :

                    excludes = excludes + surrounding  # store the excludes points ( if the points is a peak , the surrounding points must not be peaks !)
                    peaks.append([list(grid_to_latlng[i][j]), score_center ]) # peaks = [ [ [lng1,lat1] , score1 ] , [ [lng2,lat2] , score2 ] , ...]

    return peaks


# finding the top10 hightest density position "consider hotels distribution"
def search_peak(*density_objects,
                admin_area ,
                silence_demand=False,
                target_sightseeing=None ,
                topN = 50 ,
                ):

    '''
    #function : search peaks from density grid maps

    :param density_objects: the basic density "objects" you want to consider , ex : [ density_restruant , density_hotel , .. ]
    :param admin_area: city to search (e.g. Tainan , Hsinchu ..)
    :param silence_demand: if True , choose place 鬧中取靜XD .
    :param target_sightseeing: target sightseeing clients want to go , type as : ['sightseeing1','sightseeing2']
    :param topN : number of top score peaks to return

    :return: peaks with [ position_x(grid) ,position_y(grid) , score of peak]
    '''
    if not admin_area:
        raise NameError('Need to assign admin_area!!')

    # ---------- INITIALIZE ----------
    # init of grid to lat lng transform matrix , city_center , tolerance_distance
    grid_to_latlng = Array_3d.objects.get(name = 'gridtolatlng' , admin_area = admin_area).array
    city_center = [ center_of_city[admin_area]['location']['lng'],
                    center_of_city[admin_area]['location']['lat'] ]

    tolerance_distance = 10000 # the max tolerance distance to reach

    # the minimum score of point to find ( don't consider peak with score less than this value )
    demand_threshold = 3

    # the weights of basic density(for local popularity) , including: hotel , resturant , con_store density
    basic_weights = {
        'resturant': 1,
        'con': 0.5,
        'hotel': 0.25
    }

    # the weights of correction in density
    basic_correction = {
        'resturant': -1 if silence_demand else 1,
        'con': -1 if silence_demand else 1,
        'hotel': 1
    }

    # the weights of special food(You want to eat!) density , such : porkrice , eulnooles , beefsoup ..
    food_weights = 6

    # corrected weight for silence demand (from get min -> max ,so add negative weight -1)
    corrections = [basic_correction.get(den_obj.name , 1) for den_obj in density_objects]

    # initialize data of train_station and sightseeing (for 1/r wighting use)
    stations = Station.objects.filter(place_sub_type = 'train' , admin_area = admin_area)
    station_position = [[station.lng, station.lat] for station in stations ]
    sightseeing_positions = get_latlng_directly(target_sightseeing , admin_area) if target_sightseeing else []  #TODO (備忘): This will consume Google map api cost
    sightseeing_positions = [position for position in sightseeing_positions if distance(position , city_center) < tolerance_distance ] # filter too far sightseeing

    all_positions = station_position + sightseeing_positions # combine

    if not all_positions:
        raise NameError('No position exist , will cause calculate error!')

    # initialize data of density
    density_name = [ density_obj.name for density_obj in density_objects ]  # all the name of densitys => [resturant , eelnoodles , ..]
    density_stack = np.array([density_obj.array for density_obj in density_objects])  # stack the all the densitys

    # using peaks-search algorithm to find peaks based on density data
    peaks = maximum_filter_method(density_stack=density_stack,
                                  density_name=density_name,
                                  corrections=corrections,
                                  grid_to_latlng=grid_to_latlng,
                                  basic_weights=basic_weights,
                                  food_weights=food_weights)

    # 這邊解釋一下這個判斷的用意 , 因為 silence_demand 針對 basic density stack(hotel , resturant , con)
    # 要取的是 "local minimum" , 故要轉換成取 "local maximum" 就要取負號(也就是 corrections (=-1) 用意)
    # 但這邊會有個狀況就是 , 要是只考慮 basic density 而已 (也就是沒其他 target foods),
    # 抓 peak 的時候會抓到 density = 0 的點 (), 再取負號後他理所當然變成最大值! 所以這邊先針對 density = 0 的點先進行過濾
    # 但這裡要注意一件事 , 假如有 target foods 情況下 , 因為 foods density corrections 是正(=1)的
    # 故有可能會發生 density = 0 的地方, 加上 food density 後變成 positive peak 的狀況 ,
    # 取得這樣的 peak 可能會造成附近 hotel 抓取不到的現象! TODO :

    if silence_demand and len(density_objects) == len(basic_weights):
        peaks = [ [latlng , score] for latlng , score in peaks if score != 0] # filter density = 0 peak (because it was selected!)
        min_score = min([ score for _ , score in peaks ])
        peaks = [ [latlng , (-1*min_score) + score + 0.1] for latlng , score in peaks] # shift the value up min_value to let all value positive

    # sort peaks by scores and get topN peaks
    topN = topN if topN < len(peaks) else len(peaks)  # choose topN peaks
    peaks = sorted(peaks, reverse=True, key=lambda x: x[1])[:topN]
    print('DEBUG in search peaks : ', peaks)


    # modify score topN peaks by r^-1 weight from special position (e.g. sightseeing or target food stores)
    for idx, (lat_lng , score) in enumerate(peaks):

        positions_distance = list(map(lambda x: distance(lat_lng, x), all_positions))  # distance from current position to all_positions
        positions_distance_weighting = sum([1000.0 / distance  for distance in positions_distance])  # calculate 1/r weights for all_positions
        peaks[idx][1] = score*positions_distance_weighting # update the score in peaks list

    return peaks


def get_latlng_directly( positions , admin_area ):

    '''
    # function : get the lat , lng of positions from database ; if not , directly scrape from google map api.

    :param positions: positions to search
    :param admin_area: admin_area of positions

    :return: lat , lng of positions
    '''

    position_latlng = []
    for position_name in positions:

        place = Place.objects.filter(name = position_name , admin_area = admin_area) # search from Place objects
        if not place:

            latlng = get_place_latlng_by_gmaps(position_name)
            position_latlng.append(latlng)

        else:
            position_latlng = position_latlng + [ [p.lng , p.lat] for p in place ]

    return position_latlng


def get_place_latlng_by_gmaps(position , maps = None):

    if not maps:
        maps = init_gmaps()

    res = maps.geocode(position)
    try:
        location = res[0]['geometry']['location']

        print(f"DEBUG in get_place_latlng_by_gmaps : {position} , {location}")

        return lat_lng_to_x_y(location)

    except IndexError:  # if place not exist , return empty list
        return []