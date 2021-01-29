from googlesearch import search
from webpreview import web_preview

def get_search_result_by_resturant(resturant_obj):

    result_dict = {}
    for result_url in search(resturant_obj.name, stop=5, pause=2.0):
        if 'facebook' not in result_url:
            res = web_preview(result_url)
            preview_pic_url = res[2]
            result_dict.update(
                                {'result_url' : result_url,
                                'preview_pic_url' : preview_pic_url ,
                                'name': resturant_obj.name ,
                                'rating': resturant_obj.rating
                                }
                              )
            break

    print("DEBUG : " , result_dict)

    return result_dict

