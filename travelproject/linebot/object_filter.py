from functools import partial
from linebot.tools import distance
from linebot.constants import *

# filter method
def filter_by_criteria(obj, center, criteria, scan_shape='rectan'):
    """
    # function : To filter object fitted criteria

    :param obj: object to check if fit criteria
    :param center: search center
    :param criteria: search "radius"
    :param scan_shape: search shape

    :return: criteria fitted object
    """

    # Judge if whether it's hotel object,
    # if so , check room_source exist or not ; if not , set as True (belong to restaurant or con)
    if hasattr(obj, 'room_source'):
        selectable = False if not getattr(obj, 'room_source') else True  # for handling hotel type store
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