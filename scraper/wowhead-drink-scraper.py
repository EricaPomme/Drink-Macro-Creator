import re
import shutil
import sys
import time
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup as bs

### Begin configuration ###
DISCARD_BUFF_FOOD = True              # Discard buff food
DISCARD_NO_MANA = True                # Discard items with no mana regen
SHORTEN = True                        # Shorten values: 1000 -> 1k
SHOW_PROGRESS = True                  # Show progress indicator
REPORT_FAILURES = True                # If we can't process an item, print to stderr at end of run
RATE_LIMIT = 0                        # Rate limit in seconds
BASE_URL = "https://www.wowhead.com/" # Base URL for item links
SEARCH_ITEMS = [                      # List of itemids to search
    # Dragonflight (10.2.0)
    207054, 209019,
    # Dragonflight (10.1.7)
    ## Nothing added this patch
    # Dragonflight (10.1.5)
    207956, 208448, 206474,
    # Dragonflight (10.0.0 to 10.1.0)
    205684, 194691, 204072, 197794, 197792, 201422, 197769, 197795, 204845,
    201420, 197771, 204342, 197766, 194683, 194690, 197784, 198356, 197767,
    197778, 197788, 201089, 194681, 197783, 197786, 197772, 197770, 197785,
    197781, 197782, 200885, 197793, 197776, 200891, 197779, 194684, 197760,
    200886, 200759, 200889, 200895, 205690, 201090, 201047, 197790, 197780,
    197789, 197768, 201046, 200887, 200871, 194685, 202290, 200904, 197763,
    197787, 197774, 201469, 201045, 200897, 204790, 200894, 197762, 197855,
    197856, 197758, 197761, 200953, 201327, 197777, 202108, 204235, 200901,
    197791, 200892, 197759, 200902, 200888, 200899, 201725, 206139, 200966,
    200903, 194680, 200890, 202314, 191917, 202315, 205794, 206141, 200893,
    196582, 197775, 205793, 200305, 200680, 200898, 200900, 201721, 206140,
    191919, 205417, 195463, 196440, 197853, 198440, 200896, 201416, 201813,
    202063, 191056, 191064, 195456, 195457, 197851, 197852, 204730, 206144,
    198441, 201697, 206142, 191052, 191063, 195466, 200862, 205693, 206143,
    191050, 191051, 191062, 194682, 194686, 194689, 196540, 196583, 197848,
    198831, 200304, 200856, 201415, 191053, 194695, 195455, 195465, 196585,
    198832, 200619, 201419, 201820, 194688, 195460, 195462, 195464, 196584,
    197850, 197858, 198833, 200099, 201398, 201413, 202033, 204277, 204729,
    205692, 191918, 193859, 194693, 195458, 197847, 197854, 198830, 200681,
    201417, 201698, 204846, 194692, 194694, 195459, 197849, 197857, 200855,
    202401,
    # Shadowlands (9.0.1 to 9.2.7)
    190880, 187648, 172063, 179271, 172043, 178915, 173859, 172050, 172069,
    172045, 172051, 177040, 172047, 172049, 172041, 172042, 179283, 179287,
    182459, 180788, 172046, 184690, 172060, 172062, 180006, 172061, 178219,
    178546, 172044, 179992, 179276, 178535, 179023, 183597, 190953, 172040,
    172048, 178252, 179285, 180377, 180409, 182121, 179017, 180410, 182737,
    186704, 174285, 178216, 178222, 178228, 184682, 186725, 178227, 178540,
    178545, 179019, 180430, 182592, 186726, 173759, 174281, 178247, 178538,
    179020, 184201, 172064, 172068, 178220, 178225, 178518, 178536, 179286,
    180411, 180412, 180600, 182120, 184283, 184624, 173760, 174284, 178217,
    178552, 179269, 173761, 178224, 178550, 178900, 179013, 179014, 179018,
    179166, 179277, 179281, 179307, 180054, 182123, 173351, 173762, 178218,
    178539, 178551, 179012, 179015, 179274, 179275, 179310, 183963, 173350,
    177039, 177041, 177043, 178221, 178223, 178226, 178537, 178547, 179011,
    179267, 179268, 179278, 179993, 180011, 180429, 182122, 184202, 190881,
    174282, 177042, 178515, 178541, 178542, 178543, 178544, 178548, 179016,
    179021, 179022, 179025, 179026, 179270, 179272, 179273, 179279, 179284,
    179309, 182118, 182119, 183733, 184281, 187911, 174283, 178534, 178549,
    179308, 190936,
    # BfA (8.0.1 to 8.3.7)
    162555, 161128, 163781, 160092, 160484, 162010, 163695, 167071, 163651,
    166804, 169439, 163110, 170068, 156525, 160705, 165755, 168232, 154884,
    154887, 163104, 163150, 156526, 163639, 163643, 154882, 169449, 152698,
    154883, 159848, 166240, 155812, 169661, 154891, 162572, 168311, 172091,
    154881, 162012, 163083, 163160, 163388, 163637, 168314, 161383, 162011,
    163152, 163165, 154889, 158927, 162117, 163147, 154132, 154888, 161347,
    163103, 163132, 163140, 163202, 163638, 163707, 168313, 168315, 155811,
    155819, 161348, 162567, 163094, 163156, 163157, 163395, 163692, 166344,
    167832, 171195, 174041, 159874, 159878, 161346, 165229, 169441, 169663,
    159847, 160518, 162556, 163019, 163138, 163149, 163641, 163783, 154885,
    154886, 159849, 163133, 163137, 163143, 163151, 163154, 163207, 163208,
    163417, 166419, 168312, 169280, 169669, 174350, 154131, 155592, 159850,
    161373, 161384, 162026, 162550, 162552, 163098, 163391, 163549, 163694,
    174348, 174349, 174351, 159845, 161321, 162560, 163057, 163153, 163158,
    163399, 163407, 163640, 163784, 166343, 168310, 154133, 156873, 162551,
    163102, 163107, 163155, 163187, 163785, 163989, 169459, 169460, 171196,
    174352, 159726, 159846, 161126, 161127, 161314, 163054, 163100, 163145,
    163159, 163181, 163192, 163387, 163522, 163642, 167739, 169467, 169662,
    160483, 160611, 162574, 162575, 163018, 163136, 163411, 163786, 166742,
    169458, 169468, 159900, 159919, 162545, 162547, 163052, 163101, 169462,
    169463, 155820, 159875, 160989, 162566, 163053, 163058, 163106, 166545,
    168392, 169117, 169436, 169466, 169527, 169660, 156872, 159750, 159867,
    159872, 159873, 162546, 162561, 162573, 163056, 163060, 163081, 163114,
    163115, 163116, 163709, 163990, 163991, 169397, 169442, 169464, 169521,
    169946, 156835, 159723, 159871, 159879, 159899, 160517, 160554, 162559,
    162564, 162583, 163050, 163076, 163548, 167043, 168607, 169119, 169763,
    169949, 158466, 158926, 159727, 159869, 159870, 159876, 160942, 162554,
    162562, 162569, 162582, 163051, 163075, 163105, 163135, 169118, 169120,
    169443, 169469, 169948, 170202, 153602, 159868, 159898, 159920, 162557,
    162558, 162563, 162565, 162568, 162570, 163049, 163061, 163108, 163117,
    163118, 163134, 164376, 169115, 169116, 169956, 153416, 159724, 159897,
    163077, 163109, 163841, 163988, 166420, 167548, 169947, 169952, 169954,
    # Legion (7.0.1 to 7.3.5)
    138979, 133576, 133574, 133569, 140753, 133579, 133571, 128763, 133893,
    133572, 138478, 128839, 133578, 133564, 133567, 128837, 152564, 133573,
    133570, 138479, 133565, 128843, 133566, 133577, 133681, 152998, 151133,
    140287, 142334, 144427, 133568, 138983, 139398, 140355, 133983, 144420,
    144426, 147669, 151431, 140339, 153192, 136550, 139346, 140188, 140189,
    140627, 144411, 155907, 138966, 140187, 133563, 133913, 136556, 136568,
    138285, 138975, 140272, 140289, 128833, 136567, 138294, 140265, 140295,
    140343, 142323, 147777, 133562, 136562, 136565, 138292, 138976, 138987,
    140253, 140291, 140337, 141209, 144415, 144424, 145272, 151122, 128764,
    128842, 135557, 136552, 140626, 144421, 144422, 128835, 136557, 138291,
    138874, 138981, 139345, 140292, 141210, 144414, 144419, 147776, 151774,
    128844, 128850, 133557, 133575, 133989, 136564, 138974, 138980, 140204,
    140256, 140273, 140338, 144416, 144417, 144418, 113099, 128847, 136559,
    136566, 139344, 140290, 140301, 140340, 144409, 144423, 128841, 128845,
    128848, 128849, 136548, 136558, 138295, 138982, 140276, 140297, 140299,
    141206, 144425, 144428, 133561, 138731, 138977, 140266, 140296, 140629,
    140631, 140754, 141215, 128761, 133979, 136547, 136549, 137618, 138973,
    139347, 140201, 140203, 140302, 141208, 141214, 141527, 144410, 144412,
    144413, 144429, 151123, 151775, 128834, 128853, 130259, 132752, 136544,
    136545, 136553, 138290, 138978, 140271, 140288, 140628, 141207, 141212,
    143681, 151124, 152718, 128836, 133980, 133981, 136546, 136554, 136555,
    136563, 140269, 140275, 140286, 140342, 140352, 141211, 143633, 147774,
    128838, 132753, 138972, 140205, 140341, 143635, 155909, 128840, 128851,
    133988, 136560, 138986, 140184, 140202, 140207, 140298, 140344, 140679,
    141213, 142322, 142324, 151121, 128875, 129179, 133586, 136551, 136561,
    140300, 140668, 143634, 152558, 155910, 128846, 137613, 140206, 152717,
    136806,
    # WoD (6.0.1 to 6.2.4)
    126934, 120959, 113509, 117452, 120168, 120150, 111446, 111454, 114982,
    116120, 111444, 128498, 111449, 111445, 111447, 111842, 116917, 118576,
    126936, 122348, 101436, 111442, 111522, 111438, 111457, 117469, 126935,
    111433, 111450, 113108, 116405, 118897, 111456, 111458, 114017, 118271,
    118275, 118416, 122345, 122346, 118273, 118428, 122347, 111439, 111452,
    119022, 119324, 122343, 111453, 117437, 117568, 111455, 116408, 118268,
    111434, 111441, 115355, 116406, 104196, 111436, 112449, 117440, 118274,
    118277, 120293, 128219, 111437, 116407, 117442, 118269, 112095, 116409,
    117453, 118272, 118424, 115351, 115352, 117441, 117470, 117471, 122344,
    130192, 111431, 111544, 117454, 117457, 117473, 118270, 113290, 114238,
    118276, 117439, 117472, 117474, 128385, 115300, 115353, 117475, 118051,
    119157, 115354, 118050, 118900,
    # MoP (5.0.1 to 5.4.8)
    87264, 104316, 86057, 74641, 101662, 81407, 75037, 75038, 74642, 81414,
    74643, 74646, 74650, 81410, 103641, 74655, 80313, 87253, 86432, 101618,
    88531, 105700, 74652, 82450, 98126, 104348, 74644, 75026, 81403, 82451,
    86069, 88530, 74651, 86026, 87226, 87248, 98116, 74645, 74648, 74649,
    74656, 81409, 81922, 86070, 88529, 105703, 74654, 81401, 81402, 86073,
    98127, 101745, 105708, 74636, 74647, 80610, 80618, 81924, 87246, 88382,
    74653, 75016, 81923, 87236, 87242, 90660, 101661, 104314, 105721, 74919,
    81404, 86074, 86508, 98121, 103643, 81400, 81415, 87238, 88490, 98118,
    77273, 79320, 81406, 81921, 87228, 87232, 98124, 101746, 105705, 105706,
    105711, 87240, 88586, 89593, 93208, 101630, 101748, 101750, 105707, 81408,
    87234, 88578, 90135, 94535, 101747, 103642, 104343, 105702, 77264, 81916,
    105704, 105720, 81405, 81917, 82344, 87244, 88532, 101617, 101749, 105701,
    105724, 81919, 81920, 82343, 82449, 87230, 88492, 98111, 104344, 108920,
    81411, 83095, 85504, 89588, 104340, 105719, 105722, 77272, 81413, 81889,
    81918, 83094, 88379, 89591, 90457, 98122, 98123, 98157, 104339, 104342,
    105717, 81175, 85501, 88388, 88398, 89594, 89595, 89598, 89601, 89683,
    98125, 81412, 82448, 83097, 89589, 89590, 89592, 89597, 89599, 89600,
    101616, 104341, 105723, 89596, 90659,
    # Cataclysm (4.0.1 to 4.3.4)
    62790, 62649, 58278, 62674, 62675, 58265, 62672, 59029, 62290, 63293,
    74822, 75033, 58276, 75027, 62680, 57518, 59229, 60267, 58260, 61381,
    62671, 58256, 58275, 58933, 59232, 61986, 75029, 58264, 59227, 58274,
    58279, 59230, 62661, 73260, 49602, 58257, 62653, 62676, 59231, 62660,
    69243, 62669, 75036, 60858, 62668, 57519, 58263, 59228, 62289, 63275,
    63691, 63692, 65730, 74921, 75028, 75035, 49254, 49600, 58269, 62665,
    62667, 62670, 63023, 75030, 75034, 58261, 60377, 61982, 62655, 62666,
    62909, 49253, 58267, 58268, 58280, 60379, 61984, 63251, 63693, 64639,
    68687, 49601, 58277, 60269, 62651, 62662, 62908, 63291, 64641, 68140,
    70925, 58259, 60268, 60375, 60378, 61383, 61384, 61983, 62652, 62654,
    62658, 62659, 62677, 63292, 63299, 69244, 75031, 57543, 62657, 62664,
    63296, 65731, 67272, 70927, 75032, 57544, 58266, 62663, 63694, 67271,
    69920, 58258, 58262, 61382, 61985, 65499, 67273, 62656, 65517, 70924,
    70926, 49397, 63530, 65516, 65500, 65515, 67230, 67270,
    # WotLK (3.0.1 to 3.3.5)
    34747, 40356, 44228, 43478, 35948, 34752, 34753, 43480, 35954, 35950,
    42431, 43005, 44854, 35949, 33004, 43491, 39520, 42994, 46796, 34754,
    43015, 44618, 34765, 42429, 43490, 43492, 44953, 46691, 33452, 34760,
    34768, 43696, 34766, 34769, 41751, 43488, 44836, 34755, 42995, 44722,
    44791, 46690, 34762, 34763, 38350, 44838, 34761, 40357, 42428, 43236,
    44071, 44619, 45932, 33445, 33449, 34749, 34759, 40359, 43004, 44941,
    34756, 37252, 38698, 42777, 42942, 46797, 33443, 34750, 34757, 40042,
    42434, 44570, 34751, 34767, 35952, 38706, 41731, 42779, 42999, 43695,
    44575, 44616, 44840, 44940, 46887, 42430, 42432, 42996, 42997, 44571,
    44607, 46784, 34748, 34758, 43001, 43523, 44049, 44573, 37253, 42433,
    42778, 43086, 44072, 44114, 44617, 46793, 33451, 33454, 35953, 40358,
    41729, 43268, 44750, 44839, 44855, 33444, 35951, 44574, 44716, 44837,
    34125, 34764, 39691, 42993, 43000, 43518, 35947, 42998, 44609, 43087,
    44749, 40035, 44608, 37452, 40202, 40036,
    # TBC (2.0.1 to 2.4.3)
    23848, 29112, 29449, 33874, 33924, 27659, 30816, 35565, 27655, 27660,
    27658, 31672, 31673, 27651, 33048, 34832, 20857, 27667, 33866, 38466,
    33042, 27661, 27663, 28284, 35563, 23495, 29451, 33053, 22645, 27854,
    30357, 27666, 34411, 27860, 30359, 30361, 33825, 27855, 28486, 29395,
    29454, 24072, 29393, 32453, 38430, 29292, 30155, 32455, 27657, 27665,
    32667, 33867, 24008, 27635, 28112, 28501, 29401, 29448, 27857, 32685,
    32686, 33052, 35720, 28399, 30358, 30458, 38428, 24009, 27636, 27858,
    34062, 22018, 24105, 24539, 27664, 29394, 29450, 29452, 29453, 30703,
    38431, 27856, 30355, 32722, 33872, 27662, 30457, 30610, 34780, 38432,
    32668, 38429, 27859, 38427, 22019, 23756, 24338, 29412, 32721,
    # Vanilla / Other (1.1.2 to 1.12.1)
    1645, 3927, 19299, 6657, 2596, 13893, 159, 6522, 13755, 8932, 20452,
    11109, 2894, 7228, 7676, 1179, 422, 2593, 2594, 9260, 2595, 12238, 21151,
    3703, 8953, 12217, 19222, 19224, 19306, 117, 2683, 733, 19221, 4537,
    4600, 21721, 12218, 5525, 18288, 787, 2686, 4593, 724, 6299, 16168,
    16766, 17196, 21114, 414, 1708, 4595, 13932, 13935, 4536, 3665, 4540,
    6290, 19305, 21215, 3727, 8952, 21217, 2888, 3770, 5527, 10841, 12210,
    19225, 19300, 19996, 1082, 2684, 2723, 6890, 8766, 17197, 1707, 3220,
    11444, 12212, 13929, 18287, 19223, 1205, 2070, 3771, 4541, 13928, 2287,
    3664, 4542, 4602, 8364, 11415, 16166, 17407, 18255, 19304, 21030, 21031,
    2681, 4599, 4604, 4607, 6888, 13930, 17198, 20074, 21254, 2682, 4457,
    4544, 4592, 5349, 17404, 17408, 21023, 4539, 4601, 8950, 13546, 13724,
    13931, 16170, 18300, 18632, 21033, 2680, 3728, 4606, 5478, 12216, 16169,
    17406, 18254, 18633, 18635, 19301, 3729, 8957, 12213, 13927, 17222, 17403,
    18045, 19994, 20516, 22324, 1114, 1487, 2679, 4656, 4791, 5474, 6807,
    6887, 19696, 21235, 21552, 961, 4538, 5472, 6316, 12224, 13810, 16167,
    17119, 20709, 1113, 5473, 5479, 7097, 7808, 9451, 13934, 17344, 19995,
    2288, 3666, 3726, 3772, 4594, 5480, 8076, 12209, 3663, 4605, 6038, 8079,
    12214, 21072, 1017, 1401, 2136, 3662, 5057, 5066, 5342, 5350, 5477, 2687,
    4608, 5095, 5476, 5526, 8078, 11584, 13933, 17402, 2685, 7806, 8075, 8077,
    8948, 12215, 13851, 23160, 7807, 22895
    ]
SEPARATOR_LEN = 3
DEBUG = False
### End configuration ###

def shorten(value):
    if value >= 1000:
        return f"{value // 1000}k"
    else:
        return value
    
class Item():
    def __init__(self, id, name, mana, health, duration, tooltip):
        self.id = id
        self.name = name
        self.mana = 0 if mana is None else mana
        self.health = 0 if health is None else health
        self.duration = duration
        self.tooltip = tooltip
        self.mps = self.mana / self.duration if self.mana > 0 and self.duration > 0 else 0
        
    def __str__(self):
        # Special handling for mage food
        if self.mana == -1 and self.health == -1:
            return f"{str(self.id) + ',':<7} -- {self.name} {'.' * (SEPARATOR_LEN - len(self.name))} (100% MP/HP) [Mage Food]"
        # Health and Mana
        if self.mana is not None and self.health is not None:
            return f"{str(self.id) + ',':<7} -- {self.name} {'.' * (SEPARATOR_LEN - len(self.name))} ({shorten(self.mana) if SHORTEN else self.mana} MP, {shorten(self.health if SHORTEN else self.health)} HP) [{self.mps}]"
        # Health only
        if self.health is not None:
            return f"{str(self.id) + ',':<7} -- {self.name} {'.' * (SEPARATOR_LEN - len(self.name))} ({shorten(self.health) if SHORTEN else self.health} HP) [{self.mps}]"
        # Mana only
        if self.mana is not None:
            return f"{str(self.id) + ',':<7} -- {self.name} {'.' * (SEPARATOR_LEN - len(self.name))} ({shorten(self.mana) if SHORTEN else self.mana} MP) [{self.mps}]"


    __repr__ = __str__

final = [   # The beginnings of our output table, mage food (100% MP/HP) is static, stored at the top
    Item(113509, "Conjured Mana Bun", -1, -1, 20, ""),
    Item(80618, "Conjured Mana Fritter", -1, -1, 20, ""),
    Item(80610, "Conjured Mana Pudding", -1, -1, 20, ""),
    Item(65499, "Conjured Mana Cake", -1, -1, 20, ""),
    Item(43523, "Conjured Mana Strudel", -1, -1, 20, ""),
    Item(43518, "Conjured Mana Pie", -1, -1, 20, ""),
    Item(65517, "Conjured Mana Lollipop", -1, -1, 20, ""),
    Item(65516, "Conjured Mana Cupcake", -1, -1, 20, ""),
    Item(65515, "Conjured Mana Brownie", -1, -1, 20, ""),
    Item(65500, "Conjured Mana Cookie", -1, -1, 20, "")

]

presort = [] # Holding table for items as they're processed, not yet sorted
error = [] # Table for holding unrecognized items

# This all involves making some assumptions about how the data is returned to us
# health and mana should be either None or a string like (1 / 1 * 1)
# duration should be either None or a string like 1
# This is all very dirty a does not consider language differences and will break if the tooltip changes
pattern_health = r"\(\d+ (/|\*) \d+ (/|\*) (\d+)\) health"
pattern_mana = r"\(\d+ (/|\*) \d+ (/|\*) (\d+)\) mana"

start_time = time.time()
for index, itemid in enumerate(SEARCH_ITEMS):
    if SHOW_PROGRESS:
        average = (time.time() - start_time) / (index + 1)
        remaining = average * (len(SEARCH_ITEMS) - index - 1)
        remaining = f"{remaining // 60:.0f}:{remaining % 60:02.0f}"
        print(' ' * shutil.get_terminal_size().columns, end='\r', file=sys.stderr)
        print(f"[{(index+1)/len(SEARCH_ITEMS)*100:6.2f}%] ({remaining} remaining): {itemid}", end='\r', file=sys.stderr)
    res = requests.get(f"{BASE_URL}item={itemid}&xml").content
    try:
        root = ET.fromstring(res)
        soup = bs(root.find("./item/htmlTooltip").text, 'html.parser')
        name = root.find("./item/name").text
        tooltip = soup.find_all('table')[1].find('span').text
    except:
        print(f"Error parsing item {itemid}", end='\r' if SHOW_PROGRESS else '\n', file=sys.stderr)
        error.append({'res': res, 'itemid': itemid})
        continue
    
    if DEBUG: print({k: v for k, v in locals().items() if k in ['name', 'itemid', 'tooltip']}, file=sys.stderr)

    health_match = re.search(pattern_health, tooltip)
    mana_match = re.search(pattern_mana, tooltip)
    health = health_match.group(0) if health_match is not None else None
    mana = mana_match.group(0) if mana_match is not None else None
    duration = 0 # Intial value, see below
    # Most items appear to have a pattern of (mana-per-tick / tick-interval * duration)
    # I've only seen a few items that follow (a / b or a * b), not sure yet the best way to handle these
    # They should all have the 
    if health and re.match(pattern_health, health) is not None:
        a, b, c = map(int, re.findall(r"\d+", health))
        if re.match(r"^\(\d+ \* \d+ / \d+", health) is not None:
            health = int(a * b / c)
            duration = c if c > duration else duration
        elif re.match(r"^\(\d+ / \d+ \* \d+", health) is not None:
            health = int(a / b * c)
            duration = c if c > duration else duration
        elif re.match(r"^\(\d+ / \d+", health) is not None:
            health = int(a / b)
            duration = b if b > duration else duration
        elif re.match(r"^\(\d+ \* \d+", health) is not None:
            health = int(a * b)
            duration = b if b > duration else duration
        else:
            print("Unrecognized health format")
            exit(1)
    
    if mana and re.match(pattern_mana, mana) is not None:
        a, b, c = map(int, re.findall(r"\d+", mana))
        if re.match(r"^\(\d+ \* \d+ / \d+", mana) is not None:
            mana = int(a * b / c)
            duration = c if c > duration else duration
        elif re.match(r"^\(\d+ / \d+ \* \d+", mana) is not None:
            mana = int(a / b * c)
            duration = c if c > duration else duration
        elif re.match(r"^\(\d+ / \d+", mana) is not None:
            mana = int(a / b)
            duration = b if b > duration else duration
        elif re.match(r"^\(\d+ \* \d+", mana) is not None:
            mana = int(a * b)
            duration = b if b > duration else duration
        else:
            print("Unrecognized mana format")
            exit(1)

    if DISCARD_NO_MANA and mana is None:
        time.sleep(RATE_LIMIT)
    elif DISCARD_BUFF_FOOD and 'well fed' in tooltip.lower():
        time.sleep(RATE_LIMIT)
    elif re.match('^conjured', name, re.IGNORECASE) is not None:
        time.sleep(RATE_LIMIT)
    else:
        presort.append(Item(itemid, name, mana, health, duration, tooltip))
        if DEBUG: print(presort[-1], file=sys.stderr)
        time.sleep(RATE_LIMIT)

# Prepare for presentation
presort.sort(key=lambda x: (x.mps, x.mana, x.health, x.name), reverse=True)
final.extend(presort)
SEPARATOR_LEN = max([len(str(item.name)) for item in final]) + 3

for index, line in enumerate(final):
    if index + 1 < len(final):
        print(line)
    else:
        print(re.sub(r",", " ", str(line), 1))


if error and REPORT_FAILURES:
    print("\n\nErrors encountered while parsing:", file=sys.stderr)
    for index, item in enumerate(error):
        print(f"{error[index]['itemid']}: {error[index]['res']}\n", file=sys.stderr)