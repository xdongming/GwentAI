from card import Card
from copy import deepcopy
from random import shuffle, random
import numpy as np
import torch


class Env:
    def __init__(self):
        self.CardList = ['decoy', 'decoy', 'decoy', 'horn', 'horn', 'horn', 'scorch', 'scorch', 'scorch',
                         'frost', 'frost', 'frost', 'fog', 'fog', 'fog', 'rain', 'rain', 'rain',
                         'clear', 'clear', 'clear', 'geralt', 'ciri', 'yenn', 'triss', 'weilun', 'vesemir',
                         'zoltan', 'regis', 'dan', 'elf', 'roche', 'yue_na', 'yi_di', 'philippa', 'paoshi',
                         'paoshi', 'daisimo', 'toushi', 'toushi', 'nu', 'nu', 'gongcheng', 'weisi', 'de_qi',
                         'kaila', 'xi_de_tan', 'wangzi', 'julong', 'julong', 'julong', 'heyi', 'dj', 'sa_ge',
                         'xie_si', 'lanyi', 'lanyi', 'lanyi', 'ya_qi', 'tale', 'kelian', 'kelian', 'kelian',
                         'kelian', 'rui_bubing', 'rui_bubing', 'kedewen', 'kedewen', 'kedewen']
        self.CardSet = deepcopy(self.CardList)  # 构造和CardList顺序相同的集合（实际是列表）
        for i in reversed(range(len(self.CardSet) - 1)):
            if self.CardSet[i + 1] == self.CardSet[i]:
                self.CardSet.pop(i + 1)
        self.end = [np.array([1, 1, 0]), np.array([1, -1, 1]), np.array([-1, 1, 1]),
                    np.array([-1, -1, 0]), np.array([-1, 1, -1]), np.array([1, -1, -1])]
        self.device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

    def reset(self):
        self.clear_battleground()
        self.enemy_grave = []
        self.self_grave = []
        self.self_num = 10  # 记录已抽牌数，用于间谍抽牌计数
        self.enemy_num = 10
        self.enemy_cardlist = deepcopy(self.CardList)
        self.self_cardlist = deepcopy(self.CardList)
        shuffle(self.enemy_cardlist)
        shuffle(self.self_cardlist)
        self.enemy_card = self.enemy_cardlist[:10]
        self.self_card = self.self_cardlist[:10]

        self.enemy_end = False  # 对方是否结束
        self.self_end = False  # 己方是否结束
        self.enemy_skill = True
        self.self_skill = True
        self.outcome = np.array([0, 0, 0])  # 三小局结果
        self.round = 0  # 小局数
        self.self_reward = 0  # 总奖励
        self.enemy_reward = 0
        self.turn = True  # True表示是己方的回合，False表示对方的回合
        self.last_score = 0  # 上一回合的分数差
        return self.cal_state('self')

    def step(self, action):
        reward = 0
        if action == 'skill':
            if self.turn:
                self.self_skill = False
                self.self_siege['horn'] = True
            else:
                self.enemy_skill = False
                self.enemy_siege['horn'] = True
        elif action == 'end':
            if self.turn:
                self.self_end = True
            else:
                self.enemy_end = True
            self.turn = (not self.turn)
        # 卡牌作用
        else:
            card = Card(action)
            if self.turn:
                for i, item in enumerate(self.self_card):
                    if item == card.name:
                        self.self_card.pop(i)
                        break
                self.effect(card, 'self')
                if card.unit:
                    if card.skill == 'spy':
                        if card.type == 'closed':
                            self.enemy_closed['unit'].append(card)
                        elif card.type == 'ranged':
                            self.enemy_ranged['unit'].append(card)
                        elif card.type == 'siege':
                            self.enemy_siege['unit'].append(card)
                    else:
                        if card.type == 'closed':
                            self.self_closed['unit'].append(card)
                        elif card.type == 'ranged':
                            self.self_ranged['unit'].append(card)
                        elif card.type == 'siege':
                            self.self_siege['unit'].append(card)
            else:
                for i, item in enumerate(self.enemy_card):
                    if item == card.name:
                        self.enemy_card.pop(i)
                        break
                self.effect(card, 'enemy')
                if card.unit:
                    if card.skill != 'spy':
                        if card.type == 'closed':
                            self.enemy_closed['unit'].append(card)
                        elif card.type == 'ranged':
                            self.enemy_ranged['unit'].append(card)
                        elif card.type == 'siege':
                            self.enemy_siege['unit'].append(card)
                    else:
                        if card.type == 'closed':
                            self.self_closed['unit'].append(card)
                        elif card.type == 'ranged':
                            self.self_ranged['unit'].append(card)
                        elif card.type == 'siege':
                            self.self_siege['unit'].append(card)

        # 交换出牌
        if (not self.self_end) and (not self.enemy_end):
            self.turn = (not self.turn)

        # 计算连击奖励，如果连续两回合点数大于对方，奖励+1
        if self.cal_attack('self') - self.cal_attack('enemy') > 0:
            self.self_reward += 1
            if self.turn:
                reward += 1
        elif self.cal_attack('self') - self.cal_attack('enemy') < 0:
            self.enemy_reward += 1
            if not self.turn:
                reward += 1
        self.last_score = self.cal_attack('self') - self.cal_attack('enemy')

        # 判断小局是否结束
        if self.self_end and self.enemy_end:
            if self.cal_attack('self') > self.cal_attack('enemy'):
                self.outcome[self.round] = 1
            elif self.cal_attack('self') < self.cal_attack('enemy'):
                self.outcome[self.round] = -1
            else:
                if random() < 0.5:
                    self.outcome[self.round] = 1
                else:
                    self.outcome[self.round] = -1
                self.self_reward -= 10
                self.enemy_reward -= 10
                reward -= 10
            if len(self.self_card) > len(self.enemy_card):  # 牌数多的有奖励
                self.self_reward += 5
                if self.turn:
                    reward += 5
            elif len(self.self_card) < len(self.enemy_card):
                self.enemy_reward += 5
                if not self.turn:
                    reward += 5
            self.round += 1
            self.grave_update()  # 更新墓地
            self.clear_battleground()  # 清理战场
            self.self_end = False
            self.enemy_end = False
            self.last_score = 0
            self.turn = ((-1) ** self.round == 1)

        # 判断整局是否结束
        done = False
        for i, item in enumerate(self.end):
            if (self.outcome == item).all():
                done = True
                if 0 <= i <= 2:
                    self.self_reward += 25
                    self.enemy_reward -= 25
                    if self.turn:
                        reward += 25
                    else :
                        reward -= 25
                else:
                    self.enemy_reward += 25
                    self.self_reward -= 25
                    if self.turn:
                        reward -= 25
                    else :
                        reward += 25
                if len(self.self_card) > 0:
                    self.self_reward -= 10
                    if self.turn:
                        reward -= 10
                if len(self.enemy_card) > 0:
                    self.enemy_reward -= 10
                    if not self.turn:
                        reward -= 10
                break

        return self.cal_state('self'), self.cal_state('enemy'), reward, done

    def grave_update(self):
        for item in self.enemy_closed['unit']:
            if not item.legend:
                self.enemy_grave.append(item)
        for item in self.enemy_ranged['unit']:
            if not item.legend:
                self.enemy_grave.append(item)
        for item in self.enemy_siege['unit']:
            if not item.legend:
                self.enemy_grave.append(item)
        for item in self.self_closed['unit']:
            if not item.legend:
                self.self_grave.append(item)
        for item in self.self_ranged['unit']:
            if not item.legend:
                self.self_grave.append(item)
        for item in self.self_siege['unit']:
            if not item.legend:
                self.self_grave.append(item)

    def clear_battleground(self):
        self.enemy_closed = {'unit': [], 'weather': False, 'horn': False}
        self.enemy_ranged = {'unit': [], 'weather': False, 'horn': False}
        self.enemy_siege = {'unit': [], 'weather': False, 'horn': False}
        self.self_closed = {'unit': [], 'weather': False, 'horn': False}
        self.self_ranged = {'unit': [], 'weather': False, 'horn': False}
        self.self_siege = {'unit': [], 'weather': False, 'horn': False}

    def effect(self, card, obj='self'):
        if obj == 'self':
            type_list = [self.self_closed, self.self_ranged, self.self_siege]
            type_dict = {'closed': self.self_closed, 'ranged': self.self_ranged, 'siege': self.self_siege}
            index_dict = {0: self.self_closed, 1: self.self_ranged, 2: self.self_siege}
        else:
            type_list = [self.enemy_closed, self.enemy_ranged, self.enemy_siege]
            type_dict = {'closed': self.enemy_closed, 'ranged': self.enemy_ranged, 'siege': self.enemy_siege}
            index_dict = {0: self.enemy_closed, 1: self.enemy_ranged, 2: self.enemy_siege}
        value2key = lambda x, y: [*y.keys()][[*y.values()].index(x)]
        if card.skill == 'decoy':
            # 诱饵优先级：拉攻击最小的间谍
            spy_list = self.locate(obj, 'skill', 'spy')
            spy_attack = []
            for item in spy_list:
                spy_type, num = item
                spy_attack.append(type_dict[spy_type]['unit'][num].attack)
            if not spy_attack:
                return
            spy_type, num = spy_list[spy_attack.index(min(spy_attack))]
            temp_card = type_dict[spy_type]['unit'].pop(num)
            self.self_card.append(temp_card.name)
        elif card.skill == 'horn':
            attack_list = []
            for item in type_list:
                _, temp = self.cal_attack(obj, value2key(item, type_dict))
                if item['horn']:
                    attack_list.append(-1)
                else:
                    if value2key(item, type_dict) == 'closed' and self.locate(obj, 'name', 'dan') != []:
                        attack_list.append(2)  # 丹大师攻击力是2
                    else:
                        attack_list.append(sum(temp))
            max_attack = max(attack_list)
            index = index_dict[attack_list.index(max_attack)]
            index['horn'] = True
        elif card.skill == 'scorch':
            _, _, _, self_location, enemy_location = self.cal_best_attack()
            if self_location:
                closed = []
                ranged = []
                siege = []
                for item in self_location:
                    unit_type, num = item
                    if unit_type == 'closed':
                        closed.append(num)
                    elif unit_type == 'ranged':
                        ranged.append(num)
                    elif unit_type == 'siege':
                        siege.append(num)
                for i in reversed(closed):
                    temp_card = self.self_closed['unit'].pop(i)
                    self.self_grave.append(temp_card)
                for i in reversed(ranged):
                    temp_card = self.self_ranged['unit'].pop(i)
                    self.self_grave.append(temp_card)
                for i in reversed(siege):
                    temp_card = self.self_siege['unit'].pop(i)
                    self.self_grave.append(temp_card)
            if enemy_location:
                closed = []
                ranged = []
                siege = []
                for item in enemy_location:
                    unit_type, num = item
                    if unit_type == 'closed':
                        closed.append(num)
                    elif unit_type == 'ranged':
                        ranged.append(num)
                    elif unit_type == 'siege':
                        siege.append(num)
                for i in reversed(closed):
                    temp_card = self.enemy_closed['unit'].pop(i)
                    self.enemy_grave.append(temp_card)
                for i in reversed(ranged):
                    temp_card = self.enemy_ranged['unit'].pop(i)
                    self.enemy_grave.append(temp_card)
                for i in reversed(siege):
                    temp_card = self.enemy_siege['unit'].pop(i)
                    self.enemy_grave.append(temp_card)
        elif card.skill == 'burn_closed':
            if obj == 'self':
                closed_attack, closed_attack_list = self.cal_attack('enemy', 'closed')
                if closed_attack >= 10:
                    max_value = max(closed_attack_list)
                    if max_value == 0:
                        return
                    max_index = []
                    for i, item in enumerate(closed_attack_list):
                        if item == max_value:
                            max_index.append(i)
                    for i in reversed(max_index):
                        temp_card = self.enemy_closed['unit'].pop(i)
                        self.enemy_grave.append(temp_card)
            else:
                closed_attack, closed_attack_list = self.cal_attack('self', 'closed')
                if closed_attack >= 10:
                    max_value = max(closed_attack_list)
                    if max_value == 0:
                        return
                    max_index = []
                    for i, item in enumerate(closed_attack_list):
                        if item == max_value:
                            max_index.append(i)
                    for i in reversed(max_index):
                        temp_card = self.self_closed['unit'].pop(i)
                        self.self_grave.append(temp_card)
        elif card.skill == 'doctor':
            # 医生优先级：医生>间谍>抛石机>巨龙猎手>蓝衣铁卫>攻击力最高
            if obj == 'self':
                if not self.self_grave:
                    return
                # 医生拉医生，只有叶奈法拉褐旗营医师一种情况，因为叶奈法不进墓地
                location = self.locate(obj, 'name', 'heyi', grave=True)
                if location:
                    num = location[0]
                    temp_card = self.self_grave.pop(num)
                    self.self_siege['unit'].append(temp_card)
                    self.effect(temp_card, obj)
                    return
                spy_list = self.locate(obj, 'skill', 'spy', grave=True)
                if spy_list:
                    spy_attack = []
                    for num in spy_list:
                        spy_attack.append(self.self_grave[num].attack)
                    num = spy_list[spy_attack.index(min(spy_attack))]
                    temp_card = self.self_grave.pop(num)
                    if temp_card.type == 'closed':
                        self.enemy_closed['unit'].append(temp_card)
                    elif temp_card.type == 'ranged':
                        self.enemy_ranged['unit'].append(temp_card)
                    elif temp_card.type == 'siege':
                        self.enemy_siege['unit'].append(temp_card)
                    self.effect(temp_card, obj)
                    return
                location1 = self.locate(obj, 'name', 'paoshi', grave=True)
                location2 = self.locate(obj, 'name', 'paoshi')
                if location1 and location2:
                    num = location1[0]
                    temp_card = self.self_grave.pop(num)
                    self.self_siege['unit'].append(temp_card)
                    return
                location1 = self.locate(obj, 'name', 'julong', grave=True)
                location2 = self.locate(obj, 'name', 'julong')
                if location1 and location2:
                    num = location1[0]
                    temp_card = self.self_grave.pop(num)
                    self.self_ranged['unit'].append(temp_card)
                    return
                location1 = self.locate(obj, 'name', 'lanyi', grave=True)
                location2 = self.locate(obj, 'name', 'lanyi')
                if location1 and location2:
                    num = location1[0]
                    temp_card = self.self_grave.pop(num)
                    self.self_closed['unit'].append(temp_card)
                    return
                attack_list = []
                for item in self.self_grave:
                    attack_list.append(item.attack)
                temp_card = self.self_grave.pop(attack_list.index(max(attack_list)))
                type_dict[temp_card.type]['unit'].append(temp_card)
                self.effect(temp_card, obj)
            elif obj == 'enemy':
                if not self.enemy_grave:
                    return
                # 医生拉医生，只有叶奈法拉褐旗营医师一种情况，因为叶奈法不进墓地
                location = self.locate(obj, 'name', 'heyi', grave=True)
                if location:
                    num = location[0]
                    temp_card = self.enemy_grave.pop(num)
                    self.enemy_siege['unit'].append(temp_card)
                    self.effect(temp_card, obj)
                    return
                spy_list = self.locate(obj, 'skill', 'spy', grave=True)
                if spy_list:
                    spy_attack = []
                    for num in spy_list:
                        spy_attack.append(self.enemy_grave[num].attack)
                    num = spy_list[spy_attack.index(min(spy_attack))]
                    temp_card = self.enemy_grave.pop(num)
                    if temp_card.type == 'closed':
                        self.self_closed['unit'].append(temp_card)
                    elif temp_card.type == 'ranged':
                        self.self_ranged['unit'].append(temp_card)
                    elif temp_card.type == 'siege':
                        self.self_siege['unit'].append(temp_card)
                    self.effect(temp_card, obj)
                    return
                location1 = self.locate(obj, 'name', 'paoshi', grave=True)
                location2 = self.locate(obj, 'name', 'paoshi')
                if location1 and location2:
                    num = location1[0]
                    temp_card = self.enemy_grave.pop(num)
                    self.enemy_siege['unit'].append(temp_card)
                    return
                location1 = self.locate(obj, 'name', 'julong', grave=True)
                location2 = self.locate(obj, 'name', 'julong')
                if location1 and location2:
                    num = location1[0]
                    temp_card = self.enemy_grave.pop(num)
                    self.enemy_ranged['unit'].append(temp_card)
                    return
                location1 = self.locate(obj, 'name', 'lanyi', grave=True)
                location2 = self.locate(obj, 'name', 'lanyi')
                if location1 and location2:
                    num = location1[0]
                    temp_card = self.enemy_grave.pop(num)
                    self.enemy_closed['unit'].append(temp_card)
                    return
                attack_list = []
                for item in self.enemy_grave:
                    attack_list.append(item.attack)
                temp_card = self.enemy_grave.pop(attack_list.index(max(attack_list)))
                type_dict[temp_card.type]['unit'].append(temp_card)
                self.effect(temp_card, obj)
        elif card.skill == 'frost':
            self.enemy_closed['weather'] = True
            self.self_closed['weather'] = True
        elif card.skill == 'fog':
            self.enemy_ranged['weather'] = True
            self.self_ranged['weather'] = True
        elif card.skill == 'rain':
            self.enemy_siege['weather'] = True
            self.self_siege['weather'] = True
        elif card.skill == 'clear':
            self.enemy_closed['weather'] = False
            self.enemy_ranged['weather'] = False
            self.enemy_siege['weather'] = False
            self.self_closed['weather'] = False
            self.self_ranged['weather'] = False
            self.self_siege['weather'] = False
        elif card.skill == 'spy':
            if obj == 'self':
                self.self_card.append(self.self_cardlist[self.self_num + 1])
                self.self_card.append(self.self_cardlist[self.self_num + 2])
                self.self_num += 2
            elif obj == 'enemy':
                self.enemy_card.append(self.enemy_cardlist[self.enemy_num + 1])
                self.enemy_card.append(self.enemy_cardlist[self.enemy_num + 2])
                self.enemy_num += 2

    def locate(self, obj, goal, name, grave=False):
        location = []
        if not grave:
            if goal == 'name':
                if obj == 'self':
                    for i, item in enumerate(self.self_closed['unit']):
                        if item.name == name:
                            location.append(['closed', i])
                    for i, item in enumerate(self.self_ranged['unit']):
                        if item.name == name:
                            location.append(['ranged', i])
                    for i, item in enumerate(self.self_siege['unit']):
                        if item.name == name:
                            location.append(['siege', i])
                else:
                    for i, item in enumerate(self.enemy_closed['unit']):
                        if item.name == name:
                            location.append(['closed', i])
                    for i, item in enumerate(self.enemy_ranged['unit']):
                        if item.name == name:
                            location.append(['ranged', i])
                    for i, item in enumerate(self.enemy_siege['unit']):
                        if item.name == name:
                            location.append(['siege', i])
            elif goal == 'skill':
                if obj == 'self':
                    for i, item in enumerate(self.self_closed['unit']):
                        if item.skill == name:
                            location.append(['closed', i])
                    for i, item in enumerate(self.self_ranged['unit']):
                        if item.skill == name:
                            location.append(['ranged', i])
                    for i, item in enumerate(self.self_siege['unit']):
                        if item.skill == name:
                            location.append(['siege', i])
                else:
                    for i, item in enumerate(self.enemy_closed['unit']):
                        if item.skill == name:
                            location.append(['closed', i])
                    for i, item in enumerate(self.enemy_ranged['unit']):
                        if item.skill == name:
                            location.append(['ranged', i])
                    for i, item in enumerate(self.enemy_siege['unit']):
                        if item.skill == name:
                            location.append(['siege', i])
            elif goal == 'attack':
                if obj == 'self':
                    for i, item in enumerate(self.self_closed['unit']):
                        if item.attack == name:
                            location.append(['closed', i])
                    for i, item in enumerate(self.self_ranged['unit']):
                        if item.attack == name:
                            location.append(['ranged', i])
                    for i, item in enumerate(self.self_siege['unit']):
                        if item.attack == name:
                            location.append(['siege', i])
                else:
                    for i, item in enumerate(self.enemy_closed['unit']):
                        if item.attack == name:
                            location.append(['closed', i])
                    for i, item in enumerate(self.enemy_ranged['unit']):
                        if item.attack == name:
                            location.append(['ranged', i])
                    for i, item in enumerate(self.enemy_siege['unit']):
                        if item.attack == name:
                            location.append(['siege', i])
        else:
            if goal == 'name':
                if obj == 'self':
                    for i, item in enumerate(self.self_grave):
                        if item.name == name:
                            location.append(i)
                else:
                    for i, item in enumerate(self.enemy_grave):
                        if item.name == name:
                            location.append(i)
            elif goal == 'skill':
                if obj == 'self':
                    for i, item in enumerate(self.self_grave):
                        if item.skill == name:
                            location.append(i)
                else:
                    for i, item in enumerate(self.enemy_grave):
                        if item.skill == name:
                            location.append(i)
            elif goal == 'attack':
                if obj == 'self':
                    for i, item in enumerate(self.self_grave):
                        if item.attack == name:
                            location.append(i)
                else:
                    for i, item in enumerate(self.enemy_grave):
                        if item.attack == name:
                            location.append(i)

        return location

    def cal_state(self, obj='self'):
        type_dict = {'enemy_closed': 'closed', 'enemy_ranged': 'ranged', 'enemy_siege': 'siege',
                     'self_closed': 'closed', 'self_ranged': 'ranged', 'self_siege': 'siege'}
        obj_dict = {'enemy_closed': 'enemy', 'enemy_ranged': 'enemy', 'enemy_siege': 'enemy',
                    'self_closed': 'self', 'self_ranged': 'self', 'self_siege': 'self'}
        field_dict = {'enemy_closed': self.enemy_closed, 'enemy_ranged': self.enemy_ranged, 'enemy_siege': self.enemy_siege,
                      'self_closed': self.self_closed, 'self_ranged': self.self_ranged, 'self_siege': self.self_siege}
        state_list = []
        if obj == 'self':
            for item in ['enemy_closed', 'enemy_ranged', 'enemy_siege',
                         'self_closed', 'self_ranged', 'self_siege']:
                attack_sum, attack_list = self.cal_attack(obj_dict[item], type_dict[item])
                state_list.append(attack_sum)
                state_list.append(attack_sum - sum(attack_list))
                state_list.append(field_dict[item]['horn'])
                state_list.append(field_dict[item]['weather'])
            state_list.append(len(self.enemy_card))
            card_list = [0] * 42
            for item in self.self_card:
                card_list[self.CardSet.index(item)] += 1
            state_list += card_list
            state_list.append(self.enemy_skill)
            state_list.append(self.self_skill)
            state_list += self.outcome.tolist()
            max_value, self_value, enemy_value, _, _ = self.cal_best_attack()
            state_list.append(max_value)
            state_list.append(enemy_value)
            state_list.append(self_value)
        elif obj == 'enemy':
            for item in ['self_closed', 'self_ranged', 'self_siege',
                         'enemy_closed', 'enemy_ranged', 'enemy_siege']:
                attack_sum, attack_list = self.cal_attack(obj_dict[item], type_dict[item])
                state_list.append(attack_sum)
                state_list.append(attack_sum - sum(attack_list))
                state_list.append(field_dict[item]['horn'])
                state_list.append(field_dict[item]['weather'])
            state_list.append(len(self.self_card))
            card_list = [0] * 42
            for item in self.enemy_card:
                card_list[self.CardSet.index(item)] += 1
            state_list += card_list
            state_list.append(self.self_skill)
            state_list.append(self.enemy_skill)
            state_list += (-1 * self.outcome).tolist()
            max_value, self_value, enemy_value, _, _ = self.cal_best_attack()
            state_list.append(max_value)
            state_list.append(self_value)
            state_list.append(enemy_value)

        return state_list

    def cal_attack(self, obj='self', unit_type='all'):
        if obj == 'self':
            type_dict = {'closed': self.self_closed, 'ranged': self.self_ranged, 'siege': self.self_siege}
        elif obj == 'enemy':
            type_dict = {'closed': self.enemy_closed, 'ranged': self.enemy_ranged, 'siege': self.enemy_siege}
        attack_list = []
        attack_sum = 0
        if unit_type != 'all':
            # 对丹大师和科德温的攻击力计算有较小偏差
            weather = type_dict[unit_type]['weather']
            horn = type_dict[unit_type]['horn']
            horn_dan = (unit_type == 'closed') and (self.locate(obj, 'name', 'dan') != [])
            boost = False
            boost_list = self.locate(obj, 'skill', 'boost')
            for item in boost_list:
                item_type, _ = item
                if item_type == unit_type:
                    boost = True
            for item in type_dict[unit_type]['unit']:
                if item.legend:
                    attack_sum += item.attack
                    attack_list.append(0)  # 英雄显示攻击力为0，但计算总和时为正常值
                else:
                    if item.skill == 'bond':
                        bond_attack = item.attack
                        bond_num = 0
                        for temp_item in type_dict[unit_type]['unit']:
                            if temp_item.name == item.name:
                                bond_num += 1
                        item_attack = ((bond_attack ** (1 - weather)) * bond_num + boost) * (
                                2 ** ((horn or horn_dan) + 0))
                        attack_sum += item_attack
                        attack_list.append(item_attack)
                    else:
                        item_attack = ((item.attack ** (1 - weather)) + boost) * (2 ** ((horn or horn_dan) + 0))
                        attack_sum += item_attack
                        attack_list.append(item_attack)
            return attack_sum, attack_list
        else:
            closed_attack, _ = self.cal_attack(obj, 'closed')
            ranged_attack, _ = self.cal_attack(obj, 'ranged')
            siege_attack, _ = self.cal_attack(obj, 'siege')
            return closed_attack + ranged_attack + siege_attack

    # 计算场上最大攻击力单位点数、个数、位置
    def cal_best_attack(self):
        _, self_closed_attack = self.cal_attack('self', 'closed')
        _, self_ranged_attack = self.cal_attack('self', 'ranged')
        _, self_siege_attack = self.cal_attack('self', 'siege')
        _, enemy_closed_attack = self.cal_attack('enemy', 'closed')
        _, enemy_ranged_attack = self.cal_attack('enemy', 'ranged')
        _, enemy_siege_attack = self.cal_attack('enemy', 'siege')
        self_attack = self_closed_attack + self_ranged_attack + self_siege_attack
        enemy_attack = enemy_closed_attack + enemy_ranged_attack + enemy_siege_attack
        total = self_attack + enemy_attack
        if total:
            max_value = max(total)
            if max_value == 0:
                self_location = []
                enemy_location = []
            else:
                self_location = self.locate('self', 'attack', max_value)
                enemy_location = self.locate('enemy', 'attack', max_value)
        else:
            max_value = 0
            self_location = []
            enemy_location = []

        return max_value, len(self_location), len(enemy_location), self_location, enemy_location

    def cal_action_space(self, obj='self'):
        if obj == 'self':
            action_set = deepcopy(self.self_card)
            action_set = [*set(action_set)]
            if self.self_skill and (not self.self_siege['horn']):
                action_set.append('skill')
            if not self.self_end:
                action_set.append('end')
            if self.self_closed['horn'] and self.self_ranged['horn'] and self.self_siege['horn']:
                if 'horn' in action_set:
                    action_set.remove('horn')
            location = self.locate(obj, 'skill', 'spy')
            if not location:
                if 'decoy' in action_set:
                    action_set.remove('decoy')
        elif obj == 'enemy':
            action_set = deepcopy(self.enemy_card)
            action_set = [*set(action_set)]
            if self.enemy_skill and (not self.enemy_siege['horn']):
                action_set.append('skill')
            if not self.enemy_end:
                action_set.append('end')
            if self.enemy_closed['horn'] and self.enemy_ranged['horn'] and self.enemy_siege['horn']:
                if 'horn' in action_set:
                    action_set.remove('horn')
            location = self.locate(obj, 'skill', 'spy')
            if not location:
                if 'decoy' in action_set:
                    action_set.remove('decoy')
        action_space = [False] * 44
        if 'skill' in action_set:
            action_space[-2] = True
        if 'end' in action_set:
            action_space[-1] = True
        for i, item in enumerate(self.CardSet):
            if item in action_set:
                action_space[i] = True

        return torch.tensor(action_space, dtype=torch.float).to(self.device)
