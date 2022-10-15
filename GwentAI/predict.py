import time
from env import Env
from copy import deepcopy
from agent import VAnet
import torch
import cv2
import PySimpleGUI as sg
from utils import number_recognize, template_match, grab_screen


detection_dict = {'enemy_siege_unit': [622, 13, 704, 30], 'enemy_siege_attack': [443, 42, 50, 47],
                  'enemy_siege_horn': [498, 9, 118, 111], 'enemy_closed_unit': [622, 246, 705, 30],
                  'enemy_closed_attack': [446, 275, 46, 50], 'enemy_closed_horn': [498, 242, 116, 112],
                  'enemy_card': [236, 300, 41, 50], 'enemy_blood': [278, 304, 75, 39],
                  'enemy_ranged_unit': [621, 131, 707, 30], 'enemy_ranged_attack': [443, 155, 50, 49],
                  'enemy_ranged_horn': [497, 120, 117, 116], 'enemy_skill': [115, 66, 86, 114],
                  'self_siege_unit': [622, 617, 708, 30], 'self_siege_attack': [446, 646, 47, 45],
                  'self_siege_horn': [499, 610, 115, 112], 'self_turn': [8, 565, 58, 159],
                  'self_skill': [223, 772, 39, 36], 'self_closed_unit': [622, 383, 707, 30],
                  'self_closed_attack': [444, 405, 47, 50], 'self_closed_horn': [499, 378, 114, 107],
                  'self_card': [504, 736, 822, 96], 'self_blood': [277, 599, 78, 39],
                  'self_ranged_unit': [623, 501, 705, 30], 'self_ranged_attack': [446, 524, 46, 47],
                  'self_ranged_horn': [498, 491, 115, 109], 'weather': [122, 390, 250, 127]}

output_dict = {'decoy': '诱饵', 'horn': '号角', 'scorch': '烧灼', 'frost': '刺骨冰霜', 'fog': '蔽日浓雾', 'rain': '倾盆大雨',
               'clear': '晴天', 'geralt': '利维亚的杰洛特', 'ciri': '希里雅.菲欧娜.伊伦.雷安伦', 'yenn': '温格堡的叶奈法',
               'triss': '特莉丝.梅莉葛德', 'weilun': '维纶特瑞坦梅斯', 'vesemir': '维瑟米尔', 'zoltan': '卓尔坦.齐瓦',
               'regis': '爱米尔.雷吉斯.洛赫雷课.塔吉夫', 'dan': '丹德里恩', 'elf': '神秘的精灵', 'roche': '弗农.罗契',
               'yue_na': '约翰.纳塔利斯', 'yi_di': '伊斯特拉德.蒂森', 'philippa': '菲丽芭.艾哈特', 'paoshi': '抛石机',
               'daisimo': '戴斯摩', 'toushi': '投石机', 'nu': '弩炮', 'gongcheng': '攻城塔', 'weisi': '薇丝',
               'de_qi': '德内斯勒的齐格弗里德', 'kaila': '凯拉.梅兹', 'xi_de_tan': '席儿.德.坦沙维耶', 'wangzi': '斯坦尼斯王子',
               'julong': '克林菲德掠夺者巨龙猎手', 'heyi': '褐旗营医师', 'dj': '西吉斯蒙德.迪杰斯特拉', 'sa_ge': '萨宾娜.葛丽维希格',
               'xie_si': '谢尔顿.斯卡格斯', 'lanyi': '蓝衣铁卫突击队', 'ya_qi': '亚尔潘.齐格林', 'tale': '塔勒',
               'kelian': '可怜的步兵', 'rui_bubing': '瑞达尼亚步兵', 'kedewen': '科德温攻城专家', 'skill': '技能', 'end': '结束',
               '...': '...'}

outcome_dict = {(2, 2, 0): [0, 0, 0], (2, 1, 1): [1, 0, 0], (1, 2, -1): [-1, 0, 0],
                (1, 1, 1): [1, -1, 0], (1, 1, -1): [-1, 1, 0]}

device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
env = Env()
state_dim = 75
hidden_dim = 128
action_dim = 44
action_set = env.CardSet + ['skill', 'end']
model = VAnet(state_dim, hidden_dim, action_dim).to(device)
model.load_state_dict(torch.load('./model/model.pth'))
better = 0  # 用于判断小局胜负
action = '...'
start = False
end = False
layout = [[sg.Text(f'动作：{output_dict[action]}', key='action', size=(20, 2))],
            [sg.Button('开始', key='start', size=(5, 10)),sg.Button('结束', key='end', size=(5, 10))]]
window = sg.Window('GwentAI', layout, font=("宋体", 10), size=(100, 100))
while True:
    event, _ = window.read(timeout=1000)
    if event == 'start':
        start = True
    elif event == 'end':
        end = True
    if not start:
        continue
    if end:
        break
    flag = False
    time.sleep(10)  # 出牌时间
    while not flag:
        img = grab_screen()
        template = cv2.imread('./template/self_turn.png')
        x, y, w, h = detection_dict['self_turn']
        flag = (template_match(deepcopy(img)[y:y + h, x:x + w], ['self_turn'])[0] == 1)
        time.sleep(0.5)
    time.sleep(2)  # 等待“回合开始”的提示消失，或手动取消
    state_list = [0] * 75
    total_attack_list = []
    max_value = 0
    for i, item in enumerate(['enemy_closed', 'enemy_ranged', 'enemy_siege',
                              'self_closed', 'self_ranged', 'self_siege']):
        x, y, w, h = detection_dict[item + '_attack']
        attack = number_recognize('sum', deepcopy(img)[y:y + h, x:x + w])[0]
        state_list[4 * i + 0] = attack
        legend_attack = deepcopy(attack)
        x, y, w, h = detection_dict[item + '_unit']
        unit_list = number_recognize('field', deepcopy(img)[y:y + h, x:x + w])
        if unit_list:
            if max(unit_list) > max_value:
                max_value = max(unit_list)
            total_attack_list.append(unit_list)
            legend_attack -= sum(unit_list)
        state_list[4 * i + 1] = legend_attack
        x, y, w, h = detection_dict['weather']
        state_list[4 * i + 2] = template_match(deepcopy(img)[y:y + h, x:x + w], ['frost', 'fog', 'rain'])[i % 3]
        x, y, w, h = detection_dict[item + '_horn']
        state_list[4 * i + 3] = template_match(deepcopy(img)[y:y + h, x:x + w], ['horn'])[0]
    x, y, w, h = detection_dict['enemy_card']
    state_list[24] = number_recognize('card', deepcopy(img)[y:y + h, x:x + w])[0]
    x, y, w, h = detection_dict['self_card']
    state_list[25: 67] = template_match(deepcopy(img)[y:y + h, x:x + w], env.CardSet)
    x, y, w, h = detection_dict['enemy_skill']
    state_list[67] = template_match(deepcopy(img)[y:y + h, x:x + w], ['enemy_skill-True'])[0]
    x, y, w, h = detection_dict['self_skill']
    state_list[68] = template_match(deepcopy(img)[y:y + h, x:x + w], ['self_skill-True'])[0]
    x, y, w, h = detection_dict['enemy_blood']
    if template_match(deepcopy(img)[y:y + h, x:x + w], ['enemy_blood-2']):
        enemy_blood = 2
    else :
        enemy_blood = 1
    x, y, w, h = detection_dict['self_blood']
    if template_match(deepcopy(img)[y:y + h, x:x + w], ['self_blood-2']):
        self_blood = 2
    else :
        self_blood = 1
    if self_blood > enemy_blood:
        better = 1
    elif self_blood < enemy_blood:
        better = -1
    state_list[69: 72] = outcome_dict[(self_blood, enemy_blood, better)]
    enemy_num = 0
    for item in total_attack_list[:3]:
        enemy_num += item.count(max_value)
    self_num = 0
    for item in total_attack_list[3:]:
        self_num += item.count(max_value)
    state_list[72] = max_value
    state_list[73] = enemy_num
    state_list[74] = self_num
    state = torch.tensor(state_list, dtype=torch.float).to(device)
    action_space = (torch.tensor(state_list[25: 67] + [state[68]] + [1], dtype=torch.float).to(device) > 0)
    q_value = model(state).ravel()
    max_q = max(q_value[action_space.cpu().numpy() == 1]).item()
    for i in range(len(action_set)):
        if q_value[i] == max_q:
            break
    action = action_set[i]
    window['action'].update(f'动作：{output_dict[action]}')
window.close()
