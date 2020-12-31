import datetime

# GLOBAL PARAMETER
lng_1 = 102.516520*1000 # 1 longitude to meters
lat_1 = 110.740000*1000 # 1 latitude to meters


# find if english word in string
def find_english_char(string):
    '''
    function : find english alphabet in string or not

    input :
      #string : the string mix with alphabet in

    rtype :
      #bool : if True , means alphabet in

    '''
    for chr in string:
        if chr.encode('UTF-8').isalpha():
            return True
    return False


# get the all continus digits in string
def get_digits(text):
    '''
    function : get all successive digits in string

    input :
      #text : the string mix with digit in

    rtype :
      #collect : list of successive digits in string

    '''
    dummy = ''
    collect = []
    for idx, chr in enumerate(text):

        if chr == ',':
            continue

        if chr.isdigit():
            dummy += chr
        if not chr.isdigit() or idx == len(text) - 1:
            if len(dummy) > 0:
                collect.append(dummy)
                dummy = ''
            else:
                continue
    collect = [ int(num_str) for num_str in collect]

    if len(collect) == 1 :
        return collect[0] # if only one number in , directly return it

    return collect

def get_date_string(target_day = None , delta_day=0):
    '''
    # function : get +/- delta day of target day

    input :

    target_day : the day you want to search , likes '2020-12-10'

    delta_day : the range +/- of target day

    rtype :

    date: like '2020-12-10'
    '''
    if not target_day:
        target_day = datetime.datetime.now().strftime("%Y-%m-%d") # if not assign target day , using today as target day

    day = target_day.split('-')
    y , m , d = int(day[0]) , int(day[1]) , int(day[2])
    return (datetime.datetime(y , m , d) + datetime.timedelta(days=delta_day)).strftime("%Y-%m-%d")


def distance(a, b):
    '''
    get distnace of two point (in unit of meter)
    '''
    a_x, a_y = a[0], a[1]
    b_x, b_y = b[0], b[1]
    delta_x_meter = (a_x - b_x) * lng_1
    delta_y_meter = (a_y - b_y) * lat_1

    return ((delta_x_meter) ** 2 + (delta_y_meter) ** 2) ** 0.5