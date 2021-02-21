import matplotlib.pyplot as plt
import os
plt.switch_backend('agg') # https://blog.csdn.net/weixin_41678663/article/details/88866580

def save_price_trend_img(x , y , **kwargs):

    print("DEBUG in plot2:", x , y)

    plt.plot(x , y)
    plt.xticks(rotation=90)  # Rotates X-Axis Ticks by 45-degrees

    hotel_name = kwargs.get('hotel_name')
    queried_date = kwargs.get('queried_date')

    img_path = f'bot/trend_img/{hotel_name}_{queried_date}.png'
    print(f'DEBUG in img path : {img_path}')
    if os.path.isfile(img_path):
        print(f"File exist!!!")
    else:
        print(f"File Not exist!!!")
        plt.savefig(img_path)

    return img_path


if __name__  == '__main__':
    pass