from copy import deepcopy
import cv2
import numpy as np
import win32con
import win32gui
import win32ui


def number_recognize(loc_type, img):
    thred_dict = {'sum': [0.55, 0.55, 0.15, 0.45, 0.35, 0.45, 0.45, 0.37, 0.45, 0.4],
                  'field': [0.7, 0.65, 0.65, 0.7, 0.65, 0.65, 0.7, 0.6, 0.45, 0.65],
                  'card': [0.75, 0.8, 0.75, 0.8, 0.75, 0.75, 0.75, 0.75, 0.8, 0.8]}
    path_dict = {'sum': 'attack', 'field': 'unit', 'card': 'card'}
    params_dict = {'sum': [40, 110, 180], 'field': [40, 180, 180], 'card': [50, 245, 245]}
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thred_list = thred_dict[loc_type]
    temp_type = path_dict[loc_type]
    a, b, c = params_dict[loc_type]
    if loc_type in ['field', 'sum']:
        img_gray = binary(img_gray, a, b, c)
    loc_dict = {}
    num_list = []
    for i in range(10):
        path = './template/' + temp_type + '-' + str(i) + '.png'
        template = cv2.imread(path)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        if loc_type in ['field', 'sum']:
            template_gray = binary(template_gray, a, b, c)
        # ret, template_binary = cv2.threshold(template_gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        res = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        threshold = thred_list[i]
        loc = np.where(res >= threshold)
        x_list = []
        for pt in zip(*loc[::-1]):
            x, y = pt
            x_list.append(x)
        # 剔除相近的重复判定的框
        x_list = [*set(x_list)]
        flag = True
        while flag:
            flag = False
            for item in x_list:
                x_temp_list = deepcopy(x_list)
                x_temp_list.remove(item)
                pop_list = []
                for temp_item in x_temp_list:
                    if abs(item - temp_item) <= 5:
                        pop_list.append(x_list.index(temp_item))
                        flag = True
                for j in reversed(pop_list):
                    x_list.pop(j)
                if flag:
                    break
        loc_dict[str(i)] = x_list
        num_list += x_list
    if num_list:
        flag = True
        num_list.sort()
        result_list = []
        i = 0
        while i < len(num_list) - 1:
            temp_result = ''
            temp_result += value2key(num_list[i], loc_dict)
            if num_list[i + 1] - num_list[i] <= 20:
                while i < len(num_list) - 1 and num_list[i + 1] - num_list[i] <= 20:
                    temp_result += value2key(num_list[i + 1], loc_dict)
                    i += 1
                    if i == len(num_list) - 1:
                        flag = False
            else:
                i += 1
            result_list.append(eval(temp_result))
        if flag or i == 0:
            result_list.append(eval(value2key(num_list[i], loc_dict)))
        return result_list
    else:
        return []


def value2key(value, Dict):
    for item in [*Dict.keys()]:
        if value in Dict[item]:
            return item


def binary(gray, a, b, c):
    for i in range(gray.shape[0]):
        for j in range(gray.shape[1]):
            if a <= gray[i, j] < b:
                gray[i, j] = 0
            elif b <= gray[i, j] <= c:
                gray[i, j] = 255
            elif gray[i, j] <= 15:
                gray[i, j] = 0
            elif gray[i, j] >= 245:
                gray[i, j] = 255
            else:
                gray[i, j] = 255
    return gray


def template_match(img, template_name, thred=0.9):
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    flag_list = [0] * len(template_name)
    for i, item in enumerate(template_name):
        x_list = []
        if item in ['nu', 'rui_bubing', 'toushi']:
            path_list = ['./template/' + item + '-1' + '.png', './template/' + item + '-2' + '.png']
        else:
            path_list = ['./template/' + item + '.png']
        for path in path_list:
            template = cv2.imread(path)
            if item in ['enemy_blood-1', 'enemy_blood-2', 'self_blood-1', 'self_blood-2']:
                img_gray = img[:, :, 2]
                template_gray = template[:, :, 2]
                thred = 0.95
            else:
                template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            res = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= thred)
            _x_list = []
            if loc[0].tolist():
                for pt in zip(*loc[::-1]):
                    x, y = pt
                    _x_list.append(x)
                _x_list = [*set(_x_list)]
                flag = True
                while flag:
                    flag = False
                    for item in _x_list:
                        x_temp_list = deepcopy(_x_list)
                        x_temp_list.remove(item)
                        pop_list = []
                        for temp_item in x_temp_list:
                            if abs(item - temp_item) <= 5:
                                pop_list.append(_x_list.index(temp_item))
                                flag = True
                        for j in reversed(pop_list):
                            _x_list.pop(j)
                        if flag:
                            break
            x_list += _x_list
        flag_list[i] += len(x_list)
    return flag_list


def grab_screen():
    width = 1680
    height = 945
    left = 0
    top = 52
    hwnd = win32gui.FindWindow(None, 'The Witcher 3')
    hwindc = win32gui.GetWindowDC(hwnd)
    srcdc = win32ui.CreateDCFromHandle(hwindc)
    memdc = srcdc.CreateCompatibleDC()
    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(srcdc, width, height)
    memdc.SelectObject(bmp)
    memdc.BitBlt((0, 0), (width, height), srcdc, (left, top), win32con.SRCCOPY)

    signedIntsArray = bmp.GetBitmapBits(True)
    img = np.fromstring(signedIntsArray, dtype='uint8')
    img.shape = (height, width, 4)

    srcdc.DeleteDC()
    memdc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwindc)
    win32gui.DeleteObject(bmp.GetHandle())

    return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)


def moving_average(a, window_size):
    cumulative_sum = np.cumsum(np.insert(a, 0, 0))
    middle = (cumulative_sum[window_size:] - cumulative_sum[:-window_size]) / window_size
    r = np.arange(1, window_size-1, 2)
    begin = np.cumsum(a[:window_size-1])[::2] / r
    end = (np.cumsum(a[:-window_size:-1])[::2] / r)[::-1]
    return np.concatenate((begin, middle, end))
