import re


def compare_str(pattern, string):
    '''
    function : find similar and successive pattern in strings

    input:
      #pattern : the pattern to find
      #string : the target string

    rtype :
      #char_similar_list　: the list of similar parts in target string
    '''

    similar_collect_list = []
    all_similar_list = []

    for step, char in enumerate(pattern):
        # print('char:',char)
        # print(step , char)
        if char in string:
            # print('char inner:',char)
            # EX: similar_collect_list = [ [14,15] ,[22,23] ,[1,2,3,4] ...]
            if similar_collect_list:

                # collect index of successive appeared char
                remove_collect_list = []  # define remove list to store non-successive chars
                for idx_collector in similar_collect_list:

                    # print('idx_collector[-1]+1:',idx_collector[-1]+1 ,'char : ' , char)

                    if idx_collector[-1] + 1 < len(string) and string[idx_collector[-1] + 1] == char:
                        idx_collector.append(idx_collector[-1] + 1)  # collect index of successive appeared char
                    else:
                        all_similar_list.append(idx_collector)
                        remove_collect_list.append(idx_collector)

                    similar_collect_list = [collector for collector in similar_collect_list if
                                            collector not in remove_collect_list]

                # collect index of new appered char
                remove_new_list = []  # define remove list to store appeared chars
                new_set = list(re.finditer(char, string))  # find the position of target char
                for idx in new_set:
                    for collector in similar_collect_list:
                        if idx.start() in collector:
                            remove_new_list.append(idx.start())

                new_set = [[idx.start()] for idx in new_set if idx.start() not in remove_new_list]

                similar_collect_list = similar_collect_list + new_set  # combine the indexs of new appeared and successive appeared char

                # print("collect exsit !",similar_collect_list)

            # for step = 0 or all the collectors in similar_collect_list was collected to all_similar_list (for current pattern char "not" in s case)
            else:
                similar_collect_list = [[idx.start()] for idx in re.finditer(char, string)]

            # print("similar_collect_list" , similar_collect_list)

        else:
            if similar_collect_list:
                all_similar_list += similar_collect_list
                similar_collect_list.clear()
            else:
                continue

    if similar_collect_list:
        all_similar_list += similar_collect_list
    char_similar_list = [''.join([string[idx] for idx in collector]) for collector in
                         all_similar_list]  # convert to strings

    return char_similar_list


def find_common_word_2str(str1, str2):
    '''
    function : find similar and successive chars between 2 strings

    input:
      #string : the target string

    rtype :
      #max_len_similar 　: the max number of similar chars
    '''

    str1 = re.sub('[ ()!?/,‧•【】.:飯店民宿-]', '', str1)
    str2 = re.sub('[ ()!?/,‧•【】.:飯店民宿-]', '', str2)
    similar_str = compare_str(str1, str2)

    if not similar_str:
        return 0, None

    else:
        len_list = [len(char) for char in similar_str]
        max_len_similar = max(len_list)  # find the max len of similar and successive chars
        max_len_idx = [i for i, j in enumerate(len_list) if j == max_len_similar]
        max_len_chars = [similar_str[idx] for idx in max_len_idx]

    return max_len_similar, max_len_chars


# compare name between gmaps and booking

'''
def compare_hotel_name(hotel_obj, distance_threshold=100.0):
    # MarkDown : hotel name 跟 address 進去 geocoding search 出來的 placeid latlng 都會不一樣
    # Warning : gmap place search 出來的結果都是 hotel name 進去 search 的結果!

    # BUGS : 還是會發生過近的兩個 hotel 不是同一間判斷是同一間的 BUG!!!! (源自於 booking 上 LatLng 值不準確緣故!!!)
    #     會造成 EX: FUNDI hotel latlng(gmap) 跟 東亞樓大旅社 latlng(booking) 較接近 , 跟 FUNDI hotel latlng(booking)) 反而較遠 !
    # 可能的解決方案 :
    # 1. 利用 Place id as search input , 並用 booking name as geocoding input , check latlng distance 做篩檢 , if distance < threshold (default=1) , pass
    # 2. If not pass 的 , 要是在 X < distance < Y range 內 , 則進行二度篩檢.
    # 3. 二度篩檢包含兩部分 A. 以 hotel name 進行 booking & gmap name 比對 ;
    #             B. 以 booking name 進行 geocode 搜索(可能找不到!) 找出 geocoding latlng , 比對 distance if < threshold
    # 4. 二度篩檢只要有一項通過即過關 ; 反之都沒通過(B找不到結果也算fail) 就不過關.

    # (11/24) 目前已解決大部分問題 , 目前剩餘 bugs :
    # 1. 距離太近的兩家 hotel 還是會誤判成同一間 (EX: 鬍子趣 and 沙龍)
    # 2. 不同名字但同一間的 (EX: TopL and 鼎立安) ,距離稍遠會造成烙高
    # 3. 在同一棟裡面無法處理 ,會判別成同一棟XD (沐藍輕旅 and 九月) XDDDD
    # 4. 中英字母判別相同須為連續字母 ( abcdef and fedcba 會被判別成同一個) : 待修正 string comparing

    # First step : get latlng in booking from place_id in gmaps , and check the latlng close or not
    place_id_gmap = hotel_obj.place_id
    booking_latlng, name_booking, address_booking = get_booking_latlng_by_hotel_or_placeid(place_id=place_id_gmap,
                                                                                           return_name_address=True)
    print(f'latlng_booking : {booking_latlng} , latlng_gmap : {hotel_obj.location} ')
    print(f'The booking name is : {name_booking}')

    # First step : Name judgement (gmap name vs. booking name)
    common_word_count, max_len_chars = find_common_word_2str(hotel_obj.name, name_booking)
    name_judge = common_word_count >= 2

    # Second step : distance judgement (by place id input and get latlng result)
    delta_distance = distance(hotel_obj.location, booking_latlng)
    distance_judge = delta_distance < distance_threshold

    print(f'Distance = {delta_distance} meters')
    print(f'There is {common_word_count} same words {max_len_chars}')

    if name_judge and distance_judge:
        hotel_obj.room_source = 'booking'
        hotel_obj.source_name = name_booking
        print(f'Booking contain this hotel : {name_booking}')

    else:
        hotel_obj.room_source = None
        hotel_obj.source_name = None
        print(f'This hotel {name_booking} is not the same hotel as {hotel_obj.name}!')


'''