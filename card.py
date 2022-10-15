class Card:
    def __init__(self, name):
        self.name = name
        if self.name == 'decoy':     #诱饵不能被作用，没有攻击，视为非单位
            self.skill = 'decoy'
            self.unit = False

        elif self.name == 'horn':
            self.skill = 'horn'
            self.unit = False

        elif self.name == 'scorch':
            self.skill = 'scorch'
            self.unit = False

        elif self.name == 'frost':
            self.skill = 'frost'
            self.unit = False

        elif self.name == 'fog':
            self.skill = 'fog'
            self.unit = False

        elif self.name == 'rain':
            self.skill = 'rain'
            self.unit = False

        elif self.name == 'clear':
            self.skill = 'clear'
            self.unit = False

        elif self.name == 'geralt':
            self.legend = True
            self.skill = False
            self.unit = True
            self.type = 'closed'
            self.attack = 15

        elif self.name == 'ciri':
            self.legend = True
            self.skill = False
            self.unit = True
            self.type = 'closed'
            self.attack = 15

        elif self.name == 'yenn':
            self.legend = True
            self.skill = 'docter'
            self.unit = True
            self.type = 'ranged'
            self.attack = 7

        elif self.name == 'triss':
            self.legend = True
            self.skill = False
            self.unit = True
            self.type = 'closed'
            self.attack = 7

        elif self.name == 'weilun':
            self.legend = False
            self.skill = 'burn_closed'
            self.unit = True
            self.type = 'closed'
            self.attack = 7

        elif self.name == 'vesemir':
            self.legend = False
            self.skill = False
            self.unit = True
            self.type = 'closed'
            self.attack = 6

        elif self.name == 'zoltan':
            self.legend = False
            self.skill = False
            self.unit = True
            self.type = 'closed'
            self.attack = 5

        elif self.name == 'regis':
            self.legend = False
            self.skill = False
            self.unit = True
            self.type = 'closed'
            self.attack = 5

        elif self.name == 'dan':
            self.legend = False
            self.skill = 'horn'
            self.unit = True
            self.type = 'closed'
            self.attack = 2

        elif self.name == 'elf':
            self.legend = True
            self.skill = 'spy'
            self.unit = True
            self.type = 'closed'
            self.attack = 0

        elif self.name == 'roche':
            self.legend = True
            self.skill = False
            self.unit = True
            self.type = 'closed'
            self.attack = 10

        elif self.name == 'yue_na':
            self.legend = True
            self.skill = False
            self.unit = True
            self.type = 'closed'
            self.attack = 10

        elif self.name == 'yi_di':
            self.legend = True
            self.skill = False
            self.unit = True
            self.type = 'closed'
            self.attack = 10

        elif self.name == 'philippa':
            self.legend = True
            self.skill = False
            self.unit = True
            self.type = 'ranged'
            self.attack = 10

        elif self.name == 'paoshi':
            self.legend = False
            self.skill = 'bond'
            self.unit = True
            self.type = 'siege'
            self.attack = 8

        elif self.name == 'daisimo':
            self.legend = False
            self.skill = False
            self.unit = True
            self.type = 'ranged'
            self.attack = 6

        elif self.name == 'toushi':
            self.legend = False
            self.skill = False
            self.unit = True
            self.type = 'siege'
            self.attack = 6

        elif self.name == 'nu':
            self.legend = False
            self.skill = False
            self.unit = True
            self.type = 'siege'
            self.attack = 6

        elif self.name == 'gongcheng':
            self.legend = False
            self.skill = False
            self.unit = True
            self.type = 'siege'
            self.attack = 6

        elif self.name == 'weisi':
            self.legend = False
            self.skill = False
            self.unit = True
            self.type = 'closed'
            self.attack = 5

        elif self.name == 'de_qi':
            self.legend = False
            self.skill = False
            self.unit = True
            self.type = 'closed'
            self.attack = 5

        elif self.name == 'kaila':
            self.legend = False
            self.skill = False
            self.unit = True
            self.type = 'ranged'
            self.attack = 5

        elif self.name == 'xi_de_tan':
            self.legend = False
            self.skill = False
            self.unit = True
            self.type = 'ranged'
            self.attack = 5

        elif self.name == 'wangzi':
            self.legend = False
            self.skill = 'spy'
            self.unit = True
            self.type = 'closed'
            self.attack = 5

        elif self.name == 'julong':
            self.legend = False
            self.skill = 'bond'
            self.unit = True
            self.type = 'ranged'
            self.attack = 5

        elif self.name == 'heyi':
            self.legend = False
            self.skill = 'doctor'
            self.unit = True
            self.type = 'siege'
            self.attack = 5

        elif self.name == 'dj':
            self.legend = False
            self.skill = 'spy'
            self.unit = True
            self.type = 'closed'
            self.attack = 4

        elif self.name == 'sa_ge':
            self.legend = False
            self.skill = False
            self.unit = True
            self.type = 'ranged'
            self.attack = 4

        elif self.name == 'xie_si':
            self.legend = False
            self.skill = False
            self.unit = True
            self.type = 'ranged'
            self.attack = 4

        elif self.name == 'lanyi':
            self.legend = False
            self.skill = 'bond'
            self.unit = True
            self.type = 'closed'
            self.attack = 4

        elif self.name == 'ya_qi':
            self.legend = False
            self.skill = False
            self.unit = True
            self.type = 'closed'
            self.attack = 2

        elif self.name == 'tale':
            self.legend = False
            self.skill = 'spy'
            self.unit = True
            self.type = 'siege'
            self.attack = 1

        elif self.name == 'kelian':
            self.legend = False
            self.skill = 'bond'
            self.unit = True
            self.type = 'closed'
            self.attack = 1

        elif self.name == 'rui_bubing':
            self.legend = False
            self.skill = False
            self.unit = True
            self.type = 'closed'
            self.attack = 1

        elif self.name == 'kedewen':
            self.legend = False
            self.skill = 'boost'
            self.unit = True
            self.type = 'siege'
            self.attack = 1