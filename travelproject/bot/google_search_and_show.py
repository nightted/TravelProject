from googlesearch import search
from webpreview import web_preview

def get_search_result_by_resturant(resturant_obj):


    result_dict = {}
    for result_url in search(resturant_obj.name, num=3 , pause=2.0):
        if 'facebook' not in result_url:

            #print('DEBUG in web_preview:' , result_url)

            res = web_preview(result_url)
            preview_pic_url = res[2]
            if not preview_pic_url:
                continue

            result_dict.update(
                                {'result_url' : result_url,
                                 'preview_pic_url' : preview_pic_url ,
                                 'name': resturant_obj.name ,
                                 'rating': resturant_obj.rating,
                                 'position_xy': [resturant_obj.lng , resturant_obj.lat]
                                }
                              )
            break

    print("DEBUG in result_dict : " , result_dict)

    return result_dict

