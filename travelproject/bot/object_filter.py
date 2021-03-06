from functools import partial
from bot.tools import distance
from bot.constants import *

# filter method
def filter_by_criteria(obj, center, criteria, scan_shape='rectan'):
    """
    # function : To filter object fitted criteria

    :param obj: object to check if fit criteria
    :param center: search center , e.g. [lng, lat]
    :param criteria: search "radius"
    :param scan_shape: search shape

    :return: criteria fitted object
    """

    # Judge if whether it's hotel object,
    # if so , check room_source exist or not ; if not , set as True (belong to restaurant or con or other type place)
    if hasattr(obj, 'room_source'):
        selectable = False if not getattr(obj, 'room_source') else True  # for handling hotel type store , TODO (備忘): 這裡決定是否要選 booking room_source
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

    filtered_places = list(map(judge_func, objs))  # get # of points inside circle or rectangle
    filtered_places = list(filter(None.__ne__, filtered_places))  # filter None objects

    return filtered_places