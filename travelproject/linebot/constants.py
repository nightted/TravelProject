# GLOBAL　PARAMETERS

lng_1 = 102.516520*1000 # 1 longitude to meters
lat_1 = 110.740000*1000 # 1 latitude to meters

Admin_area_range_lng = [120.03786531340755 , 122.00991123709818] # range of lng in taiwan
Admin_area_range_lat = [21.871068186336803 , 25.30245194059663] # range of lng in taiwan

center_of_city = {
    "Tainan" : {'location' : {'lat': 22.9913113, 'lng': 120.198012} , 'city_en_to_cn' : '台南'} ,
    "Hsinchu" : {'location' : {'lat': 24.8015877, 'lng': 120.9715883} , 'city_en_to_cn' : '新竹'},
    "Hualien" : {'location' : {'lat': 23.9927385, 'lng': 121.6013407} , 'city_en_to_cn' : '花蓮'},
    "Yilan" : {'location' : {'lat': 24.6783841, 'lng': 121.7745634} , 'city_en_to_cn' : '宜蘭'},
}

KEY_PATH = 'C:/Users/h5904/PycharmProjects/TravelProject/travelproject/docs/API_KEY.txt'
BASE_BOOKING_URL = "https://www.booking.com/searchresults.zh-tw.html"