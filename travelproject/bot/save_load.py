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

    pass