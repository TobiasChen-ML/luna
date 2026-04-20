"""
Generate Mature clones of all existing scripts.
Each existing script gets an _mature variant with mature_scenes injected into full_script.
Run: python -m app.migrations.generate_mature_scripts
"""
import asyncio
import json
import os
import random
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import db

# ---------------------------------------------------------------------------
# MATURE scene templates keyed by relation_type.
# Each entry has multiple scene pools; one is picked per script instance.
# ---------------------------------------------------------------------------

MATURE_SCENES: dict[str, list[dict]] = {
    # ── 家庭禁忌 ────────────────────────────────────────────────────────────
    "aunt_paternal_nephew": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "肢體曖昧",
            "description": "叔叔再度出差，深夜你送餐進房，她不經意地靠上你的肩，香氣縈繞。",
            "dialogue": [
                "「你…不用那麼近。」",
                "「怎麼了，你不喜歡嗎？」她輕聲笑，眼睫輕顫。",
                "「不是…只是…」你的心跳快到說不完整的話。",
            ],
            "choices": [
                {"text": "輕輕回握她的手", "effect": "好感度+25，進入深度親密線"},
                {"text": "緩緩後退，壓下心跳", "effect": "好感度+5，維持曖昧張力"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "夜深人靜，她倚在門框說失眠，你讓她進來，燈光昏黃，彼此都清楚這一步跨出去便再也回不了頭。",
            "dialogue": [
                "「你知道我在等什麼嗎？」她的聲音低了下去。",
                "「知道…」你靠近，呼吸交疊。",
                "「那就別再讓我等了。」",
            ],
            "choices": [
                {"text": "主動擁住她", "effect": "進入 Mature 結局線"},
                {"text": "猶豫地別開眼", "effect": "進入禁忌暗戀線"},
            ],
        },
    ],
    "uncle_maternal_niece": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "肢體曖昧",
            "description": "你不小心摔跤，他扶住你的腰，兩人對視的瞬間誰也沒有鬆手。",
            "dialogue": [
                "「還好嗎？」他的聲音比平常低沉。",
                "「沒…沒事。」你感覺到他的手指微微用力。",
                "「那就好。」但他沒有放開。",
            ],
            "choices": [
                {"text": "輕輕推開，假裝沒察覺", "effect": "好感度+8，維持暧昧"},
                {"text": "抬頭看他的眼睛", "effect": "好感度+20，觸發下一幕"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "他開車送你回家，停在巷口熄火，車廂裡只剩彼此的呼吸聲。",
            "dialogue": [
                "「你知道你對我做了什麼嗎？」他轉頭，眼神深沉。",
                "「我…」你說不出話，只看著他慢慢靠近。",
                "「從你成年那天我就一直在忍。」",
            ],
            "choices": [
                {"text": "閉上眼睛迎上去", "effect": "進入 Mature 結局線"},
                {"text": "「我們…應該進去了。」", "effect": "進入糾纏暗線"},
            ],
        },
    ],
    "aunt_maternal_nephew": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "肢體曖昧",
            "description": "家族聚會散場，她借酒裝醉，你扶她上樓，她突然抱住你的頸說「你不一樣」。",
            "dialogue": [
                "「姨…你喝太多了。」",
                "「我沒醉，我只是…終於敢了。」她睜開眼，清明得可怕。",
            ],
            "choices": [
                {"text": "輕輕扣住她的手腕", "effect": "好感度+20"},
                {"text": "假裝相信她喝醉", "effect": "好感度+5，維持曖昧"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "她說「讓我做你的女人」時，你發現那句話讓你一步也移不開。",
            "dialogue": [
                "「你媽知道了會怎麼說？」她笑著問。",
                "「不知道，但現在我只在乎你怎麼說。」",
            ],
            "choices": [
                {"text": "把她拉進懷裡", "effect": "進入 Mature 結局線"},
                {"text": "「我需要時間。」", "effect": "進入糾纏暗線"},
            ],
        },
    ],
    "uncle_paternal_niece": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "肢體曖昧",
            "description": "他替你扣外套釦子，動作很慢，視線卻沒有落在釦子上。",
            "dialogue": [
                "「別動。」他低聲說，手指停在最後一顆。",
                "「…好。」你連呼吸都放輕了。",
            ],
            "choices": [
                {"text": "仰起臉看他", "effect": "好感度+20，觸發親密線"},
                {"text": "輕輕別開視線", "effect": "好感度+8"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "他說「你姑姑不懂我」，你知道那是危險的話，卻沒有離開。",
            "dialogue": [
                "「你懂我。」他的手掌覆上你的臉頰，溫熱而確定。",
                "「這樣不對…」",
                "「我知道。但我不想假裝這不是真的。」",
            ],
            "choices": [
                {"text": "閉上眼睛，任由他靠近", "effect": "進入 Mature 結局線"},
                {"text": "「我走了。」轉身離開", "effect": "進入禁忌逃離線"},
            ],
        },
    ],
    "aunt_paternal_niece": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "肢體曖昧",
            "description": "深夜她敲你的門，頭髮散著，說睡不著，你讓她進來後發現兩個人之間的距離越來越近。",
            "dialogue": [
                "「別叫我姑姑。」她突然說。",
                "「那叫…」",
                "「叫我名字。」她的眼神裡有你從未見過的東西。",
            ],
            "choices": [
                {"text": "輕聲叫出她的名字", "effect": "好感度+25，進入深度親密線"},
                {"text": "沉默地看著她", "effect": "好感度+10"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "她說你是她最特別的存在，然後把門從裡面鎖上。",
            "dialogue": [
                "「你不害怕嗎？」你問。",
                "「比這個更讓我害怕的，是一直壓著自己。」",
            ],
            "choices": [
                {"text": "走向她", "effect": "進入 Mature 結局線"},
                {"text": "「我們都需要冷靜。」", "effect": "進入糾纏暗線"},
            ],
        },
    ],
    "stepsister_stepbrother": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "肢體曖昧",
            "description": "半夜她溜進你的房，說做惡夢了，坐在你床邊，薄薄一層睡衣，月光打在她肩上。",
            "dialogue": [
                "「我只是…不想一個人。」她輕聲說。",
                "「我們不是親生的。」你看著她說出那句話。",
                "「我知道。所以我才來。」",
            ],
            "choices": [
                {"text": "拉開被子讓她進來", "effect": "好感度+25，進入深度親密線"},
                {"text": "「回你房間去。」", "effect": "好感度+5，維持張力"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "父母出遠門，整棟房子只剩你們兩個人，她站在廚房說「今晚想吃你做的菜」，但你們誰都知道那不是重點。",
            "dialogue": [
                "「你確定只是要吃飯？」你走近她。",
                "「……不確定。」她抬頭，臉頰微紅。",
            ],
            "choices": [
                {"text": "傾身，越過她去關爐火", "effect": "進入 Mature 結局線"},
                {"text": "乖乖去洗菜", "effect": "進入糾纏暗線"},
            ],
        },
    ],
    "sister_in_law": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "肢體曖昧",
            "description": "她在廚房哭，你遞紙巾，她抓住你的手，眼淚落在你手背上。",
            "dialogue": [
                "「他從來不懂我。」",
                "「我知道。」你沒有抽手。",
                "「那你呢…你懂嗎？」她抬起頭，眼眶還是紅的。",
            ],
            "choices": [
                {"text": "把她的手握緊", "effect": "好感度+20，進入禁忌線"},
                {"text": "「你先平靜一下。」", "effect": "好感度+8"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "哥哥出差，她傳訊說「一個人怕」，你去了，發現她開了燈，換了衣服，不像害怕的樣子。",
            "dialogue": [
                "「你早就知道我會來。」",
                "「嗯。」她點頭，直視你，不躲避。",
                "「那你還是要？」",
                "「我想要你來。」",
            ],
            "choices": [
                {"text": "鎖上門", "effect": "進入 Mature 結局線"},
                {"text": "「我去沙發。」", "effect": "進入克制暗線"},
            ],
        },
    ],
    # ── 校園禁忌 ────────────────────────────────────────────────────────────
    "principal_student": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "辦公室曖昧",
            "description": "你留到最後一個，辦公室只剩你們兩個人，他站起來幫你整理衣領，動作停在那裡沒有繼續。",
            "dialogue": [
                "「您在做什麼…」",
                "「你領子歪了。」他的聲音很低，眼神不是在看領子。",
            ],
            "choices": [
                {"text": "仰起臉看他", "effect": "好感度+20，觸發親密線"},
                {"text": "後退一步道謝", "effect": "好感度+5"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "他把辦公室門鎖上，說「只有你能讓我露出這種表情」。",
            "dialogue": [
                "「這樣不對…」你說。",
                "「我知道。但你也想，不是嗎？」",
            ],
            "choices": [
                {"text": "沉默地走近他", "effect": "進入 Mature 結局線"},
                {"text": "「我要走了。」", "effect": "進入禁忌逃離線"},
            ],
        },
    ],
    "homeroom_teacher_student": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "補課曖昧",
            "description": "課後補習，你問完最後一道題，她把筆蓋上，說「你不是真的來問數學的吧」。",
            "dialogue": [
                "「我…」你無法否認。",
                "「我也不是只想教數學。」她站起來，走到你這側。",
            ],
            "choices": [
                {"text": "回握她放在桌上的手", "effect": "好感度+25"},
                {"text": "假裝沒聽懂", "effect": "好感度+5，維持曖昧"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "她含淚說「我只對你特殊」，教室的燈只剩一盞，你知道這一刻以後都不一樣了。",
            "dialogue": [
                "「我知道這樣不行…」她說。",
                "「但是我停不下來。」你站起來，站在她面前。",
            ],
            "choices": [
                {"text": "替她擦掉眼淚，然後靠近", "effect": "進入 Mature 結局線"},
                {"text": "「老師…我等到畢業。」", "effect": "進入等待結局線"},
            ],
        },
    ],
    "grade_director_student": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "辦公室曖昧",
            "description": "他把你堵在辦公室角落，說「你知道我每次找你不只是為了記過吧」。",
            "dialogue": [
                "「那是為了什麼？」你抬頭問他。",
                "「你真的不知道？」他靠近了一步，彼此的距離剩下一個呼吸。",
            ],
            "choices": [
                {"text": "「…知道。」輕聲回答", "effect": "好感度+25，觸發親密線"},
                {"text": "「不知道，請主任說清楚。」", "effect": "好感度+10，維持張力"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "他握住你的手說「別告訴別人」，然後沒有再說話，只是靠得更近。",
            "dialogue": [
                "「主任…」",
                "「叫我名字。」他低聲說，目光落在你的唇上。",
            ],
            "choices": [
                {"text": "輕輕叫出他的名字", "effect": "進入 Mature 結局線"},
                {"text": "「我不能。」", "effect": "進入糾纏暗線"},
            ],
        },
    ],
    "dean_student": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "辦公室曖昧",
            "description": "她說「我這樣做都是為了你」，然後把門關上，你們第一次真正面對彼此。",
            "dialogue": [
                "「您為什麼要特別幫我？」",
                "「因為我沒辦法不幫你。」她平靜地看著你，那不是教務主任的眼神。",
            ],
            "choices": [
                {"text": "走向她", "effect": "好感度+25，進入深度親密線"},
                {"text": "「謝謝您。」低頭回避", "effect": "好感度+8"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "深夜她在辦公室崩潰，你陪在旁邊，她抬起頭說「抱我一下，只要一下」。",
            "dialogue": [
                "「老師…」你張開雙臂，她靠了進來。",
                "「謝謝你還在。」她聲音很小，身體卻貼得很緊。",
            ],
            "choices": [
                {"text": "把她抱緊，低下頭", "effect": "進入 Mature 結局線"},
                {"text": "輕拍她的背，保持距離", "effect": "進入守護暗線"},
            ],
        },
    ],
    "discipline_master_student": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "訓導室曖昧",
            "description": "他把你堵在角落，手撐在牆上，說「你以為我每次找你是真的要罰你？」",
            "dialogue": [
                "「那是…」",
                "「我只是想見到你。」他臉上難得出現一絲慌亂。",
            ],
            "choices": [
                {"text": "「那下次直接找我就好。」", "effect": "好感度+25，進入親密線"},
                {"text": "把他的手臂撥開走人", "effect": "好感度+5，維持張力"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "他把你拉進空教室，鎖上門，說「我知道這樣不對，但我管不了自己」。",
            "dialogue": [
                "「那你要怎樣？」你靠著牆，仰頭看他。",
                "「你讓我怎樣，我就怎樣。」他一字一句說清楚。",
            ],
            "choices": [
                {"text": "抓住他的衣領把他拉近", "effect": "進入 Mature 結局線"},
                {"text": "「等我畢業。」", "effect": "進入等待結局線"},
            ],
        },
    ],
    "dorm_manager_student": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "宿舍曖昧",
            "description": "深夜她打開你的房門，說忘了收你的備用鑰匙，然後站在門口沒有離開。",
            "dialogue": [
                "「鑰匙…你拿走了嗎？」你看著她手裡空無一物的手。",
                "「忘了。」她輕聲說，眼睛看著你，不是看鑰匙。",
            ],
            "choices": [
                {"text": "「那進來吧。」側身讓開", "effect": "好感度+25，進入深度親密線"},
                {"text": "「我去找一下。」轉身找鑰匙", "effect": "好感度+5"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "凌晨她說「別告訴別人」，然後在你的房間呆到天亮。",
            "dialogue": [
                "「妳不用走嗎？」",
                "「查寢的人就是我。」她淡定地說，然後把燈關上。",
            ],
            "choices": [
                {"text": "把她拉過來", "effect": "進入 Mature 結局線"},
                {"text": "「那…晚安。」躺下假裝睡著", "effect": "進入糾纏暗線"},
            ],
        },
    ],
    # ── 社會禁忌 ────────────────────────────────────────────────────────────
    "classmate_mother": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "家庭拜訪曖昧",
            "description": "同學臨時有事，你和她獨處在客廳，她換了衣服出來，比平日更隨性。",
            "dialogue": [
                "「你不怕同學回來嗎？」你問。",
                "「他今晚不回來。」她坐在你旁邊，非常近。",
            ],
            "choices": [
                {"text": "回視她不躲開", "effect": "好感度+20，觸發親密線"},
                {"text": "假裝看電視", "effect": "好感度+5，維持張力"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "她說「把我當女人看好嗎」，你沒有拒絕，而是沉默地靠近她。",
            "dialogue": [
                "「你是一直都…？」你問。",
                "「從你第一次來這裡就是了。」她握住你的手。",
            ],
            "choices": [
                {"text": "把她的手放在你的心口", "effect": "進入 Mature 結局線"},
                {"text": "「阿姨…」低頭掙扎", "effect": "進入糾纏暗線"},
            ],
        },
    ],
    "classmate_sister": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "偶遇曖昧",
            "description": "她說「我喜歡的人是你」，然後把視線別開，指尖在桌沿輕輕劃著。",
            "dialogue": [
                "「你…確定嗎？」",
                "「說出來之前我想了一年。」她抬頭，眼神直接。",
            ],
            "choices": [
                {"text": "走向她", "effect": "好感度+20，進入告白後線"},
                {"text": "「你哥知道嗎？」", "effect": "好感度+5，進入糾結線"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "在你耳邊她說「不讓同學知道」，然後手扣上你的手腕，把你帶進門。",
            "dialogue": [
                "「你哥哥那邊…」",
                "「我去處理。但現在…」她轉過身，臉很近，「現在是我們的時間。」",
            ],
            "choices": [
                {"text": "把門帶上", "effect": "進入 Mature 結局線"},
                {"text": "「等你哥同意。」", "effect": "進入等待結局線"},
            ],
        },
    ],
    "friend_sister": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "告白後曖昧",
            "description": "她說「我一直都喜歡你」後沒有跑掉，反而一步一步走近，讓你退到牆邊。",
            "dialogue": [
                "「你的回應呢？」她仰頭問，距離只剩幾公分。",
                "「妳朋友…你哥哥…」",
                "「先告訴我你的感受。」",
            ],
            "choices": [
                {"text": "「我也喜歡你。」然後靠下去", "effect": "好感度+25，進入 Mature 線"},
                {"text": "「讓我想想。」", "effect": "好感度+8，維持張力"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "她把你的外套抓住說「別走」，拉力很小，但你沒有動。",
            "dialogue": [
                "「那你說，你想要我做什麼。」你站在原地問她。",
                "「留下來。」她貼上你的胸口，「整晚。」",
            ],
            "choices": [
                {"text": "把她抱起來", "effect": "進入 Mature 結局線"},
                {"text": "「把你哥哥的事處理好再說。」", "effect": "進入友情危機線"},
            ],
        },
    ],
    "friend_older_sister": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "成熟女性曖昧",
            "description": "她說「別把我當姐姐」，然後把耳鬢的頭髮撥開，用一種你不熟悉的眼神看你。",
            "dialogue": [
                "「那叫你什麼？」你問。",
                "「叫我名字。你一直都可以。」她微微一笑，不同於平常。",
            ],
            "choices": [
                {"text": "第一次叫出她的名字", "effect": "好感度+25，進入深度親密線"},
                {"text": "「…姐姐。」還是叫了那個稱呼", "effect": "好感度+10，進入撩撥線"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "你朋友不在，她打電話說「過來一下」，開門時她披著頭髮，燈開得很暗。",
            "dialogue": [
                "「有事？」你問，但你知道沒有事。",
                "「有你就夠了。」她把門帶上。",
            ],
            "choices": [
                {"text": "走向她", "effect": "進入 Mature 結局線"},
                {"text": "「朋友知道了會怎樣？」", "effect": "進入糾結線"},
            ],
        },
    ],
    "friend_mother": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "家庭拜訪曖昧",
            "description": "她說「你是第一個讓我覺得被理解的人」，說完握住你的手，不像長輩的姿態。",
            "dialogue": [
                "「阿姨…」",
                "「我說過了，叫我名字。」她的拇指在你手背輕輕摩挲。",
            ],
            "choices": [
                {"text": "翻轉手，握住她的手", "effect": "好感度+25，觸發親密線"},
                {"text": "抽回手，假裝找茶杯", "effect": "好感度+8"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "她說「老公從來不懂我」，眼眶紅了又強忍住，你伸手的瞬間她撲進你懷裡。",
            "dialogue": [
                "「你可以讓我待一下嗎？」她悶聲問。",
                "「當然。」你把她抱緊，心知道這一步越了線。",
            ],
            "choices": [
                {"text": "低頭輕聲叫她名字", "effect": "進入 Mature 結局線"},
                {"text": "輕拍她的背，保持理智", "effect": "進入守護暗線"},
            ],
        },
    ],
    "friend_brother": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "深夜告白曖昧",
            "description": "深夜他傳訊說「過來，有話說」，你去了，他遞了一杯酒說「我暗戀你很久了」。",
            "dialogue": [
                "「我不把你當弟弟/妹妹。」他直視你。",
                "「那…你把我當什麼？」",
                "「我想你自己說。」他靠近，不說話，等待。",
            ],
            "choices": [
                {"text": "「當你喜歡的人。」", "effect": "好感度+25，進入告白後線"},
                {"text": "舉起酒杯躲避回答", "effect": "好感度+5，維持曖昧"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "他說「朋友的事我來處理」，然後把你帶進房間，說「現在只有我們」。",
            "dialogue": [
                "「你不怕你朋友嗎？」",
                "「我怕失去你更多。」他的聲音很低，卻很清楚。",
            ],
            "choices": [
                {"text": "踮腳吻上去", "effect": "進入 Mature 結局線"},
                {"text": "「先和朋友說清楚。」", "effect": "進入友情危機線"},
            ],
        },
    ],
    "doctor_nurse": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "值班室曖昧",
            "description": "值班室只剩你們兩個，他說「喜歡你喜歡了很久，但不知道怎麼開口」。",
            "dialogue": [
                "「那你現在說了。」你放下病歷看他。",
                "「嗯。」他走近，手術服的氣味很近。「你的回應呢？」",
            ],
            "choices": [
                {"text": "站起來，靠向他", "effect": "好感度+25，觸發親密線"},
                {"text": "「等下個班再說。」", "effect": "好感度+10，維持張力"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "他把值班室從裡面鎖上，說「你白大褂天使」，聲音啞了。",
            "dialogue": [
                "「醫生現在不像醫生了。」你說。",
                "「對你來說我不想是醫生。」他靠過來。",
            ],
            "choices": [
                {"text": "解下他的聽診器", "effect": "進入 Mature 結局線"},
                {"text": "「病人還在等。」推開他", "effect": "進入職業克制線"},
            ],
        },
    ],
    "nurse_patient": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "病房夜間曖昧",
            "description": "深夜她來補記錄，坐在你床邊，說「其實我一直在想辦法多排你的班」。",
            "dialogue": [
                "「護士…你這樣說合適嗎？」",
                "「不合適。」她輕聲說，「但是真的。」她的手還放在點滴管旁邊，很近。",
            ],
            "choices": [
                {"text": "握住她的手", "effect": "好感度+20，進入深度線"},
                {"text": "「你幾點下班？」", "effect": "好感度+15，維持曖昧"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "出院前夜她說「出院後我們還能見面嗎」，你沒有回答，而是把她的手拉到胸口。",
            "dialogue": [
                "「你感受到了嗎？」你說。",
                "「感受到了。」她抬頭，病房的夜燈很暗，她的眼睛卻很亮。",
            ],
            "choices": [
                {"text": "把她拉近親吻", "effect": "進入 Mature 結局線"},
                {"text": "「出院後我第一個找你。」", "effect": "進入等待結局線"},
            ],
        },
    ],
    "director_actor": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "片場曖昧",
            "description": "拍吻戲前他靠近說「這場戲我只信任你」，但導演椅到你身邊的距離讓人分不清是戲是真。",
            "dialogue": [
                "「你是在說戲嗎？」你問。",
                "「你說呢？」他低下頭，攝影機的快門聲消失了。",
            ],
            "choices": [
                {"text": "仰起臉主動靠近", "effect": "好感度+20，進入戲外情線"},
                {"text": "「導演，開拍吧。」", "effect": "好感度+10，維持曖昧張力"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "殺青夜他說「戲裡的感情是真的」，然後把你帶進導演室，關上所有燈。",
            "dialogue": [
                "「螢幕之外的你才是我想要的。」",
                "「導演…」你的呼吸亂了。",
                "「現在不用叫我導演。」",
            ],
            "choices": [
                {"text": "抓住他的衣領", "effect": "進入 Mature 結局線"},
                {"text": "「等電影上映後。」", "effect": "進入克制線"},
            ],
        },
    ],
    "convenience_store_owner": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "深夜便利店曖昧",
            "description": "打烊後她沒讓你走，把翻牌轉成「公休」，說「今晚只有我們」。",
            "dialogue": [
                "「妳這樣…不怕客訴嗎？」",
                "「只要你不說，誰知道？」她把圍裙解下，坐上收銀台。",
            ],
            "choices": [
                {"text": "走向她，站在收銀台前", "effect": "好感度+25，進入深度線"},
                {"text": "「這樣不太好吧。」", "effect": "好感度+8，維持曖昧"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "她說「我等你很久了」，燈光只剩儲藏室那一盞，她把鑰匙塞進你手裡。",
            "dialogue": [
                "「這是什麼意思？」你握著鑰匙問。",
                "「你猜。」她走進儲藏室，留著門縫等你。",
            ],
            "choices": [
                {"text": "跟進去，把門帶上", "effect": "進入 Mature 結局線"},
                {"text": "「我明天再來。」", "effect": "進入糾纏暗線"},
            ],
        },
    ],
    "bakery_owner_customer": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "麵包店曖昧",
            "description": "打烊後他說「這是只為你做的」，遞來一個沒有標籤的小蛋糕，上面寫著你的名字。",
            "dialogue": [
                "「你…什麼時候記住我名字的？」",
                "「第二次來的時候。」他靠著案台看你，「你第幾次來了？」",
                "「很多次了…」",
                "「我知道。我每次都在等。」",
            ],
            "choices": [
                {"text": "繞過案台走向他", "effect": "好感度+25，進入深度親密線"},
                {"text": "低頭吃蛋糕假裝沒聽見", "effect": "好感度+10，維持曖昧"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "下雨天他讓你在店裡躲雨，然後重新開燈，說「今晚我不想讓你走」。",
            "dialogue": [
                "「雨停了也不用走嗎？」你問。",
                "「嗯。」他走近，麵粉的氣味很淡，但很近。",
            ],
            "choices": [
                {"text": "站起來，仰頭看他", "effect": "進入 Mature 結局線"},
                {"text": "「那就再等等雨。」", "effect": "進入糾纏暗線"},
            ],
        },
    ],
    # ── 通用關係（auto_* 系列補充）─────────────────────────────────────────
    "boss_subordinate": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "辦公室曖昧",
            "description": "加班到深夜，他把外套披在你肩上，站在你身後沒有離開。",
            "dialogue": [
                "「謝謝您…」你轉身，他站得很近。",
                "「別謝我。」他低頭，聲音壓低。「謝了我反而很難辦。」",
            ],
            "choices": [
                {"text": "仰起臉問「為什麼難辦」", "effect": "好感度+20，觸發親密線"},
                {"text": "低頭繼續工作", "effect": "好感度+5，維持張力"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "他把辦公室門鎖上，說「你知道為什麼我只找你加班嗎」。",
            "dialogue": [
                "「因為我效率好？」你試探地問。",
                "「因為我想見你。」他說得很直接，眼神更直接。",
            ],
            "choices": [
                {"text": "站起來走向他", "effect": "進入 Mature 結局線"},
                {"text": "「這樣不合適。」", "effect": "進入職場克制線"},
            ],
        },
    ],
    "teacher_student": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "補課曖昧",
            "description": "課後只剩你們，她說「你不是真的在聽課」，你承認了，她靠近問「那你在看什麼」。",
            "dialogue": [
                "「看…」你說不下去。",
                "「看我嗎？」她的聲音低了下去，不再像老師。",
            ],
            "choices": [
                {"text": "「嗯。」點頭承認", "effect": "好感度+25，觸發親密線"},
                {"text": "轉移話題回到課本", "effect": "好感度+5"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "她說「等你畢業」，然後卻是她先打破了那條線，把教室的燈關上。",
            "dialogue": [
                "「不是說等畢業嗎？」你問。",
                "「等不了了。」她走過來，「你也等不了，對嗎？」",
            ],
            "choices": [
                {"text": "把她拉進懷裡", "effect": "進入 Mature 結局線"},
                {"text": "「老師…再忍一下。」", "effect": "進入等待結局線"},
            ],
        },
    ],
    "affair": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "秘密見面曖昧",
            "description": "他說「你讓我沒辦法假裝什麼都沒有」，然後把你帶去那個只有你們知道的地方。",
            "dialogue": [
                "「你知道這樣不對。」你說。",
                "「知道。但是我控制不了。」他低頭，額抵上你的額，「你呢？」",
            ],
            "choices": [
                {"text": "閉上眼睛，手扣上他的手", "effect": "好感度+25，進入深度親密線"},
                {"text": "「我們應該停下來。」", "effect": "好感度+5，維持糾纏"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "酒店的房卡在桌上，他說「這一步我做不了決定，只有你能。」",
            "dialogue": [
                "「你知道這代表什麼。」你看著那張卡說。",
                "「知道。所以讓你來決定。」他不催，只是等。",
            ],
            "choices": [
                {"text": "拿起房卡", "effect": "進入 Mature 結局線"},
                {"text": "「再等一下，等我想清楚。」", "effect": "進入糾纏暗線"},
            ],
        },
    ],
    "contract_lovers": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "契約外曖昧",
            "description": "他說「合約裡沒有這條」，然後把你抵在牆上，「但我想要」。",
            "dialogue": [
                "「你超出範圍了。」你說。",
                "「加條款。」他靠得很近，「你同意嗎？」",
            ],
            "choices": [
                {"text": "「同意。」輕聲回答", "effect": "好感度+25，進入真愛線"},
                {"text": "「要重新簽約。」推開他", "effect": "好感度+10，維持張力"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "合約到期的最後一夜，他把合約撕掉，說「這個不需要了」。",
            "dialogue": [
                "「那我們是什麼？」你問。",
                "「是我的人。」他說得很篤定，然後靠近，「你說呢？」",
            ],
            "choices": [
                {"text": "推他倒在沙發上", "effect": "進入 Mature 結局線"},
                {"text": "「再寫一份新的。」", "effect": "進入正式戀人線"},
            ],
        },
    ],
    "ex_lovers": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "重逢曖昧",
            "description": "他說「你還是一樣」，手放在你臉頰旁邊沒有碰，像在確認什麼。",
            "dialogue": [
                "「我們分開很久了。」你說。",
                "「但是我沒有忘記。」他很近，「你忘了嗎？」",
            ],
            "choices": [
                {"text": "「沒有。」低聲承認", "effect": "好感度+25，觸發親密線"},
                {"text": "轉開臉，「我走了。」", "effect": "好感度+5，維持克制"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "他說「這次我不讓你走了」，然後把門關上，把你的手拉到他的胸口。",
            "dialogue": [
                "「你的心跳。」你說。",
                "「一直都是你造成的。」他把你的手按緊，低下頭。",
            ],
            "choices": [
                {"text": "仰起臉迎上去", "effect": "進入 Mature 結局線"},
                {"text": "「我需要你先解釋當初。」", "effect": "進入和解後的情感線"},
            ],
        },
    ],
    "bodyguard_employer": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "貼身保護曖昧",
            "description": "他把你護在牆邊，危機解除後兩人對視，他的手還按著你的肩膀沒有鬆開。",
            "dialogue": [
                "「危險解除了。」你說。",
                "「我知道。」他低頭，「但我還不想放開。」",
            ],
            "choices": [
                {"text": "把手放上他的手背", "effect": "好感度+20，觸發親密線"},
                {"text": "「去報告情況。」", "effect": "好感度+5，維持職業張力"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "他說「保護你是職責，但喜歡你是我自己的事」，然後跨越了那條線。",
            "dialogue": [
                "「這不符合規定。」你說。",
                "「我知道。」他把槍放下，「所以我現在不是你的保鑣。」他靠近，「我是你喜歡的人。」",
            ],
            "choices": [
                {"text": "抓住他的衣領拉近", "effect": "進入 Mature 結局線"},
                {"text": "「任務結束後再說。」", "effect": "進入克制等待線"},
            ],
        },
    ],
    "master_servant": [
        {
            "scene_id": "tension_1",
            "trigger": "好感度 ≥ 60%",
            "scene_type": "身份逾越曖昧",
            "description": "他抬起頭說「我知道這樣不應該」，卻沒有低下頭，眼神直視著你。",
            "dialogue": [
                "「你在想什麼？」你問。",
                "「想著如果我不是你的僕從，我現在會做什麼。」",
            ],
            "choices": [
                {"text": "「那你現在就做。」", "effect": "好感度+25，觸發親密線"},
                {"text": "「別這樣。」別開視線", "effect": "好感度+8，維持身份張力"},
            ],
        },
        {
            "scene_id": "intimate_1",
            "trigger": "好感度 ≥ 85%",
            "scene_type": "親密場景",
            "description": "他說「我不要再是您的僕人了」，然後第一次用你的名字，不帶任何敬語。",
            "dialogue": [
                "「你知道你在說什麼嗎？」",
                "「知道。」他站起來，第一次和你平視，「所以我才說。」",
            ],
            "choices": [
                {"text": "走下台階，站在他面前", "effect": "進入 Mature 結局線"},
                {"text": "「退下。」但聲音發抖", "effect": "進入禁忌克制線"},
            ],
        },
    ],
}

# 通用 MATURE 場景模板 (適用於無對應 relation_type 的劇本)
GENERIC_MATURE_SCENES: list[dict] = [
    {
        "scene_id": "tension_1",
        "trigger": "好感度 ≥ 60%",
        "scene_type": "肢體曖昧",
        "description": "一個不經意的接觸，讓空氣都凝固了，誰也沒有先退開。",
        "dialogue": [
            "「你…」",
            "「別說話。」TA低聲說，距離很近，呼吸清晰可聞。",
        ],
        "choices": [
            {"text": "閉上眼睛，不抵抗", "effect": "好感度+20，進入深度親密線"},
            {"text": "後退一步，深呼吸", "effect": "好感度+5，維持曖昧張力"},
        ],
    },
    {
        "scene_id": "intimate_1",
        "trigger": "好感度 ≥ 85%",
        "scene_type": "親密場景",
        "description": "門被帶上，燈光昏黃，彼此都清楚接下來會發生什麼，卻沒有一個人想要阻止。",
        "dialogue": [
            "「你確定嗎？」TA問，給你最後一次退出的機會。",
            "「確定。」你說，然後靠了過去。",
        ],
        "choices": [
            {"text": "主動靠近TA", "effect": "進入 Mature 結局線"},
            {"text": "「我需要一點時間。」", "effect": "進入糾纏暗線"},
        ],
    },
]

# Mature 結局模板
Mature_ENDINGS = {
    "good": [
        "你們跨越了所有界限，在只屬於彼此的夜晚裡，確認了那份無法否認的感情。",
        "身體誠實地說出了口中說不出的話，這一夜讓你們再也無法回頭。",
        "TA把你抱緊，說「這就是我想要的」，燈光熄滅前，你知道你們都找到了答案。",
    ],
    "secret": [
        "這個夜晚成為你們共同保守的秘密，每次相視時，眼神裡都帶著只有彼此懂得的溫度。",
        "誰也不說，誰也不問，但從這一晚之後，你們之間多了一層任何人都撕不開的羈絆。",
        "「只有我們知道。」TA在你耳邊說，然後把燈關上。",
    ],
}


def _pick_mature_scenes(relation_types: list[str]) -> list[dict]:
    """選取對應關係類型的 MATURE 場景，否則使用通用模板。"""
    for rel in relation_types:
        if rel in MATURE_SCENES:
            scenes = MATURE_SCENES[rel]
            # 隨機選 tension + intimate 各一組
            tension = [s for s in scenes if s["scene_id"].startswith("tension")]
            intimate = [s for s in scenes if s["scene_id"].startswith("intimate")]
            result = []
            if tension:
                result.append(random.choice(tension))
            if intimate:
                result.append(random.choice(intimate))
            return result
    return list(GENERIC_MATURE_SCENES)


def _build_mature_full_script(original_full_script: dict | None, mature_scenes: list[dict]) -> dict:
    """在原有 full_script 基礎上注入 mature_scenes 與 Mature 結局。"""
    base = dict(original_full_script) if original_full_script else {}

    base["mature_scenes"] = mature_scenes
    base["mature_endings"] = {
        "good": random.choice(Mature_ENDINGS["good"]),
        "secret": random.choice(Mature_ENDINGS["secret"]),
    }

    # 升級 character_inner_state climax 描述
    if "character_inner_state" in base:
        base["character_inner_state"] = dict(base["character_inner_state"])
        base["character_inner_state"]["climax"] = (
            base["character_inner_state"].get("climax", "TA終於無法壓抑")
            + "，身體的接觸讓一切掩飾都失去意義。"
        )

    # 在 narrative_beats 末尾加入 Mature 節拍
    beats = list(base.get("narrative_beats", []))
    beats.append({
        "scene": mature_scenes[0]["description"] if mature_scenes else "曖昧的肢體接觸",
        "emotion": "慾望與猶豫交織",
        "hint": mature_scenes[0]["choices"][0]["text"] if mature_scenes and mature_scenes[0].get("choices") else "你的選擇決定一切",
    })
    if len(mature_scenes) > 1:
        beats.append({
            "scene": mature_scenes[1]["description"],
            "emotion": "無法抑制的親密",
            "hint": mature_scenes[1]["choices"][0]["text"] if mature_scenes[1].get("choices") else "放開所有顧慮",
        })
    base["narrative_beats"] = beats

    return base


async def generate_mature_clones() -> None:
    await db.connect()

    count_result = await db.execute("SELECT COUNT(*) as count FROM script_library", fetch=True)
    total = count_result["count"] if count_result else 0
    print(f"Total existing scripts: {total}")

    # 取所有已發布劇本
    rows = await db.execute(
        "SELECT * FROM script_library WHERE status = 'published'",
        fetch_all=True,
    )
    if not rows:
        print("No published scripts found.")
        return

    print(f"Found {len(rows)} published scripts to clone.")

    batch_size = 100
    cloned = 0
    skipped = 0

    for i, row in enumerate(rows):
        original_id: str = row["id"]
        mature_id = f"{original_id}_mature"

        # 跳過已存在的 Mature 克隆
        existing = await db.execute(
            "SELECT id FROM script_library WHERE id = ?", (mature_id,), fetch=True
        )
        if existing:
            skipped += 1
            continue

        # 解析 relation_types
        try:
            relation_types: list[str] = json.loads(row.get("relation_types") or "[]")
        except Exception:
            relation_types = []

        # 選取 MATURE 場景
        mature_scenes = _pick_mature_scenes(relation_types)

        # 建立 Mature full_script
        original_full_script: dict | None = None
        fs_raw = row.get("full_script")
        if fs_raw:
            try:
                original_full_script = json.loads(fs_raw)
            except Exception:
                pass

        mature_full_script = _build_mature_full_script(original_full_script, mature_scenes)

        # 組裝 Mature 劇本標題
        title = row.get("title", "")
        title_en = row.get("title_en", "")
        mature_title = f"【Mature】{title}" if title else "【Mature】無題"
        mature_title_en = f"[Mature] {title_en}" if title_en else "[Mature] Untitled"

        now = datetime.utcnow().isoformat()

        await db.execute(
            """INSERT INTO script_library
               (id, title, title_en, summary, emotion_tones, relation_types,
                contrast_types, era, gender_target, character_gender, profession,
                length, age_rating, contrast_surface, contrast_truth, contrast_hook,
                script_seed, full_script, popularity, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                mature_id,
                mature_title,
                mature_title_en,
                row.get("summary"),
                row.get("emotion_tones"),
                row.get("relation_types"),
                row.get("contrast_types"),
                row.get("era"),
                row.get("gender_target"),
                row.get("character_gender"),
                row.get("profession"),
                row.get("length"),
                "mature",
                row.get("contrast_surface"),
                row.get("contrast_truth"),
                row.get("contrast_hook"),
                row.get("script_seed"),
                json.dumps(mature_full_script, ensure_ascii=False),
                0,
                "published",
                now,
                now,
            ),
        )
        cloned += 1

        if cloned % batch_size == 0:
            print(f"  Cloned {cloned} Mature scripts...")

    final = await db.execute("SELECT COUNT(*) as count FROM script_library", fetch=True)
    print(f"\nDone!")
    print(f"  Cloned:  {cloned}")
    print(f"  Skipped: {skipped} (already existed)")
    print(f"  Total scripts now: {final['count']}")


if __name__ == "__main__":
    asyncio.run(generate_mature_clones())
