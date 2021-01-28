from googlesearch import search
from webpreview import web_preview

def get_search_result_by_resturant(resturant_name):

    result = []
    for result_url in search(resturant_name, stop=5, pause=2.0):
        if 'facebook' not in result_url:
            res = web_preview(result_url)
            preview_pic_url = res[2]
            break

    return result_url , preview_pic_url


if __name__ == '__main__':

    query = '春川煎餅'
    result = get_search_result_by_resturant(query)

    print(result)