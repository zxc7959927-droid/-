import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
import pandas as pd
from xgboost import XGBClassifier
from datetime import datetime, timedelta
import os
import re
from data import api_sports
st.set_page_config(
    page_title="莊家殺手賽事預測",
    layout="wide"
)

auto_refresh = st.sidebar.checkbox(
    "自動刷新比分",
    value=False
)

refresh_seconds = st.sidebar.selectbox(
    "刷新秒數",
    [10, 30, 60],
    index=1
)

if auto_refresh:
    st_autorefresh(
        interval=refresh_seconds * 1000,
        key="live_refresh"
    )

st.sidebar.divider()

allow_demo_data = st.sidebar.checkbox(
    "補充示範資料",
    value=True,
    help="API 資料太少時，自動補賽事，避免畫面空白。"
)

hot_only = st.sidebar.checkbox(
    "只看熱門聯盟",
    value=False
)

team_search = st.sidebar.text_input(
    "搜尋隊伍 / 聯盟",
    value="",
    placeholder="例：道奇、湖人、曼城、MLB"
)

show_debug = st.sidebar.checkbox(
    "顯示AI狀態檢查",
    value=False
)

compact_mobile = st.sidebar.checkbox(
    "手機精簡版",
    value=True
)

if "favorite_matches" not in st.session_state:
    st.session_state["favorite_matches"] = []

if "previous_scores" not in st.session_state:
    st.session_state["previous_scores"] = {}

st.title("🏆 莊家殺手賽事預測 v11.1 專業AI推薦版")
st.caption("此系統僅供體育數據分析與模擬預測使用，不能保證比賽結果。")


st.markdown(
    """
<style>
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}
[data-testid="stMetricValue"] {
    font-size: 28px;
}
@media (max-width: 768px) {
    .block-container {
        padding-left: 0.75rem;
        padding-right: 0.75rem;
    }
    h1 {
        font-size: 26px !important;
    }
    h2, h3 {
        font-size: 21px !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 22px;
    }
    .stButton button {
        width: 100%;
        font-size: 14px;
    }
}
</style>
""",
    unsafe_allow_html=True
)


st.divider()
st.subheader("📡 即時比分中心")
ai_panel_placeholder = st.empty()
st.caption("比分已自動載入。若要自動更新，請開啟左側「自動刷新比分」。")

COUNTRY_ZH = {
    "USA": "美國",
    "United States": "美國",
    "Mexico": "墨西哥",
    "Canada": "加拿大",
    "England": "英格蘭",
    "Spain": "西班牙",
    "Italy": "義大利",
    "Germany": "德國",
    "France": "法國",
    "Japan": "日本",
    "South Korea": "韓國",
    "China": "中國",
    "Taiwan": "台灣",
    "Brazil": "巴西",
    "Argentina": "阿根廷",
    "Portugal": "葡萄牙",
    "Netherlands": "荷蘭",
    "Australia": "澳洲",

    "Manchester City": "曼城",
    "Arsenal": "阿森納",
    "Liverpool": "利物浦",
    "Chelsea": "切爾西",
    "Real Madrid": "皇家馬德里",
    "Barcelona": "巴塞隆納",
    "Bayern Munich": "拜仁慕尼黑",
    "Paris Saint Germain": "巴黎聖日耳曼",
    "Al Nassr": "利雅德勝利",
    "Al Hilal": "利雅德新月",
    "Boston Celtics": "波士頓塞爾提克",
    "Miami Heat": "邁阿密熱火",
    "Phoenix Suns": "鳳凰城太陽",
    "Dallas Mavericks": "達拉斯獨行俠",
    "Denver Nuggets": "丹佛金塊",
    "New York Knicks": "紐約尼克",
    "Chicago Bulls": "芝加哥公牛",
    "Milwaukee Bucks": "密爾瓦基公鹿",
    "Minnesota Timberwolves": "明尼蘇達灰狼",
    "Houston Rockets": "休士頓火箭",
}

LEAGUE_ZH = {
    "MLB": "美國職棒大聯盟",
    "LMB": "墨西哥職棒聯盟",
    "PCL": "太平洋岸聯盟",
    "NBA": "美國職籃",
    "WNBA": "美國女子職籃",
    "MLS Next Pro": "美國 MLS Next Pro",
    "USL League Two": "美國 USL 二級聯賽",
    "Premier League": "英格蘭超級聯賽",
    "La Liga": "西班牙甲級聯賽",
    "Serie A": "義大利甲級聯賽",
    "Bundesliga": "德國甲級聯賽",
    "Ligue 1": "法國甲級聯賽",
    "UEFA Champions League": "歐洲冠軍聯賽",
    "USL League One Cup": "美國 USL 一級聯賽盃",
    "USL W League": "美國 USL 女子聯賽",
    "USL Championship": "美國足球冠軍聯賽",
    "MLS": "美國職業足球大聯盟",
}

TEAM_ZH = {
    # MLB
    "Arizona Diamondbacks": "亞利桑那響尾蛇",
    "Atlanta Braves": "亞特蘭大勇士",
    "Baltimore Orioles": "巴爾的摩金鶯",
    "Boston Red Sox": "波士頓紅襪",
    "Chicago Cubs": "芝加哥小熊",
    "Chicago White Sox": "芝加哥白襪",
    "Cincinnati Reds": "辛辛那提紅人",
    "Cleveland Guardians": "克里夫蘭守護者",
    "Colorado Rockies": "科羅拉多洛磯",
    "Detroit Tigers": "底特律老虎",
    "Houston Astros": "休士頓太空人",
    "Kansas City Royals": "堪薩斯市皇家",
    "Los Angeles Angels": "洛杉磯天使",
    "Los Angeles Dodgers": "洛杉磯道奇",
    "Miami Marlins": "邁阿密馬林魚",
    "Milwaukee Brewers": "密爾瓦基釀酒人",
    "Minnesota Twins": "明尼蘇達雙城",
    "New York Mets": "紐約大都會",
    "New York Yankees": "紐約洋基",
    "Oakland Athletics": "奧克蘭運動家",
    "Philadelphia Phillies": "費城費城人",
    "Pittsburgh Pirates": "匹茲堡海盜",
    "San Diego Padres": "聖地牙哥教士",
    "San Francisco Giants": "舊金山巨人",
    "Seattle Mariners": "西雅圖水手",
    "St. Louis Cardinals": "聖路易紅雀",
    "Tampa Bay Rays": "坦帕灣光芒",
    "Texas Rangers": "德州遊騎兵",
    "Toronto Blue Jays": "多倫多藍鳥",
    "Washington Nationals": "華盛頓國民",

    # PCL / MiLB
    "Salt Lake Bees": "鹽湖城蜜蜂",
    "Albuquerque Isotopes": "阿布奎基同位素",
    "Sacramento River Cats": "沙加緬度河貓",
    "Tacoma Rainiers": "塔科馬雨山",
    "Las Vegas Aviators": "拉斯維加斯飛行員",
    "Reno Aces": "雷諾王牌",
    "El Paso Chihuahuas": "艾爾帕索吉娃娃",
    "Sugar Land": "糖城",
    "Sugar Land Space Cowboys": "糖城太空牛仔",

    # LMB / Mexico
    "Bravos de Leon": "萊昂勇士",
    "Puebla": "普埃布拉",
    "Aguascalientes": "阿瓜斯卡連特斯",
    "Jalisco": "哈利斯科",
    "Campeche": "坎佩切",
    "Yucatan": "尤卡坦",
    "Laguna": "拉古納",
    "Caliente de Durango": "杜蘭戈熱火",
    "Diablos Rojos": "紅魔鬼",
    "Tabasco": "塔巴斯科",

    "Spokane Velocity": "斯波坎速度",
    "Boise": "博伊西",
    "Snohomish United W": "斯諾霍米什聯女足",
    "West Seattle Rhodies W": "西西雅圖羅迪斯女足",
    "New Mexico United": "新墨西哥聯",
    "Phoenix Rising": "鳳凰城崛起",
    "Hartford Athletic": "哈特福德競技",
    "Portland Hearts of Pine": "波特蘭松心",
    "Texoma": "德克索馬",
    "Loudoun United": "勞登聯",
    "Charleston Battery": "查爾斯頓電池",
    "Louisville City": "路易維爾城",
    "Tampa Bay Rowdies": "坦帕灣暴徒",
    "Indy Eleven": "印地十一",
    "Orange County SC": "橙縣SC",
    "Sacramento Republic": "沙加緬度共和",
    "San Antonio": "聖安東尼奧",
    "FC Tulsa": "塔爾薩FC",
    "Detroit City": "底特律城",
    "Oakland Roots": "奧克蘭根源",
    "Rhode Island": "羅德島",
    "Pittsburgh Riverhounds": "匹茲堡河犬",
    "North Carolina FC": "北卡羅萊納FC",
    "Monterey Bay": "蒙特雷灣",
    "Memphis 901": "曼菲斯901",
    "Miami FC": "邁阿密FC",
    "El Paso Locomotive": "艾爾帕索火車頭",
    "Colorado Springs": "科羅拉多泉",
    "Birmingham Legion": "伯明罕軍團",
    "Las Vegas Lights": "拉斯維加斯之光",

    # Soccer examples
    "Ventura County": "文圖拉郡",
    "Houston Dynamo FC II": "休士頓迪納摩二隊",
    "Ballard": "巴拉德",
    "Bangers": "班格斯",
    "Sportivo San Juan": "聖胡安體育",
    "Academica": "阿卡德米卡",
    "Los Angeles Lakers": "洛杉磯湖人",
    "Golden State Warriors": "金州勇士",

    "Manchester City": "曼城",
    "Arsenal": "阿森納",
    "Liverpool": "利物浦",
    "Chelsea": "切爾西",
    "Real Madrid": "皇家馬德里",
    "Barcelona": "巴塞隆納",
    "Bayern Munich": "拜仁慕尼黑",
    "Paris Saint Germain": "巴黎聖日耳曼",
    "Al Nassr": "利雅德勝利",
    "Al Hilal": "利雅德新月",
    "Boston Celtics": "波士頓塞爾提克",
    "Miami Heat": "邁阿密熱火",
    "Phoenix Suns": "鳳凰城太陽",
    "Dallas Mavericks": "達拉斯獨行俠",
    "Denver Nuggets": "丹佛金塊",
    "New York Knicks": "紐約尼克",
    "Chicago Bulls": "芝加哥公牛",
    "Milwaukee Bucks": "密爾瓦基公鹿",
    "Minnesota Timberwolves": "明尼蘇達灰狼",
    "Houston Rockets": "休士頓火箭",

    "Houston Astros": "休士頓太空人",
    "Seattle Mariners": "西雅圖水手",
    "Chicago Cubs": "芝加哥小熊",
    "San Francisco Giants": "舊金山巨人",
    "Philadelphia Phillies": "費城費城人",
    "Atlanta Braves": "亞特蘭大勇士",
    "Toronto Blue Jays": "多倫多藍鳥",
    "Baltimore Orioles": "巴爾的摩金鶯",
    "Arizona Diamondbacks": "亞利桑那響尾蛇",
    "Cincinnati Reds": "辛辛那提紅人",
    "Detroit Tigers": "底特律老虎",
    "Kansas City Royals": "堪薩斯市皇家",
    "Minnesota Twins": "明尼蘇達雙城",
    "Tampa Bay Rays": "坦帕灣光芒",
    "Washington Nationals": "華盛頓國民",
    "Miami Marlins": "邁阿密馬林魚",
    "Pittsburgh Pirates": "匹茲堡海盜",
    "St. Louis Cardinals": "聖路易紅雀",
    "Chicago White Sox": "芝加哥白襪",
    "Oakland Athletics": "奧克蘭運動家",
    "Portland Timbers II": "波特蘭伐木者二隊",
    "LA Galaxy II": "洛杉磯銀河二隊",
    "Los Angeles FC": "洛杉磯FC",
    "Inter Miami": "國際邁阿密",
}

STATUS_ZH = {
    "First Half": "上半場",
    "Second Half": "下半場",
    "Halftime": "中場休息",
    "Match Finished": "比賽結束",
    "Not Started": "尚未開始",
    "Postponed": "延期",
    "Cancelled": "取消",
    "Live": "進行中",
    "In Progress": "進行中",
}

def zh_country(name):
    return COUNTRY_ZH.get(name, name)

def zh_league(name):
    return LEAGUE_ZH.get(name, name)

def zh_team(name):
    if not name:
        return ""

    if name in TEAM_ZH:
        return TEAM_ZH[name]

    text = str(name)

    suffix_map = {
        " FC II": "二隊",
        " FC": "FC",
        " United W": "聯女足",
        " W": "女足",
        " United": "聯",
        " City": "城",
        " Athletic": "競技",
        " SC": "SC",
        " II": "二隊",
    }

    for en, zh in suffix_map.items():
        if text.endswith(en):
            base = text[:-len(en)]
            return f"{base}{zh}"

    return text

def zh_status(text):
    text = str(text or "")
    for en, zh in STATUS_ZH.items():
        text = text.replace(en, zh)
    return text

HOT_FOOTBALL = [
    "Premier League",
    "La Liga",
    "Bundesliga",
    "Serie A",
    "Ligue 1",
    "UEFA Champions League",
    "MLS",
    "USL Championship",
    "USL League One Cup",
]

HOT_BASEBALL = [
    "MLB",
    "NPB",
    "KBO",
    "PCL",
    "LMB",
]

HOT_BASKETBALL = [
    "NBA",
    "WNBA",
]

def is_hot_league(league_name, hot_list):
    return league_name in hot_list

def sort_football_matches(matches):
    def key(match):
        league_name = match.get("league", {}).get("name", "")
        elapsed = match.get("fixture", {}).get("status", {}).get("elapsed") or 0
        hot_rank = 0 if is_hot_league(league_name, HOT_FOOTBALL) else 1
        return (hot_rank, -elapsed)

    return sorted(matches, key=key)

def sort_baseball_games(games):
    def inning_value(game):
        status_text = str(game.get("status", {}).get("long", "") or game.get("status", {}).get("short", ""))
        match = re.search(r"(\d+)", status_text)
        return int(match.group(1)) if match else 0

    def key(game):
        league_name = game.get("league", {}).get("name", "")
        hot_rank = 0 if is_hot_league(league_name, HOT_BASEBALL) else 1
        return (hot_rank, -inning_value(game))

    return sorted(games, key=key)

def sort_basketball_games(games):
    def key(game):
        league_name = game.get("league", {}).get("name", "")
        status_text = str(game.get("status", {}).get("long", "") or game.get("status", {}).get("short", ""))
        hot_rank = 0 if is_hot_league(league_name, HOT_BASKETBALL) else 1

        quarter = 0
        for n in [4, 3, 2, 1]:
            if str(n) in status_text:
                quarter = n
                break

        return (hot_rank, -quarter)

    return sorted(games, key=key)




def get_live_star_text(rate):
    if rate >= 85:
        return "★★★★★", "低風險"
    elif rate >= 75:
        return "★★★★☆", "中低風險"
    elif rate >= 65:
        return "★★★☆☆", "中風險"
    elif rate >= 55:
        return "★★☆☆☆", "中高風險"
    return "★☆☆☆☆", "高風險"

def estimate_live_win_rate(home_score, away_score, status, sport_icon):
    try:
        hs = int(home_score)
        aw = int(away_score)
    except:
        hs = 0
        aw = 0

    diff = abs(hs - aw)

    if hs == aw:
        return 50, 50, "雙方平手"

    # 基礎分差勝率
    if sport_icon == "baseball":
        base = 50 + diff * 6
    elif sport_icon == "football":
        base = 50 + diff * 12
    elif sport_icon == "basketball":
        base = 50 + diff * 2
    else:
        base = 50 + diff * 5

    base = min(base, 95)

    if hs > aw:
        return base, 100 - base, "主隊"
    else:
        return 100 - base, base, "客隊"

def generate_live_ai_analysis(
    home,
    away,
    home_score,
    away_score,
    status,
    sport_icon
):
    try:
        hs = int(home_score)
        aw = int(away_score)
    except:
        hs = 0
        aw = 0

    home_rate, away_rate, leader_side = estimate_live_win_rate(
        home_score,
        away_score,
        status,
        sport_icon
    )

    if home_rate > away_rate:
        leader = home
        best_rate = home_rate
        trailing = away
        recommendation = f"{home} 方向"
    elif away_rate > home_rate:
        leader = away
        best_rate = away_rate
        trailing = home
        recommendation = f"{away} 方向"
    else:
        leader = "雙方平手"
        best_rate = 50
        trailing = "雙方"
        recommendation = "暫不重壓，等待下一波局勢"

    diff = abs(hs - aw)
    stars, risk = get_live_star_text(best_rate)

    sport_name = {
        "football": "足球",
        "baseball": "棒球",
        "basketball": "籃球"
    }.get(sport_icon, "賽事")

    if sport_icon == "baseball":
        if diff >= 5:
            read = "分差已經明顯拉開，領先方目前勝勢較強。"
            advice = "可偏向領先方，但仍要注意後段牛棚與失誤。"
        elif diff >= 2:
            read = "領先方有一定優勢，但棒球後段仍可能有大局。"
            advice = "領先方方向較佳，建議保守看待。"
        elif diff == 1:
            read = "目前只有一分差，勝負仍高度開放。"
            advice = "不建議過早重壓，觀察下一局攻守。"
        else:
            read = "目前平手，雙方仍在拉鋸。"
            advice = "等待得分或投手更換後再判斷。"

    elif sport_icon == "football":
        if diff >= 3:
            read = "分差已經很大，落後方追回難度偏高。"
            advice = "領先方不敗方向較佳，讓球盤需注意是否過深。"
        elif diff >= 1:
            read = "領先方目前掌握優勢，但仍需注意最後階段變化。"
            advice = "領先方不敗方向，保守看待。"
        else:
            read = "目前平手，下一球會大幅影響盤勢。"
            advice = "觀察控球、射門與紅黃牌狀況。"

    elif sport_icon == "basketball":
        if diff >= 12:
            read = "分差明顯，領先方節奏掌握度較高。"
            advice = "領先方方向較佳，但仍需注意垃圾時間。"
        elif diff >= 6:
            read = "領先方有優勢，但籃球追分速度快。"
            advice = "領先方方向，但需注意末節追分。"
        elif diff >= 1:
            read = "分差很小，比賽仍然接近。"
            advice = "建議等待下一節或關鍵回合。"
        else:
            read = "目前平手，雙方勝負接近五五波。"
            advice = "觀察犯規、命中率與節奏。"
    else:
        read = "目前依照比分做基礎判斷。"
        advice = "建議搭配下方模型參數再判斷。"

    return {
        "sport_name": sport_name,
        "home_rate": home_rate,
        "away_rate": away_rate,
        "leader": leader,
        "trailing": trailing,
        "best_rate": best_rate,
        "diff": diff,
        "stars": stars,
        "risk": risk,
        "read": read,
        "advice": advice,
        "recommendation": recommendation,
    }



live_recommendations = []

def add_live_recommendation(
    sport_name,
    league_name,
    country,
    home,
    away,
    home_score,
    away_score,
    status,
    sport_icon
):
    home_zh = zh_team(home)
    away_zh = zh_team(away)

    analysis = generate_live_ai_analysis(
        home_zh,
        away_zh,
        home_score,
        away_score,
        zh_status(status),
        sport_icon
    )

    if analysis["home_rate"] >= analysis["away_rate"]:
        pick = home_zh
        confidence = analysis["home_rate"]
    else:
        pick = away_zh
        confidence = analysis["away_rate"]

    live_recommendations.append({
        "sport": sport_name,
        "league": zh_league(league_name),
        "country": zh_country(country),
        "match": f"{home_zh} vs {away_zh}",
        "pick": pick,
        "confidence": confidence,
        "stars": analysis["stars"],
        "risk": analysis["risk"],
        "score": f"{home_score}:{away_score}",
        "status": zh_status(status),
        "advice": analysis["advice"],
    })

def render_ai_dashboard():
    if not live_recommendations:
        st.info("目前尚未載入即時賽事，請稍候或確認 API 是否有進行中的比賽。")
        return

    football_count = sum(1 for r in live_recommendations if r["sport"] == "足球")
    baseball_count = sum(1 for r in live_recommendations if r["sport"] == "棒球")
    basketball_count = sum(1 for r in live_recommendations if r["sport"] == "籃球")
    high_confidence_count = sum(1 for r in live_recommendations if r["confidence"] >= 75)

    st.subheader("📊 今日AI儀表板")

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("足球賽事", football_count)
    d2.metric("棒球賽事", baseball_count)
    d3.metric("籃球賽事", basketball_count)
    d4.metric("高信心", high_confidence_count)

    st.subheader("🏆 AI推薦排行榜 TOP 10")

    ranked = sorted(
        live_recommendations,
        key=lambda x: x["confidence"],
        reverse=True
    )[:10]

    for i, item in enumerate(ranked, 1):
        hot_tag = "🔥熱門" if item["league"] in [
            "美國職棒大聯盟",
            "美國職籃",
            "英格蘭超級聯賽",
            "西班牙甲級聯賽",
            "歐洲冠軍聯賽",
            "美國職業足球大聯盟",
        ] else ""

        st.success(
            f"{i}. {hot_tag} {item['pick']}｜{item['stars']}｜{item['confidence']:.1f}%｜{item['sport']}｜{item['match']}｜比分 {item['score']}｜{item['status']}"
        )

    st.subheader("🏅 分運動推薦")

    rtab1, rtab2, rtab3 = st.tabs(["⚽ 足球推薦", "⚾ 棒球推薦", "🏀 籃球推薦"])

    def render_sport_rank(sport_name):
        items = [
            r for r in live_recommendations
            if r["sport"] == sport_name
        ]

        items = sorted(
            items,
            key=lambda x: x["confidence"],
            reverse=True
        )[:5]

        if not items:
            st.info("目前沒有推薦。")
            return

        for i, item in enumerate(items, 1):
            st.write(
                f"{i}. **{item['pick']}**｜{item['stars']}｜{item['confidence']:.1f}%｜{item['match']}｜比分 {item['score']}｜{item['status']}"
            )

    with rtab1:
        render_sport_rank("足球")

    with rtab2:
        render_sport_rank("棒球")

    with rtab3:
        render_sport_rank("籃球")

    st.subheader("🔥 今日熱門賽事")

    hot_items = ranked[:5]

    for item in hot_items:
        st.info(
            f"""
{item['sport']}｜{item['country']}：{item['league']}

{item['match']}

目前比分：{item['score']}

推薦方向：{item['pick']}

信心：{item['confidence']:.1f}%｜{item['stars']}

風險：{item['risk']}
"""
        )


def set_ai_match(home, away, sport_icon, home_score, away_score, status):
    st.session_state["selected_home_team"] = home
    st.session_state["selected_away_team"] = away
    st.session_state["selected_home_score"] = home_score
    st.session_state["selected_away_score"] = away_score
    st.session_state["selected_status"] = status
    st.session_state["selected_match"] = f"{zh_team(home)} vs {zh_team(away)}"
    st.session_state["selected_sport"] = sport_icon


def render_selected_ai_panel():
    if "selected_match" not in st.session_state:
        return

    home = st.session_state.get("selected_home_team", "")
    away = st.session_state.get("selected_away_team", "")
    home_score = st.session_state.get("selected_home_score", 0)
    away_score = st.session_state.get("selected_away_score", 0)
    status = st.session_state.get("selected_status", "")

    try:
        hs = int(home_score)
        aw = int(away_score)
    except:
        hs = 0
        aw = 0

    if hs > aw:
        leader = zh_team(home)
        situation = "主隊目前領先"
    elif aw > hs:
        leader = zh_team(away)
        situation = "客隊目前領先"
    else:
        leader = "雙方平手"
        situation = "目前平手"

    with ai_panel_placeholder.container():
        st.success(f"🎯 固定 AI 分析賽事：{st.session_state['selected_match']}")

        sport_icon = st.session_state.get("selected_sport", "")

        analysis = generate_live_ai_analysis(
            zh_team(home),
            zh_team(away),
            home_score,
            away_score,
            zh_status(status),
            sport_icon
        )

        st.markdown("### 🎯 AI 即時分析")

        m1, m2, m3 = st.columns(3)

        with m1:
            st.metric("主隊即時勝率", f"{analysis['home_rate']:.1f}%")

        with m2:
            st.metric("客隊即時勝率", f"{analysis['away_rate']:.1f}%")

        with m3:
            st.metric("信心星等", analysis["stars"])

        st.success(f"✅ 推薦方向：{analysis['recommendation']}")

        st.info(
            f"""
比賽類型：{analysis['sport_name']}

即時比分：{zh_team(home)} {home_score} : {away_score} {zh_team(away)}

比賽狀態：{zh_status(status)}

目前分差：{analysis['diff']}

AI判讀：{analysis['read']}

風險等級：{analysis['risk']}

建議：{analysis['advice']}

提醒：此分析只根據即時比分與目前狀態做模擬判斷，正式預測請再搭配下方模型參數。
"""
        )

        if st.button("清除固定分析", key="clear_selected_match_top"):
            for k in [
                "selected_home_team",
                "selected_away_team",
                "selected_home_score",
                "selected_away_score",
                "selected_status",
                "selected_match",
                "selected_sport",
            ]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()


def ai_analysis_button(home, away, sport_icon, home_score=0, away_score=0, status=""):
    safe_home = str(home).replace(" ", "_").replace("/", "_").replace("-", "_")
    safe_away = str(away).replace(" ", "_").replace("/", "_").replace("-", "_")
    key = f"ai_btn_{sport_icon}_{safe_home}_{safe_away}_{home_score}_{away_score}"

    st.button(
        f"🎯 AI分析：{zh_team(home)} vs {zh_team(away)}",
        key=key,
        on_click=set_ai_match,
        args=(home, away, sport_icon, home_score, away_score, status)
    )

    if (
        st.session_state.get("selected_home_team") == home
        and st.session_state.get("selected_away_team") == away
    ):
        st.success(f"✅ 已固定分析：{zh_team(home)} vs {zh_team(away)}")



def is_baseball_game_live(game):
    status = game.get("status", {})
    status_long = str(status.get("long", "") or "")
    status_short = str(status.get("short", "") or "")

    text = f"{status_long} {status_short}".lower()

    live_keywords = [
        "inning",
        "live",
        "playing",
        "in progress",
        "top",
        "bottom",
        "delayed"
    ]

    finished_keywords = [
        "finished",
        "after",
        "cancelled",
        "postponed",
        "not started",
        "scheduled"
    ]

    if any(k in text for k in finished_keywords):
        return False

    return any(k in text for k in live_keywords)


def get_baseball_games_safely():
    games = []

    try:
        live_data = api_sports.get_live_baseball()
        games = live_data.get("response", [])
    except Exception:
        games = []

    # API-Sports 棒球 live=all 有時會回空，所以再抓今日賽程做備援
    if len(games) == 0:
        try:
            today_data = api_sports.get_today_baseball()
            all_games = today_data.get("response", [])
            games = [g for g in all_games if is_baseball_game_live(g)]
        except Exception:
            games = []

    return games




def status_text_lower(item):
    status = item.get("status", {}) or item.get("fixture", {}).get("status", {})
    long_text = str(status.get("long", "") or "")
    short_text = str(status.get("short", "") or "")
    elapsed = str(status.get("elapsed", "") or "")
    return f"{long_text} {short_text} {elapsed}".lower()

def is_finished_status(item):
    text = status_text_lower(item)
    return any(k in text for k in [
        "finished", "after", "match finished", "full time",
        "ft", "aet", "pen", "cancelled", "canceled"
    ])

def is_upcoming_status(item):
    text = status_text_lower(item)
    return any(k in text for k in [
        "not started", "scheduled", "ns", "tbd"
    ])

def is_live_status(item):
    text = status_text_lower(item)

    if is_finished_status(item) or is_upcoming_status(item):
        return False

    # 有 elapsed 分鐘也算進行中
    status = item.get("status", {}) or item.get("fixture", {}).get("status", {})
    if status.get("elapsed"):
        return True

    return any(k in text for k in [
        "live", "in progress", "playing", "inning", "top", "bottom",
        "first half", "second half", "halftime", "quarter", "period"
    ])

def split_games_by_status(items):
    finished = []
    live = []
    upcoming = []

    for item in items:
        if is_finished_status(item):
            finished.append(item)
        elif is_upcoming_status(item):
            upcoming.append(item)
        else:
            live.append(item)

    return finished, live, upcoming

def unique_items(items):
    unique = []
    seen = set()

    for item in items:
        home = item.get("teams", {}).get("home", {}).get("name", "")
        away = item.get("teams", {}).get("away", {}).get("name", "")
        league = item.get("league", {}).get("name", "")
        game_id = (
            item.get("id")
            or item.get("fixture", {}).get("id")
            or item.get("game", {}).get("id")
            or f"{league}-{home}-{away}-{item.get('_query_date', '')}"
        )

        if game_id not in seen:
            seen.add(game_id)
            unique.append(item)

    return unique

def date_range_strings():
    return [
        datetime.now().strftime("%Y-%m-%d"),
        (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
    ]

def get_football_games_safely():
    items = []

    try:
        live_data = api_sports.get_live_football()
        items.extend(live_data.get("response", []))
    except Exception:
        pass

    for date_str in date_range_strings():
        try:
            if hasattr(api_sports, "get_football_by_date"):
                data = api_sports.get_football_by_date(date_str)
                games = data.get("response", [])
                for g in games:
                    g["_query_date"] = date_str
                items.extend(games)
        except Exception:
            continue

    return unique_items(items)

def get_baseball_games_safely():
    items = []

    try:
        live_data = api_sports.get_live_baseball()
        items.extend(live_data.get("response", []))
    except Exception:
        pass

    for date_str in date_range_strings():
        try:
            if hasattr(api_sports, "get_baseball_by_date"):
                data = api_sports.get_baseball_by_date(date_str)
            else:
                data = api_sports.get_today_baseball()

            games = data.get("response", [])
            for g in games:
                g["_query_date"] = date_str
            items.extend(games)
        except Exception:
            continue

    return unique_items(items)

def get_basketball_games_safely():
    items = []

    try:
        live_data = api_sports.get_live_basketball()
        items.extend(live_data.get("response", []))
    except Exception:
        pass

    for date_str in date_range_strings():
        try:
            if hasattr(api_sports, "get_basketball_by_date"):
                data = api_sports.get_basketball_by_date(date_str)
                games = data.get("response", [])
                for g in games:
                    g["_query_date"] = date_str
                items.extend(games)
        except Exception:
            continue

    return unique_items(items)

def render_section(title, items, render_func, expanded=False):
    with st.expander(title, expanded=expanded):
        if len(items) == 0:
            st.info("目前沒有資料。")
        else:
            for item in items:
                render_func(item)





def make_demo_baseball_games():
    return [
        # 進行中
        {"league": {"name": "MLB"}, "country": {"name": "USA"}, "teams": {"home": {"name": "Los Angeles Dodgers"}, "away": {"name": "Los Angeles Angels"}}, "scores": {"home": {"total": 2}, "away": {"total": 1}}, "status": {"long": "Inning 3"}, "_demo": True},
        {"league": {"name": "MLB"}, "country": {"name": "USA"}, "teams": {"home": {"name": "Houston Astros"}, "away": {"name": "Seattle Mariners"}}, "scores": {"home": {"total": 4}, "away": {"total": 3}}, "status": {"long": "Inning 5"}, "_demo": True},
        {"league": {"name": "MLB"}, "country": {"name": "USA"}, "teams": {"home": {"name": "Chicago Cubs"}, "away": {"name": "San Francisco Giants"}}, "scores": {"home": {"total": 1}, "away": {"total": 1}}, "status": {"long": "Inning 6"}, "_demo": True},
        {"league": {"name": "MLB"}, "country": {"name": "USA"}, "teams": {"home": {"name": "Philadelphia Phillies"}, "away": {"name": "Atlanta Braves"}}, "scores": {"home": {"total": 6}, "away": {"total": 2}}, "status": {"long": "Inning 7"}, "_demo": True},
        {"league": {"name": "PCL"}, "country": {"name": "USA"}, "teams": {"home": {"name": "Las Vegas Aviators"}, "away": {"name": "Reno Aces"}}, "scores": {"home": {"total": 3}, "away": {"total": 5}}, "status": {"long": "Inning 4"}, "_demo": True},

        # 即將開賽
        {"league": {"name": "MLB"}, "country": {"name": "USA"}, "teams": {"home": {"name": "New York Yankees"}, "away": {"name": "Boston Red Sox"}}, "scores": {"home": {"total": 0}, "away": {"total": 0}}, "status": {"long": "Not Started"}, "_demo": True},
        {"league": {"name": "MLB"}, "country": {"name": "USA"}, "teams": {"home": {"name": "Toronto Blue Jays"}, "away": {"name": "Baltimore Orioles"}}, "scores": {"home": {"total": 0}, "away": {"total": 0}}, "status": {"long": "Not Started"}, "_demo": True},
        {"league": {"name": "MLB"}, "country": {"name": "USA"}, "teams": {"home": {"name": "Arizona Diamondbacks"}, "away": {"name": "Cincinnati Reds"}}, "scores": {"home": {"total": 0}, "away": {"total": 0}}, "status": {"long": "Scheduled"}, "_demo": True},

        # 已結束
        {"league": {"name": "PCL"}, "country": {"name": "USA"}, "teams": {"home": {"name": "Sacramento River Cats"}, "away": {"name": "Tacoma Rainiers"}}, "scores": {"home": {"total": 5}, "away": {"total": 2}}, "status": {"long": "Finished"}, "_demo": True},
        {"league": {"name": "MLB"}, "country": {"name": "USA"}, "teams": {"home": {"name": "Minnesota Twins"}, "away": {"name": "Tampa Bay Rays"}}, "scores": {"home": {"total": 7}, "away": {"total": 4}}, "status": {"long": "Finished"}, "_demo": True},
        {"league": {"name": "MLB"}, "country": {"name": "USA"}, "teams": {"home": {"name": "Washington Nationals"}, "away": {"name": "Miami Marlins"}}, "scores": {"home": {"total": 3}, "away": {"total": 6}}, "status": {"long": "Finished"}, "_demo": True},
    ]

def make_demo_football_matches():
    return [
        # 進行中
        {"league": {"name": "MLS", "country": "USA"}, "teams": {"home": {"name": "Inter Miami"}, "away": {"name": "Los Angeles FC"}}, "goals": {"home": 2, "away": 2}, "fixture": {"status": {"long": "First Half", "elapsed": 32}}, "_demo": True},
        {"league": {"name": "USL League One Cup", "country": "USA"}, "teams": {"home": {"name": "New Mexico United"}, "away": {"name": "Phoenix Rising"}}, "goals": {"home": 1, "away": 0}, "fixture": {"status": {"long": "Second Half", "elapsed": 68}}, "_demo": True},
        {"league": {"name": "Premier League", "country": "England"}, "teams": {"home": {"name": "Manchester City"}, "away": {"name": "Arsenal"}}, "goals": {"home": 1, "away": 1}, "fixture": {"status": {"long": "Second Half", "elapsed": 75}}, "_demo": True},
        {"league": {"name": "La Liga", "country": "Spain"}, "teams": {"home": {"name": "Real Madrid"}, "away": {"name": "Barcelona"}}, "goals": {"home": 0, "away": 1}, "fixture": {"status": {"long": "First Half", "elapsed": 28}}, "_demo": True},

        # 即將開賽
        {"league": {"name": "Bundesliga", "country": "Germany"}, "teams": {"home": {"name": "Bayern Munich"}, "away": {"name": "Chelsea"}}, "goals": {"home": 0, "away": 0}, "fixture": {"status": {"long": "Not Started", "elapsed": None}}, "_demo": True},
        {"league": {"name": "Ligue 1", "country": "France"}, "teams": {"home": {"name": "Paris Saint Germain"}, "away": {"name": "Liverpool"}}, "goals": {"home": 0, "away": 0}, "fixture": {"status": {"long": "Scheduled", "elapsed": None}}, "_demo": True},
        {"league": {"name": "MLS Next Pro", "country": "USA"}, "teams": {"home": {"name": "Portland Timbers II"}, "away": {"name": "LA Galaxy II"}}, "goals": {"home": 0, "away": 0}, "fixture": {"status": {"long": "Not Started", "elapsed": None}}, "_demo": True},

        # 已結束
        {"league": {"name": "MLS", "country": "USA"}, "teams": {"home": {"name": "LA Galaxy II"}, "away": {"name": "Portland Timbers II"}}, "goals": {"home": 3, "away": 1}, "fixture": {"status": {"long": "Match Finished", "elapsed": 90}}, "_demo": True},
        {"league": {"name": "Saudi Pro League", "country": "Saudi Arabia"}, "teams": {"home": {"name": "Al Nassr"}, "away": {"name": "Al Hilal"}}, "goals": {"home": 2, "away": 4}, "fixture": {"status": {"long": "Match Finished", "elapsed": 90}}, "_demo": True},
    ]

def make_demo_basketball_games():
    return [
        # 進行中
        {"league": {"name": "NBA"}, "country": {"name": "USA"}, "teams": {"home": {"name": "Los Angeles Lakers"}, "away": {"name": "Golden State Warriors"}}, "scores": {"home": {"total": 88}, "away": {"total": 84}}, "status": {"long": "Quarter 4"}, "_demo": True},
        {"league": {"name": "NBA"}, "country": {"name": "USA"}, "teams": {"home": {"name": "Boston Celtics"}, "away": {"name": "Miami Heat"}}, "scores": {"home": {"total": 101}, "away": {"total": 96}}, "status": {"long": "Quarter 4"}, "_demo": True},
        {"league": {"name": "NBA"}, "country": {"name": "USA"}, "teams": {"home": {"name": "Dallas Mavericks"}, "away": {"name": "Denver Nuggets"}}, "scores": {"home": {"total": 64}, "away": {"total": 70}}, "status": {"long": "Quarter 3"}, "_demo": True},

        # 即將開賽
        {"league": {"name": "NBA"}, "country": {"name": "USA"}, "teams": {"home": {"name": "Phoenix Suns"}, "away": {"name": "Los Angeles Lakers"}}, "scores": {"home": {"total": 0}, "away": {"total": 0}}, "status": {"long": "Not Started"}, "_demo": True},
        {"league": {"name": "NBA"}, "country": {"name": "USA"}, "teams": {"home": {"name": "New York Knicks"}, "away": {"name": "Chicago Bulls"}}, "scores": {"home": {"total": 0}, "away": {"total": 0}}, "status": {"long": "Scheduled"}, "_demo": True},

        # 已結束
        {"league": {"name": "NBA"}, "country": {"name": "USA"}, "teams": {"home": {"name": "Milwaukee Bucks"}, "away": {"name": "Minnesota Timberwolves"}}, "scores": {"home": {"total": 112}, "away": {"total": 104}}, "status": {"long": "Finished"}, "_demo": True},
        {"league": {"name": "NBA"}, "country": {"name": "USA"}, "teams": {"home": {"name": "Houston Rockets"}, "away": {"name": "Phoenix Suns"}}, "scores": {"home": {"total": 98}, "away": {"total": 106}}, "status": {"long": "Finished"}, "_demo": True},
    ]

def add_demo_if_empty(items, demo_items, min_count=8):
    if len(items) == 0:
        return demo_items, True

    if len(items) < min_count:
        existing_keys = set()
        for item in items:
            home = item.get("teams", {}).get("home", {}).get("name", "")
            away = item.get("teams", {}).get("away", {}).get("name", "")
            existing_keys.add(f"{home}-{away}")

        filled = list(items)

        for demo in demo_items:
            home = demo.get("teams", {}).get("home", {}).get("name", "")
            away = demo.get("teams", {}).get("away", {}).get("name", "")
            key = f"{home}-{away}"

            if key not in existing_keys:
                filled.append(demo)
                existing_keys.add(key)

            if len(filled) >= min_count:
                break

        return filled, True

    return items, False


def fill_each_section(finished, live, upcoming, demo_items, min_finished=2, min_live=4, min_upcoming=2):
    demo_finished, demo_live, demo_upcoming = split_games_by_status(demo_items)

    def add_missing(target, source, minimum):
        existing = set()
        for item in target:
            home = item.get("teams", {}).get("home", {}).get("name", "")
            away = item.get("teams", {}).get("away", {}).get("name", "")
            existing.add(f"{home}-{away}")

        result = list(target)

        for item in source:
            home = item.get("teams", {}).get("home", {}).get("name", "")
            away = item.get("teams", {}).get("away", {}).get("name", "")
            key = f"{home}-{away}"

            if key not in existing:
                result.append(item)
                existing.add(key)

            if len(result) >= minimum:
                break

        return result

    finished = add_missing(finished, demo_finished, min_finished)
    live = add_missing(live, demo_live, min_live)
    upcoming = add_missing(upcoming, demo_upcoming, min_upcoming)

    return finished, live, upcoming


def translate_baseball_status(status_text):
    text = str(status_text or "")

    for i in range(1, 20):
        text = text.replace(f"Inning {i}", f"第{i}局")

    replacements = {
        "Top": "上半局",
        "Bottom": "下半局",
        "Live": "進行中",
        "In Progress": "進行中",
        "Playing": "進行中",
        "Not Started": "未開始",
        "Finished": "已結束",
        "Postponed": "延賽",
        "Delayed": "延遲",
        "Not Started": "尚未開始",
        "Scheduled": "即將開賽"
    }

    for en, zh in replacements.items():
        text = text.replace(en, zh)

    return text


def normalize_search_text(text):
    return str(text or "").strip().lower()

def should_show_item(sport_name, league_name, country, home, away):
    keyword = normalize_search_text(team_search)

    if hot_only:
        if sport_name == "足球" and not is_hot_league(league_name, HOT_FOOTBALL):
            return False
        if sport_name == "棒球" and not is_hot_league(league_name, HOT_BASEBALL):
            return False
        if sport_name == "籃球" and not is_hot_league(league_name, HOT_BASKETBALL):
            return False

    if not keyword:
        return True

    search_pool = " ".join([
        str(league_name),
        str(country),
        str(home),
        str(away),
        zh_league(league_name),
        zh_country(country),
        zh_team(home),
        zh_team(away),
    ]).lower()

    return keyword in search_pool

def match_key(home, away):
    return f"{zh_team(home)} vs {zh_team(away)}"

def toggle_favorite(home, away):
    key = match_key(home, away)

    if key in st.session_state["favorite_matches"]:
        st.session_state["favorite_matches"].remove(key)
    else:
        st.session_state["favorite_matches"].append(key)

def is_favorite(home, away):
    return match_key(home, away) in st.session_state["favorite_matches"]

def score_change_text(home, away, home_score, away_score):
    key = match_key(home, away)
    current = f"{home_score}:{away_score}"
    previous = st.session_state["previous_scores"].get(key)

    st.session_state["previous_scores"][key] = current

    if previous and previous != current:
        return f"⚡ 比分變動：{previous} → {current}"

    return ""

def render_favorite_button(home, away, sport_icon):
    fav = is_favorite(home, away)
    label = "⭐ 已收藏" if fav else "☆ 收藏"
    safe_home = str(home).replace(" ", "_").replace("/", "_").replace("-", "_")
    safe_away = str(away).replace(" ", "_").replace("/", "_").replace("-", "_")

    st.button(
        label,
        key=f"fav_{sport_icon}_{safe_home}_{safe_away}",
        on_click=toggle_favorite,
        args=(home, away)
    )

def render_favorites_panel():
    favorites = st.session_state.get("favorite_matches", [])

    if not favorites:
        return

    st.subheader("⭐ 我的收藏賽事")

    for item in favorites:
        st.info(item)

def filter_items(items, sport_name, get_fields_func):
    result = []

    for item in items:
        league_name, country, home, away = get_fields_func(item)

        if should_show_item(sport_name, league_name, country, home, away):
            result.append(item)

    return result

def add_demo_if_needed(items, demo_items, min_count=8):
    if not allow_demo_data:
        return items, False

    return add_demo_if_empty(items, demo_items, min_count=min_count)


def render_score_card(
    league_name,
    country,
    home,
    away,
    home_score,
    away_score,
    status,
    sport_icon
):
    if home_score is None:
        home_score = 0

    if away_score is None:
        away_score = 0

    html = f"""
    <div style="
        background:#0f172a;
        color:white;
        border-radius:18px;
        padding:18px;
        margin-bottom:12px;
        border:1px solid #1e293b;
        font-family:Arial, sans-serif;
        max-width:760px;
    ">

        <div style="
            color:#60a5fa;
            font-weight:700;
            font-size:15px;
            margin-bottom:14px;
        ">
            {sport_icon} {zh_country(country) or ""}：{zh_league(league_name) or ""}
        </div>

        <table style="
            width:100%;
            border-collapse:collapse;
            table-layout:fixed;
        ">
            <tr>
                <td style="
                    color:white;
                    font-size:22px;
                    font-weight:800;
                    padding:5px 0;
                    width:80%;
                    white-space:nowrap;
                    overflow:hidden;
                    text-overflow:ellipsis;
                ">
                    {zh_team(home)}
                </td>
                <td style="
                    color:#ef4444;
                    font-size:30px;
                    font-weight:900;
                    text-align:right;
                    width:20%;
                    padding:5px 0;
                ">
                    {home_score}
                </td>
            </tr>

            <tr>
                <td style="
                    color:white;
                    font-size:22px;
                    font-weight:800;
                    padding:5px 0;
                    width:80%;
                    white-space:nowrap;
                    overflow:hidden;
                    text-overflow:ellipsis;
                ">
                    {zh_team(away)}
                </td>
                <td style="
                    color:#ef4444;
                    font-size:30px;
                    font-weight:900;
                    text-align:right;
                    width:20%;
                    padding:5px 0;
                ">
                    {away_score}
                </td>
            </tr>
        </table>

        <div style="
            margin-top:14px;
            color:#f87171;
            font-size:15px;
            font-weight:700;
        ">
            ⏱ {zh_status(status)}
        </div>

    </div>
    """

    card_height = 190 if compact_mobile else 220

    components.html(
        html,
        height=card_height,
        scrolling=False
    )



def get_score_total(score):
    if isinstance(score, dict):
        for key in ["total", "score", "points"]:
            value = score.get(key)
            if value is not None:
                return value
        return 0

    return score if score is not None else 0


render_selected_ai_panel()

if show_debug:
    with st.expander("AI狀態檢查", expanded=False):
        st.write({
            "selected_match": st.session_state.get("selected_match"),
            "selected_home_team": st.session_state.get("selected_home_team"),
            "selected_away_team": st.session_state.get("selected_away_team"),
            "favorites": st.session_state.get("favorite_matches", []),
            "previous_scores": st.session_state.get("previous_scores", {}),
        })

render_favorites_panel()

sport_tab1, sport_tab2, sport_tab3 = st.tabs(
    ["⚽ 足球", "⚾ 棒球", "🏀 籃球"]
)

with sport_tab1:
    st.caption("已自動載入足球比分")

    try:
        matches = get_football_games_safely()
        matches, used_demo = add_demo_if_needed(matches, make_demo_football_matches(), min_count=6)
        matches = filter_items(
            matches,
            "足球",
            lambda m: (
                m.get("league", {}).get("name", ""),
                m.get("league", {}).get("country", ""),
                m.get("teams", {}).get("home", {}).get("name", ""),
                m.get("teams", {}).get("away", {}).get("name", ""),
            )
        )

        matches = sort_football_matches(matches)

        if used_demo:
            st.warning("官方足球 API 回傳資料較少，已自動補充示範賽事。")

        finished_matches, live_matches, upcoming_matches = split_games_by_status(matches)
        if allow_demo_data:
            finished_matches, live_matches, upcoming_matches = fill_each_section(
                finished_matches,
                live_matches,
                upcoming_matches,
                make_demo_football_matches(),
                min_finished=2,
                min_live=4,
                min_upcoming=3
            )

        def render_football_match(match):
            league_name = match.get("league", {}).get("name", "")
            country = match.get("league", {}).get("country", "")
            home = match.get("teams", {}).get("home", {}).get("name", "")
            away = match.get("teams", {}).get("away", {}).get("name", "")
            home_score = match.get("goals", {}).get("home", 0)
            away_score = match.get("goals", {}).get("away", 0)
            minute = match.get("fixture", {}).get("status", {}).get("elapsed", "")
            status = match.get("fixture", {}).get("status", {}).get("long", "")

            if minute:
                status_text = f"{minute}' {status}"
            else:
                status_text = status

            if match.get("_demo"):
                status_text = f"{status_text}｜示範資料"

            render_score_card(
                league_name,
                country,
                home,
                away,
                home_score,
                away_score,
                status_text,
                "⚽"
            )

            add_live_recommendation(
                "足球",
                league_name,
                country,
                home,
                away,
                home_score,
                away_score,
                status_text,
                "football"
            )

            change_msg = score_change_text(home, away, home_score, away_score)
            if change_msg:
                st.warning(change_msg)

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                ai_analysis_button(home, away, "football", home_score, away_score, status_text)
            with btn_col2:
                render_favorite_button(home, away, "football")

        st.caption(
            f"足球：進行中 {len(live_matches)} 場｜已結束 {len(finished_matches)} 場｜即將開賽 {len(upcoming_matches)} 場"
        )

        render_section("顯示已結束", finished_matches, render_football_match, expanded=False)
        render_section("進行中", live_matches, render_football_match, expanded=True)
        render_section("顯示即將開賽", upcoming_matches, render_football_match, expanded=False)

    except Exception as e:
        st.error(f"足球比分讀取失敗：{e}")


with sport_tab2:
    st.caption("已自動載入棒球比分")

    try:
        games = get_baseball_games_safely()
        games, used_demo = add_demo_if_needed(games, make_demo_baseball_games(), min_count=12)
        games = filter_items(
            games,
            "棒球",
            lambda g: (
                g.get("league", {}).get("name", ""),
                g.get("country", {}).get("name", ""),
                g.get("teams", {}).get("home", {}).get("name", ""),
                g.get("teams", {}).get("away", {}).get("name", ""),
            )
        )

        games = sort_baseball_games(games)

        if used_demo:
            st.warning("官方棒球 API 回傳資料較少，已自動補充示範賽事。")

        finished_games, live_games, upcoming_games = split_games_by_status(games)
        if allow_demo_data:
            finished_games, live_games, upcoming_games = fill_each_section(
                finished_games,
                live_games,
                upcoming_games,
                make_demo_baseball_games(),
                min_finished=3,
                min_live=5,
                min_upcoming=3
            )

        def render_baseball_game(game):
            league_name = game.get("league", {}).get("name", "")
            country = game.get("country", {}).get("name", "")
            home = game.get("teams", {}).get("home", {}).get("name", "")
            away = game.get("teams", {}).get("away", {}).get("name", "")
            home_score = get_score_total(game.get("scores", {}).get("home", {}))
            away_score = get_score_total(game.get("scores", {}).get("away", {}))

            status = game.get("status", {})
            status_text = status.get("long", "") or status.get("short", "")
            status_text = translate_baseball_status(status_text)
            if game.get("_demo"):
                status_text = f"{status_text}｜示範資料"

            render_score_card(
                league_name,
                country,
                home,
                away,
                home_score,
                away_score,
                status_text,
                "⚾"
            )

            add_live_recommendation(
                "棒球",
                league_name,
                country,
                home,
                away,
                home_score,
                away_score,
                status_text,
                "baseball"
            )

            change_msg = score_change_text(home, away, home_score, away_score)
            if change_msg:
                st.warning(change_msg)

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                ai_analysis_button(home, away, "baseball", home_score, away_score, status_text)
            with btn_col2:
                render_favorite_button(home, away, "baseball")

        st.caption(
            f"棒球：進行中 {len(live_games)} 場｜已結束 {len(finished_games)} 場｜即將開賽 {len(upcoming_games)} 場"
        )

        render_section("顯示已結束", finished_games, render_baseball_game, expanded=False)
        render_section("進行中", live_games, render_baseball_game, expanded=True)
        render_section("顯示即將開賽", upcoming_games, render_baseball_game, expanded=True)

    except Exception as e:
        st.error(f"棒球比分讀取失敗：{e}")


with sport_tab3:
    st.caption("已自動載入籃球比分")

    try:
        games = get_basketball_games_safely()
        games, used_demo = add_demo_if_needed(games, make_demo_basketball_games(), min_count=6)
        games = filter_items(
            games,
            "籃球",
            lambda g: (
                g.get("league", {}).get("name", ""),
                g.get("country", {}).get("name", ""),
                g.get("teams", {}).get("home", {}).get("name", ""),
                g.get("teams", {}).get("away", {}).get("name", ""),
            )
        )

        games = sort_basketball_games(games)

        if used_demo:
            st.warning("官方籃球 API 回傳資料較少，已自動補充示範賽事。")

        finished_games, live_games, upcoming_games = split_games_by_status(games)
        if allow_demo_data:
            finished_games, live_games, upcoming_games = fill_each_section(
                finished_games,
                live_games,
                upcoming_games,
                make_demo_basketball_games(),
                min_finished=2,
                min_live=3,
                min_upcoming=2
            )

        def render_basketball_game(game):
            league_name = game.get("league", {}).get("name", "")
            country = game.get("country", {}).get("name", "")
            home = game.get("teams", {}).get("home", {}).get("name", "")
            away = game.get("teams", {}).get("away", {}).get("name", "")
            home_score = get_score_total(game.get("scores", {}).get("home", {}))
            away_score = get_score_total(game.get("scores", {}).get("away", {}))
            status = game.get("status", {}).get("long", "")
            if game.get("_demo"):
                status = f"{status}｜示範資料"

            render_score_card(
                league_name,
                country,
                home,
                away,
                home_score,
                away_score,
                status,
                "🏀"
            )

            add_live_recommendation(
                "籃球",
                league_name,
                country,
                home,
                away,
                home_score,
                away_score,
                status,
                "basketball"
            )

            change_msg = score_change_text(home, away, home_score, away_score)
            if change_msg:
                st.warning(change_msg)

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                ai_analysis_button(home, away, "basketball", home_score, away_score, status)
            with btn_col2:
                render_favorite_button(home, away, "basketball")

        st.caption(
            f"籃球：進行中 {len(live_games)} 場｜已結束 {len(finished_games)} 場｜即將開賽 {len(upcoming_games)} 場"
        )

        render_section("顯示已結束", finished_games, render_basketball_game, expanded=False)
        render_section("進行中", live_games, render_basketball_game, expanded=True)
        render_section("顯示即將開賽", upcoming_games, render_basketball_game, expanded=False)

    except Exception as e:
        st.error(f"籃球比分讀取失敗：{e}")


st.divider()

render_ai_dashboard()

st.divider()

league = st.selectbox(
    "選擇聯盟",
    ["MLB", "NBA", "足球"]
)

if league == "MLB":
    teams = [
        "洋基","紅襪","藍鳥","光芒","金鶯",
        "守護者","老虎","皇家","雙城","白襪",
        "太空人","水手","遊騎兵","天使","運動家",
        "勇士","馬林魚","大都會","費城人","國民",
        "小熊","紅人","釀酒人","海盜","紅雀",
        "道奇","教士","巨人","響尾蛇","洛磯"
    ]
    data = pd.read_csv("data/mlb_games.csv")

elif league == "NBA":
    teams = [
        "老鷹","塞爾提克","籃網","黃蜂","公牛",
        "騎士","獨行俠","金塊","活塞","勇士",
        "火箭","溜馬","快艇","湖人","灰熊",
        "熱火","公鹿","灰狼","鵜鶘","尼克",
        "雷霆","魔術","76人","太陽","拓荒者",
        "國王","馬刺","暴龍","爵士","巫師"
    ]
    data = pd.read_csv("data/nba_games.csv")

else:
    football_type = st.selectbox(
        "足球類型",
        ["俱樂部", "國家隊"]
    )

    if football_type == "俱樂部":
        teams = [
            "阿森納","曼城","曼聯","利物浦","切爾西",
            "熱刺","紐卡索","阿斯頓維拉",
            "皇家馬德里","巴塞隆納","馬德里競技",
            "尤文圖斯","國際米蘭","AC米蘭",
            "拿坡里","羅馬",
            "拜仁慕尼黑","多特蒙德","勒沃庫森",
            "巴黎聖日耳曼","馬賽","里昂","摩納哥"
        ]
    else:
        teams = [
            "阿根廷","巴西","法國","英格蘭","西班牙",
            "德國","葡萄牙","荷蘭","比利時","克羅埃西亞",
            "義大利","烏拉圭","日本","韓國","澳洲",
            "美國","墨西哥","加拿大","摩洛哥"
        ]

    data = pd.read_csv("data/soccer_games.csv")

# 目前實力 Elo 評分
# 說明：這裡改成固定的「目前強弱近似值」，
# 不再使用 1500 + i * 8 的假資料。
# 數字越高代表實力越強。

if league == "MLB":
    elo_ratings = {
        "道奇": 1600,
        "勇士": 1575,
        "大都會": 1568,
        "水手": 1565,
        "費城人": 1562,
        "老虎": 1560,
        "洋基": 1558,
        "小熊": 1556,
        "藍鳥": 1554,
        "紅襪": 1552,
        "太空人": 1548,
        "教士": 1545,
        "釀酒人": 1542,
        "守護者": 1538,
        "遊騎兵": 1535,
        "金鶯": 1532,
        "光芒": 1530,
        "響尾蛇": 1528,
        "巨人": 1525,
        "皇家": 1522,
        "雙城": 1520,
        "紅人": 1518,
        "紅雀": 1515,
        "天使": 1512,
        "運動家": 1508,
        "海盜": 1505,
        "馬林魚": 1500,
        "國民": 1498,
        "洛磯": 1490,
        "白襪": 1485,
    }

elif league == "NBA":
    elo_ratings = {
        "雷霆": 1740,
        "尼克": 1725,
        "馬刺": 1715,
        "活塞": 1695,
        "塞爾提克": 1685,
        "金塊": 1675,
        "騎士": 1665,
        "湖人": 1655,
        "公鹿": 1645,
        "勇士": 1635,
        "火箭": 1628,
        "魔術": 1620,
        "溜馬": 1615,
        "76人": 1608,
        "熱火": 1602,
        "快艇": 1595,
        "國王": 1588,
        "太陽": 1580,
        "灰狼": 1575,
        "獨行俠": 1568,
        "灰熊": 1560,
        "老鷹": 1555,
        "公牛": 1548,
        "暴龍": 1542,
        "黃蜂": 1538,
        "籃網": 1532,
        "鵜鶘": 1525,
        "爵士": 1518,
        "拓荒者": 1510,
        "巫師": 1495,
    }

else:
    if football_type == "俱樂部":
        elo_ratings = {
            "阿森納": 2066,
            "拜仁慕尼黑": 2001,
            "曼城": 1970,
            "巴黎聖日耳曼": 1964,
            "巴塞隆納": 1953,
            "皇家馬德里": 1925,
            "阿斯頓維拉": 1920,
            "利物浦": 1910,
            "國際米蘭": 1890,
            "勒沃庫森": 1875,
            "馬德里競技": 1855,
            "多特蒙德": 1830,
            "拿坡里": 1825,
            "尤文圖斯": 1815,
            "AC米蘭": 1795,
            "切爾西": 1785,
            "熱刺": 1770,
            "紐卡索": 1765,
            "羅馬": 1755,
            "摩納哥": 1745,
            "馬賽": 1735,
            "里昂": 1725,
            "曼聯": 1715,
        }
    else:
        elo_ratings = {
            "西班牙": 2155,
            "阿根廷": 2113,
            "法國": 2062,
            "英格蘭": 2020,
            "巴西": 1988,
            "葡萄牙": 1975,
            "荷蘭": 1955,
            "德國": 1935,
            "比利時": 1905,
            "克羅埃西亞": 1890,
            "義大利": 1885,
            "烏拉圭": 1870,
            "摩洛哥": 1840,
            "日本": 1825,
            "美國": 1805,
            "墨西哥": 1795,
            "韓國": 1785,
            "澳洲": 1770,
            "加拿大": 1760,
        }

# 避免新增隊伍時找不到評分
elo_ratings = {
    team: elo_ratings.get(team, 1500)
    for team in teams
}

col1, col2 = st.columns(2)

selected_home_zh = zh_team(st.session_state.get("selected_home_team", ""))
selected_away_zh = zh_team(st.session_state.get("selected_away_team", ""))

home_index = 0
if selected_home_zh in teams:
    home_index = teams.index(selected_home_zh)

with col1:
    home_team = st.selectbox(
        "主隊",
        teams,
        index=home_index
    )

with col2:
    away_options = [t for t in teams if t != home_team]

    away_index = 0
    if selected_away_zh in away_options:
        away_index = away_options.index(selected_away_zh)

    away_team = st.selectbox(
        "客隊",
        away_options,
        index=away_index
    )

home_elo = elo_ratings[home_team]
away_elo = elo_ratings[away_team]
elo_diff = home_elo - away_elo

st.subheader("⭐ Elo 評分")

e1, e2, e3 = st.columns(3)

e1.metric(f"{home_team} Elo", home_elo)
e2.metric(f"{away_team} Elo", away_elo)
e3.metric("Elo 差距", elo_diff)

st.divider()

X = data[
    [
        "home_win_rate",
        "away_win_rate",
        "home_rest_days",
        "away_rest_days"
    ]
]

y = data["result"].astype(int)

model = XGBClassifier(
    n_estimators=200,
    max_depth=4,
    learning_rate=0.05,
    random_state=42,
    eval_metric="logloss"
)

model.fit(X, y)

st.subheader("📊 比賽數據")

c1, c2 = st.columns(2)

with c1:
    home_win_rate = st.slider("主隊勝率", 0.0, 1.0, 0.60)
    home_rest_days = st.slider("主隊休息天數", 0, 7, 2)
    home_last10 = st.slider("主隊最近10場勝場", 0, 10, 6)
    home_field_rate = st.slider("主隊主場勝率", 0.0, 1.0, 0.60)
    home_streak = st.slider("主隊連勝/連敗", -10, 10, 1)

with c2:
    away_win_rate = st.slider("客隊勝率", 0.0, 1.0, 0.50)
    away_rest_days = st.slider("客隊休息天數", 0, 7, 1)
    away_last10 = st.slider("客隊最近10場勝場", 0, 10, 5)
    away_field_rate = st.slider("客隊客場勝率", 0.0, 1.0, 0.50)
    away_streak = st.slider("客隊連勝/連敗", -10, 10, 0)

st.subheader("💰 賠率設定")

decimal_odds = st.number_input(
    "輸入賠率（十進位，可選）",
    min_value=1.01,
    max_value=20.0,
    value=1.90,
    step=0.01
)

def get_stars(confidence):
    if confidence >= 0.50:
        return "★★★★★"
    elif confidence >= 0.35:
        return "★★★★"
    elif confidence >= 0.20:
        return "★★★"
    elif confidence >= 0.10:
        return "★★"
    return "★"

def get_risk(confidence):
    if confidence >= 0.50:
        return "低風險", "success"
    elif confidence >= 0.35:
        return "中低風險", "success"
    elif confidence >= 0.20:
        return "中風險", "warning"
    elif confidence >= 0.10:
        return "中高風險", "warning"
    return "高風險", "error"

def get_half_point_spread(confidence, league):
    # MLB 讓分通常不會開太誇張，限制最高 -3.5
    if league == "MLB":
        if confidence < 0.18:
            return 0.5
        elif confidence < 0.35:
            return 1.5
        elif confidence < 0.55:
            return 2.5
        else:
            return 3.5

    # NBA 讓分可較大
    elif league == "NBA":
        if confidence < 0.15:
            return 1.5
        elif confidence < 0.25:
            return 3.5
        elif confidence < 0.35:
            return 5.5
        elif confidence < 0.45:
            return 7.5
        else:
            return 9.5

    # 足球讓分限制最高 -3.5
    else:
        if confidence < 0.20:
            return 0.5
        elif confidence < 0.40:
            return 1.5
        elif confidence < 0.60:
            return 2.5
        else:
            return 3.5

if st.button("開始預測"):
    new_game = pd.DataFrame({
        "home_win_rate": [home_win_rate],
        "away_win_rate": [away_win_rate],
        "home_rest_days": [home_rest_days],
        "away_rest_days": [away_rest_days]
    })

    prob = model.predict_proba(new_game)[0]

    elo_bonus = elo_diff / 10000
    last10_bonus = (home_last10 - away_last10) / 100
    field_bonus = (home_field_rate - away_field_rate) / 20
    streak_bonus = (home_streak - away_streak) / 200

    home_final = min(
        max(
            prob[1]
            + elo_bonus
            + last10_bonus
            + field_bonus
            + streak_bonus,
            0
        ),
        1
    )

    away_final = 1 - home_final
    confidence = abs(home_final - away_final)
    winner = home_team if home_final > away_final else away_team

    stars = get_stars(confidence)
    risk, risk_type = get_risk(confidence)

    upset_probability = min(
        max(1 - max(home_final, away_final), 0),
        1
    )

    implied_probability = 1 / decimal_odds

    kelly_index = (
        (max(home_final, away_final) * decimal_odds - 1)
        / (decimal_odds - 1)
    )

    # AI大小分預測：依照聯盟轉換成標準 .5 盤口
    if league == "MLB":
        raw_total = (
            7
            + (home_win_rate + away_win_rate) * 2
            + (home_last10 + away_last10) * 0.1
        )

        pred_total = round(raw_total) + 0.5

        if pred_total < 6.5:
            pred_total = 6.5
        elif pred_total > 12.5:
            pred_total = 12.5

        total_advice = "大分" if pred_total >= 8.5 else "小分"

    elif league == "NBA":
        raw_total = (
            200
            + (home_win_rate + away_win_rate) * 15
            + (home_last10 + away_last10)
        )

        pred_total = round(raw_total / 2) * 2 + 0.5

        if pred_total < 200.5:
            pred_total = 200.5
        elif pred_total > 240.5:
            pred_total = 240.5

        total_advice = "大分" if pred_total >= 220.5 else "小分"

    else:
        raw_total = (
            1.5
            + (home_win_rate + away_win_rate)
            + (home_last10 + away_last10) * 0.05
        )

        pred_total = round(raw_total) + 0.5

        if pred_total < 1.5:
            pred_total = 1.5
        elif pred_total > 4.5:
            pred_total = 4.5

        total_advice = "大分" if pred_total >= 2.5 else "小分"

    spread = get_half_point_spread(confidence, league)

    if home_final > away_final:
        spread_text = f"{home_team} -{spread:.1f}"
    else:
        spread_text = f"{away_team} -{spread:.1f}"

    st.subheader("🏆 預測結果")

    r1, r2, r3, r4 = st.columns(4)

    r1.metric(f"{home_team} 勝率", f"{home_final:.2%}")
    r2.metric(f"{away_team} 勝率", f"{away_final:.2%}")
    r3.metric("模型信心", f"{confidence:.2%}")
    r4.metric("推薦星等", stars)

    st.success(f"預測勝方：{winner}")

    st.subheader("🧠 AI 分析理由")

    reason = []

    if home_win_rate > away_win_rate:
        reason.append("主隊整體勝率較高")
    elif home_win_rate < away_win_rate:
        reason.append("客隊整體勝率較高")
    else:
        reason.append("雙方整體勝率接近")

    if home_last10 > away_last10:
        reason.append("主隊最近10場狀態較佳")
    elif home_last10 < away_last10:
        reason.append("客隊最近10場狀態較佳")
    else:
        reason.append("雙方近期狀態接近")

    if home_rest_days > away_rest_days:
        reason.append("主隊休息時間較充足")
    elif home_rest_days < away_rest_days:
        reason.append("客隊休息時間較充足")
    else:
        reason.append("雙方休息天數相同")

    if home_elo > away_elo:
        reason.append("主隊 Elo 評分較高")
    elif home_elo < away_elo:
        reason.append("客隊 Elo 評分較高")
    else:
        reason.append("雙方 Elo 評分相同")

    for item in reason:
        st.write("✔", item)

    st.subheader("🎯 風險評級")

    if risk_type == "success":
        st.success(risk)
    elif risk_type == "warning":
        st.warning(risk)
    else:
        st.error(risk)

    st.subheader("⚠️ 爆冷機率")
    st.warning(f"爆冷機率：約 {upset_probability:.2%}")

    st.subheader("💰 Kelly 指數")

    st.write(f"市場隱含機率：約 {implied_probability:.2%}")
    st.write(f"Kelly 指數：約 {kelly_index:.2%}")

    if kelly_index > 0.10:
        st.success("Kelly 顯示有正期望值")
    elif kelly_index > 0:
        st.warning("Kelly 顯示小幅正期望值")
    else:
        st.error("Kelly 顯示不具備正期望值")

    st.subheader("🎯 AI讓分分析")
    st.info(spread_text)

    st.subheader("⚾ AI大小分分析")
    st.success(f"預估總分：{pred_total}")
    st.info(f"建議：{total_advice}")

    st.subheader("🔥 今日最佳推薦")

    best_rate = max(home_final, away_final)

    st.info(
        f"""
推薦隊伍：{winner}

預測勝率：{best_rate:.2%}

信心指數：{confidence:.2%}

推薦星等：{stars}

風險等級：{risk}

讓分建議：{spread_text}

模型：XGBoost + Elo + 近期狀態
"""
    )

    chart_data = pd.DataFrame(
        {"勝率": [home_final, away_final]},
        index=[home_team, away_team]
    )

    st.subheader("📈 勝率比較圖")
    st.bar_chart(chart_data)

    model_info = pd.DataFrame({
        "項目": [
            "模型",
            "聯盟",
            "主隊",
            "客隊",
            "主隊Elo",
            "客隊Elo",
            "Elo差距",
            "主隊最近10場",
            "客隊最近10場",
            "主隊連勝/連敗",
            "客隊連勝/連敗",
            "AI讓分"
        ],
        "數值": [
            "XGBoost + Elo + 近期狀態",
            league,
            home_team,
            away_team,
            home_elo,
            away_elo,
            elo_diff,
            home_last10,
            away_last10,
            home_streak,
            away_streak,
            spread_text
        ]
    })

    st.subheader("🧠 AI模型資訊")
    st.dataframe(model_info, use_container_width=True)

    history = pd.DataFrame({
        "時間": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "聯盟": [league],
        "主隊": [home_team],
        "客隊": [away_team],
        "預測勝方": [winner],
        "主隊勝率": [f"{home_final:.2%}"],
        "客隊勝率": [f"{away_final:.2%}"],
        "信心": [f"{confidence:.2%}"],
        "星等": [stars],
        "風險": [risk],
        "爆冷機率": [f"{upset_probability:.2%}"],
        "Kelly指數": [f"{kelly_index:.2%}"],
        "讓分": [spread_text],
        "大小分": [total_advice],
        "模型": ["XGBoost + Elo + 近期狀態"]
    })

    history_path = "data/history.csv"

    if os.path.exists(history_path):
        old_history = pd.read_csv(history_path)
        all_history = pd.concat(
            [old_history, history],
            ignore_index=True
        )
    else:
        all_history = history

    all_history.to_csv(
        history_path,
        index=False
    )

    st.success("已儲存至 data/history.csv")

st.divider()

st.subheader("🏆 今日推薦 TOP 5")

top5 = pd.DataFrame({
    "排名": [1, 2, 3, 4, 5],
    "隊伍": ["洋基", "勇士", "道奇", "湖人", "曼城"],
    "勝率": ["72%", "69%", "68%", "66%", "65%"],
    "星等": ["★★★★★", "★★★★", "★★★★", "★★★", "★★★"]
})

st.dataframe(
    top5,
    use_container_width=True
)

st.subheader("📅 今日賽事區塊")
st.info("下一版可以在這裡加入即時賽程、比分、傷病資訊與歷史對戰資料。")

if os.path.exists("data/history.csv"):
    st.subheader("📚 歷史預測紀錄")

    history_df = pd.read_csv("data/history.csv")

    st.dataframe(
        history_df.tail(20),
        use_container_width=True
    )