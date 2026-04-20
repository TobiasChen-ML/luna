"""
Generate ethical relation scripts with full content
Run: python -m app.migrations.generate_ethical_scripts
"""
import asyncio
import json
import os
import random
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import db

RELATION_TYPE_CONFIGS = {
    'principal_student': {
        'name': '校长×学生',
        'category': '校园',
        'templates': [
            {'surface': '威严庄重', 'truth': '内心孤独渴望被理解'},
            {'surface': '严厉公正', 'truth': '私下温柔体贴'},
            {'surface': '高高在上', 'truth': '其实只是不善于表达'},
            {'surface': '冷酷无情', 'truth': '背负沉重过去'},
        ],
        'progressions': [
            {'start': '你因违纪被叫到校长室', 'build': '多次接触后发现TA不为人知的一面', 'climax': 'TA在你面前卸下伪装', 'resolve': '确立秘密关系'},
            {'start': 'TA是你毕业论文的指导校长', 'build': '单独辅导中产生微妙情感', 'climax': 'TA主动打破师生界限', 'resolve': '约定毕业后公开'},
        ],
        'hooks': ['只有你能让TA露出微笑', 'TA的书房里藏着秘密', 'TA的红酒杯里倒映着孤独'],
    },
    'homeroom_teacher_student': {
        'name': '班主任×学生',
        'category': '校园',
        'templates': [
            {'surface': '严厉负责', 'truth': '其实很关心你'},
            {'surface': '冷漠疏离', 'truth': '温柔到让你心动的另一面'},
            {'surface': '一丝不苟', 'truth': '私底下很可爱'},
            {'surface': '铁面无私', 'truth': '内心渴望被依赖'},
        ],
        'progressions': [
            {'start': '你是TA班上的问题学生', 'build': 'TA一次次帮你化解麻烦', 'climax': 'TA说"我只对你特殊"', 'resolve': '在教室的秘密'},
            {'start': 'TA对你的成绩格外上心', 'build': '课后补习变成心灵交流', 'climax': 'TA含泪承认对你的感情', 'resolve': '约定毕业后再公开'},
        ],
        'hooks': ['TA办公桌抽屉里的秘密', 'TA每次点名都会多看你一眼', 'TA的眼神里藏着说不出口的话'],
    },
    'grade_director_student': {
        'name': '年级主任×学生',
        'category': '校园',
        'templates': [
            {'surface': '威严霸气', 'truth': '其实很好哄'},
            {'surface': '一视同仁', 'truth': '唯独对你特殊'},
            {'surface': '不苟言笑', 'truth': '笑起来很好看'},
            {'surface': '铁腕治学', 'truth': '内心柔软如水'},
        ],
        'progressions': [
            {'start': '你被TA盯上了', 'build': '在严厉之下发现TA的温柔', 'climax': 'TA在办公室告白', 'resolve': '属于你们的秘密'},
            {'start': 'TA是全校最可怕的人', 'build': '你发现TA私下会偷偷关注你', 'climax': 'TA握住你的手说"别告诉别人"', 'resolve': '身份悬殊下的禁忌之恋'},
        ],
        'hooks': ['TA的办公室门永远为你留缝', 'TA看似责骂实则在保护你', 'TA的衣柜里藏着不为人知的一面'],
    },
    'dean_student': {
        'name': '教务主任×学生',
        'category': '校园',
        'templates': [
            {'surface': '公正无私', 'truth': '为你破例很多次'},
            {'surface': '冷若冰霜', 'truth': '对你有不一样的温度'},
            {'surface': '规则至上', 'truth': '为你颠覆所有规则'},
            {'surface': '刻板严肃', 'truth': '私下很浪漫'},
        ],
        'progressions': [
            {'start': '你被教务处盯上了', 'build': 'TA一次又一次帮你摆平麻烦', 'climax': 'TA说"我这样做都是为了你"', 'resolve': '打破规则的爱'},
            {'start': 'TA总是找理由见你', 'build': '从责备变成关心', 'climax': 'TA在你面前崩溃', 'resolve': '互相救赎'},
        ],
        'hooks': ['TA的档案柜里有你的专属文件夹', 'TA从不加班，但为你例外', 'TA的红印章下藏着对你的思念'],
    },
    'discipline_master_student': {
        'name': '训导主任×学生',
        'category': '校园',
        'templates': [
            {'surface': '凶神恶煞', 'truth': '其实是个大暖男'},
            {'surface': '不近人情', 'truth': '对你情有独钟'},
            {'surface': '恶魔教师', 'truth': '只想保护你一个人'},
            {'surface': '冷酷无情', 'truth': '内心最柔软的地方给你'},
        ],
        'progressions': [
            {'start': '你是TA最头疼的学生', 'build': 'TA对你的惩罚越来越轻', 'climax': 'TA把你堵在角落表白', 'resolve': '训导处里的秘密'},
            {'start': 'TA以各种理由扣你的分', 'build': '你发现TA只是想多见你', 'climax': 'TA承认自己的幼稚', 'resolve': '从对立到相爱'},
        ],
        'hooks': ['TA的记分本上写满了你的名字', 'TA每次巡逻都会路过你的教室', 'TA的训斥越来越像撒娇'],
    },
    'dorm_manager_student': {
        'name': '宿管×学生',
        'category': '校园',
        'templates': [
            {'surface': '严厉凶悍', 'truth': '其实很温柔'},
            {'surface': '冷漠无情', 'truth': '偷偷照顾你的生活'},
            {'surface': '唠唠叨叨', 'truth': '只是担心你'},
            {'surface': '铁面无私', 'truth': '只对你破例'},
        ],
        'progressions': [
            {'start': '你经常被TA抓到违纪', 'build': 'TA从责备变成关心', 'climax': '深夜TA敲门说想你了', 'resolve': '宿舍楼里的秘密'},
            {'start': 'TA总是对你格外严格', 'build': '你发现TA在偷偷帮你', 'climax': 'TA说"别告诉别人"', 'resolve': '门禁之外的爱情'},
        ],
        'hooks': ['TA给你留了备用钥匙', 'TA的值班室有你的专属座位', 'TA每次查寝都会在你门口多站一会儿'],
    },
    'aunt_paternal_nephew': {
        'name': '婶婶×侄子',
        'category': '家庭',
        'templates': [
            {'surface': '端庄贤淑', 'truth': '内心寂寞难耐'},
            {'surface': '温柔贤惠', 'truth': '渴望被爱的女人'},
            {'surface': '知书达理', 'truth': '压抑多年的欲望'},
            {'surface': '相夫教子', 'truth': '婚姻不幸福'},
        ],
        'progressions': [
            {'start': '叔叔常年在外，你经常陪TA', 'build': '独处时的暧昧气氛', 'climax': 'TA主动靠近你', 'resolve': '家族的禁忌秘密'},
            {'start': 'TA是你最亲近的长辈', 'build': '你发现TA在婚姻里很孤独', 'climax': 'TA哭着说"只有你懂我"', 'resolve': '越界的温柔'},
        ],
        'hooks': ['TA的眼神在家族聚会上总是寻找你', 'TA会在没人的时候叫你的小名', 'TA送的礼物里藏着别样的心意'],
    },
    'uncle_maternal_niece': {
        'name': '舅舅×外甥女',
        'category': '家庭',
        'templates': [
            {'surface': '成熟稳重', 'truth': '对你有着不可言说的感情'},
            {'surface': '风趣幽默', 'truth': '只为博你一笑'},
            {'surface': '事业有成', 'truth': '内心最柔软的地方留给你'},
            {'surface': '单身多年', 'truth': '一直在等你长大'},
        ],
        'progressions': [
            {'start': 'TA是你最疼你的舅舅', 'build': '你发现TA看你的眼神变了', 'climax': 'TA说"你不再是孩子了"', 'resolve': '禁忌的温柔'},
            {'start': 'TA单身多年，你是最亲近的人', 'build': '关系逐渐暧昧', 'climax': 'TA在你成年那晚告白', 'resolve': '血脉之外的羁绊'},
        ],
        'hooks': ['TA的书房里放着你的照片', 'TA从不让你叫TA舅舅', 'TA的怀抱比任何人都温暖'],
    },
    'aunt_maternal_nephew': {
        'name': '姨妈×外甥',
        'category': '家庭',
        'templates': [
            {'surface': '风情万种', 'truth': '只为你展现柔弱'},
            {'surface': '独立强势', 'truth': '在你面前是小女人'},
            {'surface': '事业女性', 'truth': '内心渴望被依赖'},
            {'surface': '单身贵族', 'truth': '一直在等你'},
        ],
        'progressions': [
            {'start': 'TA是你妈妈最漂亮的妹妹', 'build': '每次见面都让你心动', 'climax': 'TA在醉酒后吐露心声', 'resolve': '不能说的秘密'},
            {'start': 'TA总是特别关照你', 'build': '你发现TA对你的好超出亲情', 'climax': 'TA说"让我做你的女人"', 'resolve': '家庭聚会的秘密'},
        ],
        'hooks': ['TA的香水味让你心神不宁', 'TA总是在你耳边低语', 'TA的眼神在餐桌下追逐着你'],
    },
    'uncle_paternal_niece': {
        'name': '姑父×侄女',
        'category': '家庭',
        'templates': [
            {'surface': '和蔼可亲', 'truth': '对你的感情不单纯'},
            {'surface': '成功人士', 'truth': '婚姻形同虚设'},
            {'surface': '严肃正经', 'truth': '私下很温柔'},
            {'surface': '顾家好男人', 'truth': '只为你心动'},
        ],
        'progressions': [
            {'start': 'TA是你最亲近的长辈', 'build': '你发现TA在偷偷关注你', 'climax': 'TA说"你姑姑不懂我"', 'resolve': '见不得光的温柔'},
            {'start': 'TA和姑姑感情不好', 'build': '你成为TA的精神寄托', 'climax': 'TA把秘密都告诉了你', 'resolve': '越界的关系'},
        ],
        'hooks': ['TA的肩膀是最安全的避风港', 'TA总是帮你挡掉所有麻烦', 'TA的眼神里有说不出的温柔'],
    },
    'aunt_paternal_niece': {
        'name': '姑姑×侄子',
        'category': '家庭',
        'templates': [
            {'surface': '高冷傲娇', 'truth': '其实很粘人'},
            {'surface': '独立自主', 'truth': '渴望被呵护'},
            {'surface': '不婚主义', 'truth': '在等对的人'},
            {'surface': '事业女强', 'truth': '内心小女孩'},
        ],
        'progressions': [
            {'start': 'TA是家族里最特别的女性', 'build': '你们的互动越来越暧昧', 'climax': 'TA说"别叫我姑姑"', 'resolve': '称呼之外的关系'},
            {'start': 'TA总是对你格外照顾', 'build': '你发现TA对你的占有欲', 'climax': 'TA在深夜敲开你的门', 'resolve': '家族的秘密'},
        ],
        'hooks': ['TA从不让你叫TA长辈', 'TA的每一个拥抱都意犹未尽', 'TA说你是TA最特别的存在'],
    },
    'stepsister_stepbrother': {
        'name': '继妹×继兄',
        'category': '家庭',
        'templates': [
            {'surface': '乖巧懂事', 'truth': '叛逆又撩人'},
            {'surface': '冷漠抗拒', 'truth': '其实很在意你'},
            {'surface': '天真无邪', 'truth': '心思缜密的小恶魔'},
            {'surface': '任性刁蛮', 'truth': '只想引起你的注意'},
        ],
        'progressions': [
            {'start': '父母再婚后你们成为家人', 'build': '从排斥到产生微妙情愫', 'climax': 'TA说"我们不是亲生的"', 'resolve': '同一个屋檐下的秘密'},
            {'start': 'TA总是故意和你作对', 'build': '你发现TA只是想靠近你', 'climax': 'TA在深夜溜进你房间', 'resolve': '兄妹之外的羁绊'},
        ],
        'hooks': ['TA的房间和你只隔一堵墙', 'TA的眼神里藏着说不出的话', 'TA的恶作剧其实是撒娇'],
    },
    'sister_in_law': {
        'name': '嫂子/弟妹',
        'category': '家庭',
        'templates': [
            {'surface': '温柔贤惠', 'truth': '婚姻不幸福'},
            {'surface': '幸福美满', 'truth': '内心寂寞空虚'},
            {'surface': '端庄大方', 'truth': '渴望被真正爱着'},
            {'surface': '体贴入微', 'truth': '对你的关心超出亲情'},
        ],
        'progressions': [
            {'start': 'TA是你哥哥/弟弟的妻子', 'build': 'TA总找理由接近你', 'climax': 'TA说"他从来不懂我"', 'resolve': '背叛与救赎'},
            {'start': '你发现TA在婚姻里不快乐', 'build': '你成为TA的倾诉对象', 'climax': 'TA在你怀里哭泣', 'resolve': '不能说的秘密'},
        ],
        'hooks': ['TA的眼神总是若有若无地看向你', 'TA的每一次关心都意味深长', 'TA的秘密只告诉你一个人'],
    },
    'classmate_mother': {
        'name': '同学的妈妈',
        'category': '社会',
        'templates': [
            {'surface': '温柔慈祥', 'truth': '其实很寂寞'},
            {'surface': '端庄优雅', 'truth': '渴望被当作女人看待'},
            {'surface': '青春依旧', 'truth': '内心住着小女孩'},
            {'surface': '风情万种', 'truth': '只对你展现真实一面'},
        ],
        'progressions': [
            {'start': '你经常去同学家玩', 'build': 'TA对你的关注越来越多', 'climax': 'TA趁同学不在靠近你', 'resolve': '不能说的秘密'},
            {'start': 'TA是所有人眼中的完美母亲', 'build': '你发现TA在婚姻里很孤独', 'climax': 'TA说"把我当女人看好吗"', 'resolve': '禁忌的温柔'},
        ],
        'hooks': ['TA总是给你准备特别的点心', 'TA的眼神在同学面前也在追逐你', 'TA的拥抱比任何人都久'],
    },
    'classmate_sister': {
        'name': '同学的妹妹',
        'category': '社会',
        'templates': [
            {'surface': '乖巧可爱', 'truth': '其实很撩人'},
            {'surface': '天真无邪', 'truth': '心思比你想象的复杂'},
            {'surface': '害羞内向', 'truth': '私下很大胆'},
            {'surface': '邻家女孩', 'truth': '对你情有独钟'},
        ],
        'progressions': [
            {'start': '你是TA哥哥/姐姐的同学', 'build': 'TA总是找借口接近你', 'climax': 'TA说"我喜欢的人是你"', 'resolve': '同学家的秘密'},
            {'start': 'TA总是偷偷看你', 'build': '你们的互动越来越暧昧', 'climax': 'TA在你耳边说喜欢你', 'resolve': '不能让同学知道'},
        ],
        'hooks': ['TA总是在你经过时出现', 'TA的借口拙劣但可爱', 'TA的眼神在人群中只找你'],
    },
    'friend_sister': {
        'name': '朋友的妹妹',
        'category': '社会',
        'templates': [
            {'surface': '活泼开朗', 'truth': '只对你害羞'},
            {'surface': '大大咧咧', 'truth': '其实心思细腻'},
            {'surface': '不拘小节', 'truth': '对你小心翼翼'},
            {'surface': '随性自然', 'truth': '暗恋你很久了'},
        ],
        'progressions': [
            {'start': 'TA是你最好朋友的妹妹', 'build': 'TA总是出现在你们聚会中', 'climax': 'TA说"我一直都喜欢你"', 'resolve': '朋友不知道的秘密'},
            {'start': 'TA经常找你帮忙', 'build': '你发现TA对你的好超出友情', 'climax': 'TA告白后等待你的回应', 'resolve': '友情与爱情的抉择'},
        ],
        'hooks': ['TA的求助总是找你', 'TA在朋友面前看你的眼神不同', 'TA说你是TA最信任的人'],
    },
    'friend_older_sister': {
        'name': '朋友的姐姐',
        'category': '社会',
        'templates': [
            {'surface': '成熟知性', 'truth': '私底下很可爱'},
            {'surface': '强势干练', 'truth': '在你面前是小女人'},
            {'surface': '高不可攀', 'truth': '其实很好接近'},
            {'surface': '独立自信', 'truth': '渴望被呵护'},
        ],
        'progressions': [
            {'start': 'TA是你朋友的姐姐，总是照顾你们', 'build': '你发现TA对你特别好', 'climax': 'TA说"别把我当姐姐"', 'resolve': '朋友家的秘密'},
            {'start': 'TA是你暗恋已久的对象', 'build': 'TA对你的态度越来越暧昧', 'climax': 'TA主动打破朋友界限', 'resolve': '越界的关系'},
        ],
        'hooks': ['TA总是给你特别照顾', 'TA的眼神在朋友面前也在说你', 'TA的温柔只给你一个人'],
    },
    'friend_mother': {
        'name': '朋友的妈妈',
        'category': '社会',
        'templates': [
            {'surface': '温婉贤淑', 'truth': '内心渴望被爱'},
            {'surface': '优雅迷人', 'truth': '婚姻早就名存实亡'},
            {'surface': '热情好客', 'truth': '只对你特别'},
            {'surface': '保养得宜', 'truth': '比同龄人年轻太多'},
        ],
        'progressions': [
            {'start': '你经常去朋友家，TA总是特别照顾你', 'build': '你发现TA对你越来越好', 'climax': 'TA说"我老公从来不懂我"', 'resolve': '朋友不知道的秘密'},
            {'start': 'TA是你见过最有魅力的长辈', 'build': 'TA开始私下联系你', 'climax': 'TA在你面前展现脆弱', 'resolve': '禁忌的温柔'},
        ],
        'hooks': ['TA总是给你留饭', 'TA的眼神让你心跳加速', 'TA的秘密只告诉你'],
    },
    'friend_brother': {
        'name': '朋友的哥哥',
        'category': '社会',
        'templates': [
            {'surface': '成熟稳重', 'truth': '私底下很会撩'},
            {'surface': '高冷疏离', 'truth': '只对你温柔'},
            {'surface': '严肃正经', 'truth': '内心很闷骚'},
            {'surface': '不屑一顾', 'truth': '其实暗恋你很久'},
        ],
        'progressions': [
            {'start': 'TA是你朋友的哥哥，总是很高冷', 'build': '你发现TA其实很关心你', 'climax': 'TA说"我不把你当弟弟/妹妹"', 'resolve': '朋友不知道的秘密'},
            {'start': 'TA总是默默帮你', 'build': '你开始在意TA的存在', 'climax': 'TA在深夜找你告白', 'resolve': '越界的关系'},
        ],
        'hooks': ['TA总是帮你解决麻烦', 'TA的眼神在你身上停留很久', 'TA说的每一句话都像在暗示什么'],
    },
    'doctor_nurse': {
        'name': '医生×护士',
        'category': '社会',
        'templates': [
            {'surface': '冷静专业', 'truth': '私下很温柔'},
            {'surface': '不苟言笑', 'truth': '只对你展现笑容'},
            {'surface': '高高在上', 'truth': '内心渴望被理解'},
            {'surface': '完美主义', 'truth': '在你面前会犯错'},
        ],
        'progressions': [
            {'start': '你们在同一家医院工作', 'build': '工作中擦出火花', 'climax': 'TA在值班室说喜欢你', 'resolve': '医院里的秘密'},
            {'start': 'TA是你见过的最优秀的医生', 'build': '你发现TA私下很孤独', 'climax': 'TA说你是TA的白大褂天使', 'resolve': '白衣下的爱情'},
        ],
        'hooks': ['TA的手术刀很稳，但看你的手会抖', 'TA总是找理由让你帮忙', 'TA的眼神在手术台外只找你'],
    },
    'nurse_patient': {
        'name': '护士×患者',
        'category': '社会',
        'templates': [
            {'surface': '温柔体贴', 'truth': '对你格外上心'},
            {'surface': '专业冷静', 'truth': '私下面红耳赤'},
            {'surface': '一视同仁', 'truth': '唯独对你特殊'},
            {'surface': '疏离客气', 'truth': '心跳加速在掩饰'},
        ],
        'progressions': [
            {'start': '你住院期间TA照顾你', 'build': 'TA对你的关心超出职责', 'climax': 'TA说"出院后我们还能见面吗"', 'resolve': '病房里的秘密'},
            {'start': 'TA是照顾你的护士', 'build': '你们之间产生微妙情感', 'climax': 'TA在深夜偷偷来看你', 'resolve': '医患之外的羁绊'},
        ],
        'hooks': ['TA的输液总是不疼', 'TA的眼神比药物还管用', 'TA会在没人的时候握住你的手'],
    },
    'director_actor': {
        'name': '导演×演员',
        'category': '社会',
        'templates': [
            {'surface': '严厉苛刻', 'truth': '其实很欣赏你'},
            {'surface': '不近人情', 'truth': '私底下很温柔'},
            {'surface': '完美主义', 'truth': '对你有独特的偏爱'},
            {'surface': '高高在上', 'truth': '内心渴望被理解'},
        ],
        'progressions': [
            {'start': '你试镜TA的新电影', 'build': 'TA对你的要求格外高', 'climax': 'TA说"戏里的感情是真的"', 'resolve': '片场的秘密'},
            {'start': 'TA是圈内有名的魔鬼导演', 'build': '你发现TA只对你格外严厉又格外温柔', 'climax': 'TA在片场告白', 'resolve': '银幕之外的爱情'},
        ],
        'hooks': ['TA的镜头语言在说爱你', 'TA的批评都是变相的关心', 'TA的导演椅旁总有你的位置'],
    },
    'convenience_store_owner': {
        'name': '便利店老板娘×常客',
        'category': '社会',
        'templates': [
            {'surface': '热情开朗', 'truth': '其实很寂寞'},
            {'surface': '大大咧咧', 'truth': '对你心思细腻'},
            {'surface': '唠唠叨叨', 'truth': '只是想多和你说说话'},
            {'surface': '风韵犹存', 'truth': '渴望被当作女人'},
        ],
        'progressions': [
            {'start': '你每天深夜去便利店', 'build': 'TA开始给你留特别的便当', 'climax': 'TA说"我等你很久了"', 'resolve': '深夜便利店的秘密'},
            {'start': 'TA总是记住你的喜好', 'build': '你们之间的互动越来越暧昧', 'climax': 'TA在打烊后不让你走', 'resolve': '24小时的爱情'},
        ],
        'hooks': ['TA的收银台总有你的专属零食', 'TA的眼神在深夜格外温柔', 'TA会为你提前开门或推迟关门'],
    },
    'bakery_owner_customer': {
        'name': '面包店老板×顾客',
        'category': '社会',
        'templates': [
            {'surface': '温暖阳光', 'truth': '私下很孤独'},
            {'surface': '温柔治愈', 'truth': '渴望被温暖'},
            {'surface': '勤劳朴实', 'truth': '对你有特别的心思'},
            {'surface': '踏实可靠', 'truth': '内心也很浪漫'},
        ],
        'progressions': [
            {'start': '你每天早上都去买面包', 'build': 'TA开始给你特别款待', 'climax': 'TA说"这是只为你做的"', 'resolve': '面包店里的秘密'},
            {'start': 'TA是街角面包店的老板', 'build': '你发现TA总是在等你', 'climax': 'TA给你做了特别的蛋糕', 'resolve': '甜蜜的爱情'},
        ],
        'hooks': ['TA的面包有特别的形状', 'TA的笑容比面包还甜', 'TA会为你打烊后重新开灯'],
    },
}

EMOTION_TONES = ['sweet', 'angst', 'healing', 'comedy', 'dark', 'suspense', 'revenge', 'ethical', 'rebirth', 'thriller']
ERAS = ['modern_urban', 'modern_campus', 'ancient_palace', 'ancient_jianghu', 'republic_concession']

NAMES_MALE = ['陆', '沈', '顾', '江', '傅', '霍', '谢', '萧', '叶', '温', '苏', '楚', '秦', '薄', '商', '裴', '晏']
NAMES_FEMALE = ['苏', '沈', '顾', '林', '叶', '江', '温', '楚', '秦', '白', '宋', '唐', '陈', '许', '周', '夏', '安', '姜', '乔', '季']

PROFESSIONS_BY_ERA = {
    'modern_urban': ['business', 'doctor', 'lawyer', 'chef', 'writer', 'artist', 'musician', 'athlete', 'detective', 'programmer'],
    'modern_campus': ['student', 'professor', 'teacher', 'counselor', 'coach'],
    'ancient_palace': ['emperor', 'prince', 'princess', 'general', 'minister', 'concubine', 'guard', 'physician'],
    'ancient_jianghu': ['swordsman', 'assassin', 'sect_leader', 'healer', 'merchant', 'noble'],
    'republic_concession': ['warlord', 'singer', 'spy', 'businessman', 'student', 'journalist'],
}

TITLE_TEMPLATES = [
    ('{name}的秘密', "{name}'s Secret"),
    ('与{relation}的禁忌', "Forbidden with {relation}"),
    ('{name}的另一面', "The Other Side of {name}"),
    ('越过界限的{relation}', "Crossing the Line"),
    ('{name}的眼泪', "{name}'s Tears"),
    ('不能说的{emotion}', "Unspeakable {emotion}"),
    ('{name}的告白', "{name}'s Confession"),
    ('禁忌{relation}', "Forbidden {relation}"),
    ('{name}的温柔陷阱', "{name}'s Gentle Trap"),
    ('与{relation}的约定', "Promise with {relation}"),
]

KEY_NODE_NAMES = [
    '初见', '误会', '靠近', '心动', '试探', '告白', '犹豫', '决心', '危机', '和解'
]

KEY_NODE_DESCRIPTIONS = [
    '命运的相遇，那一刻TA的眼神让你心跳加速',
    '一场误会，让你们的关系陷入冰点',
    'TA开始有意无意地接近你',
    '你发现TA对你来说已经不一样了',
    'TA试探性地问你一些奇怪的问题',
    'TA终于说出了藏在心里的话',
    '面对这份感情，TA开始犹豫',
    'TA决定不再逃避自己的心',
    '外界发现了你们的关系',
    '经历风雨后，你们更加坚定',
]

ENDING_GOOD = [
    'TA终于放下所有顾虑，与你走到了一起，在月光下许下永远',
    '你们勇敢地面对所有阻碍，最终收获了属于彼此的幸福',
    'TA抛弃了一切世俗眼光，只为与你相守一生',
]

ENDING_NEUTRAL = [
    'TA选择了离开，给你们彼此一段时间冷静，但眼神里的不舍出卖了一切',
    '你们的关系悬而未决，谁也没有勇气打破这份暧昧',
    'TA决定暂时保持现状，但彼此心里都有了无法言说的羁绊',
]

ENDING_BAD = [
    'TA最终选择了放弃，留下一封信后消失在你的世界里',
    '现实的压力让TA无法承受，你们只能以遗憾收场',
    'TA转身离开，眼角的泪光说明了一切，有些人注定只能错过',
]

ENDING_SECRET = [
    '你们决定把这份感情藏在心底，以另一种身份继续守护彼此',
    'TA说"如果下辈子早点遇到你就好了"，然后转身融入人群',
    '你们的秘密被封存在一个特殊的角落，成为彼此最珍贵的回忆',
]


def generate_name(gender: str) -> str:
    surnames = NAMES_MALE if gender == 'male' else NAMES_FEMALE
    name_chars = '晨暮雪晴雨涵梓萱逸然'
    return random.choice(surnames) + ''.join([random.choice(name_chars) for _ in range(random.randint(1, 2))])


def generate_script(relation_type: str, config: dict, index: int) -> dict:
    char_gender = 'male_char' if random.random() > 0.3 else 'female_char'
    name = generate_name(char_gender.replace('_char', ''))
    
    template = random.choice(config['templates'])
    progression = random.choice(config['progressions'])
    hook = random.choice(config['hooks'])
    
    era = random.choice(ERAS)
    profession = random.choice(PROFESSIONS_BY_ERA.get(era, ['business']))
    emotion_tone = random.choice(EMOTION_TONES)
    
    title_template = random.choice(TITLE_TEMPLATES)
    title = title_template[0].format(name=name, relation=config['name'], emotion=emotion_tone)
    title_en = title_template[1].format(name=name, relation=config['name'], emotion=emotion_tone)
    
    summary = f"一段{config['name']}的禁忌之恋。{template['surface']}的外表下，藏着{template['truth']}的灵魂。{hook}。"
    
    num_key_nodes = random.randint(3, 6)
    selected_indices = random.sample(range(len(KEY_NODE_NAMES)), num_key_nodes)
    key_nodes = [
        {
            'name': KEY_NODE_NAMES[i],
            'description': KEY_NODE_DESCRIPTIONS[i],
            'trigger': f'当好感度达到{30 + i * 15}%时触发'
        }
        for i in sorted(selected_indices)
    ]
    
    script_seed = {
        'character': {
            'name': '{{character_name}}',
            'age': random.randint(22, 40),
            'surface_identity': template['surface'],
            'true_identity': template['truth'],
            'profession': profession,
        },
        'contrast': {
            'surface': template['surface'],
            'truth': template['truth'],
            'hook': hook,
        },
        'progression': {
            'start': progression['start'],
            'build': progression['build'],
            'climax': progression['climax'],
            'resolve': progression['resolve'],
        },
        'key_nodes': key_nodes,
        'endings': {
            'good': random.choice(ENDING_GOOD),
            'neutral': random.choice(ENDING_NEUTRAL),
            'bad': random.choice(ENDING_BAD),
            'secret': random.choice(ENDING_SECRET),
        }
    }
    
    full_script = {
        'prologue': f"你是{{{{character_name}}}}，一个{template['surface']}的人。表面上，你们是{config['name']}的关系，但内心深处，有什么在悄然改变...",
        'opening_scene': progression['start'],
        'character_inner_state': {
            'initial': f"表面{template['surface']}，内心{template['truth']}",
            'development': '随着故事推进，TA对你的态度逐渐改变',
            'climax': 'TA终于无法压抑内心的感情',
        },
        'narrative_beats': [
            {'scene': progression['start'], 'emotion': '紧张', 'hint': '注意TA的细节'},
            {'scene': progression['build'], 'emotion': '暧昧', 'hint': 'TA在试探你的反应'},
            {'scene': progression['climax'], 'emotion': '心跳加速', 'hint': '关键时刻，你的选择决定一切'},
            {'scene': progression['resolve'], 'emotion': '温暖', 'hint': '属于你们的结局'},
        ],
        'dialogue_hints': {
            'style': '根据TA的性格特点调整对话风格',
            'key_phrases': [f'"{hook}"', f'"我从未想过会对你..."', f'"别告诉任何人..."'],
        },
        'branching_points': [
            {
                'trigger': key_nodes[0]['trigger'] if key_nodes else '好感度30%',
                'choices': [
                    {'text': '回应TA的好意', 'effect': '好感度+20，进入暧昧线'},
                    {'text': '保持距离', 'effect': '好感度-10，进入疏远线'},
                ]
            },
            {
                'trigger': key_nodes[-1]['trigger'] if key_nodes and len(key_nodes) > 1 else '好感度60%',
                'choices': [
                    {'text': '勇敢告白', 'effect': '进入恋爱结局'},
                    {'text': '压抑感情', 'effect': '进入暗恋结局'},
                ]
            }
        ],
    }
    
    emotion_tones = [emotion_tone]
    if random.random() > 0.5:
        emotion_tones.append(random.choice([t for t in EMOTION_TONES if t != emotion_tone]))
    
    script_id = f"ethical_{relation_type}_{index:03d}"
    
    return {
        'id': script_id,
        'title': title,
        'title_en': title_en,
        'summary': summary,
        'emotion_tones': json.dumps(emotion_tones, ensure_ascii=False),
        'relation_types': json.dumps([relation_type], ensure_ascii=False),
        'contrast_types': json.dumps(['identity', 'personality'], ensure_ascii=False),
        'era': era,
        'gender_target': 'female' if char_gender == 'male_char' else 'male',
        'character_gender': char_gender,
        'profession': profession,
        'length': random.choice(['short', 'medium', 'long']),
        'age_rating': 'mature',
        'contrast_surface': f"表面{template['surface']}",
        'contrast_truth': f"其实{template['truth']}",
        'contrast_hook': hook,
        'script_seed': json.dumps(script_seed, ensure_ascii=False),
        'full_script': json.dumps(full_script, ensure_ascii=False),
        'status': 'published'
    }


async def generate_scripts():
    await db.connect()
    
    count_result = await db.execute("SELECT COUNT(*) as count FROM script_library", fetch=True)
    initial_count = count_result['count'] if count_result else 0
    print(f"Current scripts: {initial_count}")
    
    scripts_per_type = 25
    total_generated = 0
    
    for relation_type, config in RELATION_TYPE_CONFIGS.items():
        print(f"\nGenerating {scripts_per_type} scripts for {config['name']}...")
        
        for i in range(scripts_per_type):
            script = generate_script(relation_type, config, i + 1)
            
            now = datetime.utcnow().isoformat()
            try:
                await db.execute(
                    """INSERT OR REPLACE INTO script_library 
                       (id, title, title_en, summary, emotion_tones, relation_types, 
                        contrast_types, era, gender_target, character_gender, profession,
                        length, age_rating, contrast_surface, contrast_truth, contrast_hook,
                        script_seed, full_script, status, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        script['id'], script['title'], script['title_en'], script['summary'],
                        script['emotion_tones'], script['relation_types'], script['contrast_types'],
                        script['era'], script['gender_target'], script['character_gender'],
                        script['profession'], script['length'], script['age_rating'],
                        script['contrast_surface'], script['contrast_truth'], script['contrast_hook'],
                        script['script_seed'], script['full_script'], script['status'], now, now
                    )
                )
                total_generated += 1
            except Exception as e:
                print(f"Error inserting script {script['id']}: {e}")
        
        print(f"  Generated {scripts_per_type} scripts for {config['name']}")
    
    final_count = await db.execute("SELECT COUNT(*) as count FROM script_library", fetch=True)
    print(f"\nDone! Total scripts: {final_count['count']} (added {total_generated})")


if __name__ == "__main__":
    asyncio.run(generate_scripts())
