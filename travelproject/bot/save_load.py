import pickle
from bot.models import Resturant

def save_pkl(path, data):
    with open(path, "wb") as pkl:
        pickle.dump(data, pkl)

def load_pkl(path):
    with open(path, "rb") as pkl:
        data = pickle.load(pkl)
    return data

if __name__  == '__main__' :

    abs_file_paths = {}
    Tainan_all_objects = {}
    cur_path = 'C:/Users/h5904/PycharmProjects/Travel_Recommend_project/Travel_Recommend/city data/Tainan/dict data/Tainan_all_objects_dict'
    Tainan_all_objects = load_pkl(cur_path)

    gruels_dicts = Tainan_all_objects['gruel']
    for gruel_dict in gruels_dicts:
       obj = Resturant.create_obj_by_dict(gruel_dict)
       obj.save()



