import matplotlib.pyplot as plt
import os
import glob
import random
import discord
import requests
import json
import io
import re
import time
import math
import msgpack
from scour import scour
from datetime import datetime, timedelta, timezone
from matplotlib import rcParams
from matplotlib import font_manager
from matplotlib.ticker import MaxNLocator
from matplotlib.backends.backend_svg import FigureCanvasSVG

opts = scour.sanitizeOptions()
opts.remove_metadata = True
opts.remove_descriptive_elements = True
opts.remove_titles = True
opts.remove_descriptions = True
opts.enable_comment_stripping = True
opts.keep_unreferenced_defs = False
opts.keep_editor_data = False
opts.disable_embed_rasters = True
opts.enable_id_stripping = True
opts.shorten_ids = True
opts.disable_group_collapsing = False
opts.create_groups = True
opts.disable_simplify_colors = False
opts.disable_style_to_xml = False
opts.enable_viewboxing = True
opts.renderer_workaround = False
opts.set_precision = 5
opts.set_c_precision = 5
opts.strip_xml_prolog = True
opts.strip_xml_space = True
opts.indent_type = None
opts.no_line_breaks = True

font_path = os.path.join(os.path.dirname(__file__), "NotoSansJP-Medium.ttf")
font_manager.fontManager.addfont(font_path)
prop = font_manager.FontProperties(fname=font_path)
font_name = prop.get_name()
plt.rcParams['font.family'] = font_name
plt.rcParams['font.sans-serif'] = [font_name]
#plt.rc("svg", fonttype="none")

intents = discord.Intents.none()
intents.members = True
intents.presences = True
intents.guilds = True

client = discord.Client(intents=intents)

def get_median(data):
    half = len(score) // 2
    score.sort()
    if len(score) % 2 == 0:
        mdn = (score[half - 1] + score[half]) / 2.0
    else:
        mdn = score[half]
    return mdn

for p in glob.glob('output/*.png')+glob.glob('output/*.svg'):
    if os.path.isfile(p):
        os.remove(p)

bots = {
    "1467103416776917043": {
        "regex": r"Servers: \d+/(\d+) \| VCs: \d+/(\d+)",
        "reading": 2,
        "server": 1
    },
    "1429102950722043944": {
        "regex": r"(\d+)VCで読み上げ中 \/ (\d+)サーバーに導入",
        "reading": 1,
        "server": 2
    },
    "1135864594146005042": {
        "regex": r"読み上げ中: \d+\/(\d+) \| サーバー数: (\d+)",
        "reading": 1,
        "server": 2
    },
    "695096014482440244": {},
    "1170665001443405854": {
        "regex": r"(\d+)Servers \| \d+Shards \| VC:(\d+)",
        "reading": 2,
        "server": 1
    },
    "1330469772915245107": {},
    "1333819940645638154": {
        "regex": r"VC接続中: \d+\/(\d+) \| サーバー数: (\d+)",
        "reading": 1,
        "server": 2
    },
    "1343805344098553938": {
        "regex": r"(\d+)サーバー \| (\d+)VC接続中",
        "reading": 2,
        "server": 1
    },
    "1371465579780767824": {
        "regex": r"(\d+) servers \| (\d+) VCs",
        "reading": 2,
        "server": 1
    },
    "518899666637553667": {},
    "533698325203910668": {},
    "727508841368911943": {
        "regex": r"(\d+)servers \| (\d+)VC",
        "reading": 2,
        "server": 1
    },
    "865517105118183434": {},
    "917633605684056085": {
        "regex": r"(\d+)\/(\d+)読み上げ中",
        "reading": 1,
        "server": 2
    },
    "940658205950885908": {},
    "972456281782775859": {
        "regex": r"(\d+)\/(\d+) サーバー",
        "reading": 1,
        "server": 2
    },
    "1019823740479082526": {
        "regex": r"(\d+)\/(\d+) サーバー",
        "reading": 1,
        "server": 2
    },
    "887986350199013406": {
        "regex": r"(\d+)ボイスチャンネル \/ (\d+)サーバー",
        "reading": 1,
        "server": 2
    },
    "916300992612540467": {
        "regex": r"(\d+)ボイスチャンネル \/ (\d+)サーバー",
        "reading": 1,
        "server": 2
    },
    "1392268209742287019": {
        "regex": r"参加VC: (\d+) \/ 導入サーバー: (\d+)",
        "reading": 1,
        "server": 2
    },
    "1532309518828961823": {
        "regex": r"(\d+)サーバー \| VC (\d+)",
        "reading": 2,
        "server": 1
    },
    "1460650023611011286": {}
}

now_hour_id = math.floor(time.time() / 300) * 300

online_data = {}
avatars = {}
try:
    try:
        with open("data/history.dat", mode="rb") as f:
            online_data = msgpack.unpackb(f.read())
    except:
        with open("data/history.json") as f:
            online_data = json.loads(f.read())
    for hour in online_data.keys():
        if int(hour) < now_hour_id - 31 * 24 * 60 * 60:
            del online_data[hour]
except:pass

latest_data = None
bot_names = {}
is_onlines = {}

@client.event
async def on_ready():
    global latest_data
    print(f"Logged in as {client.user}")
    guild = client.get_guild(1387592992923324496)
    data = {}
    now = time.time()
    for bot in bots.keys():
        data[bot] = {
            "online": False
        }
    try:
        for member in guild.members:
            try:
                bot_id = str(member.id)
                bot_name = member.display_name
                if bot_id in bots:
                    avatars[bot_id] = member.display_avatar.url
                    bot_names[bot_id] = bot_name
                    online = member.status == bots[bot_id].get("online", discord.Status.online)
                    data[bot_id]["online"] = online
                    is_onlines[bot_id] = online
                    reading_count = None
                    server_count = None
                    activity = None
                    if member.activity:
                        activity = member.activity.name
                    if "regex" in bots[bot_id] and activity:
                        regex = bots[bot_id]["regex"]
                        match = re.search(regex, activity)
                        if match:
                            if "reading" in bots[bot_id]:
                                reading_count = int(match.group(bots[bot_id]["reading"]))
                                data[bot_id]["reading"] = reading_count
                            if "server" in bots[bot_id]:
                                server_count = int(match.group(bots[bot_id]["server"]))
                                data[bot_id]["server"] = server_count
                    if not "server" in bots[bot_id]:
                        try:
                            appinfo = requests.get("https://discord.com/api/v9/application-directory-static/applications/"+str(bot_id)+"?locale=ja&t="+str(now))
                            if appinfo.status_code == 200:
                                appdata = appinfo.json()
                                server_count = appdata["directory_entry"]["guild_count"]
                                data[bot_id]["server"] = server_count
                        except:pass
                    print(f"Bot ID: {bot_id}, Reading: {reading_count}, Servers: {server_count}, Online: {online}")
                    with open("data/"+bot_id+".dat", mode="wb") as f:
                        f.write(msgpack.packb(data[bot_id]))
            except:continue
    except:pass
    latest_data = data
    await client.close()

client.run(os.environ.get("DISCORD_TOKEN"))

print(latest_data)

if latest_data:
    online_data[str(now_hour_id)] = latest_data

with open("data/history.dat", mode="wb") as f:
    f.write(msgpack.packb(online_data))
with open("data/history.json", mode="w") as f:
    f.write(json.dumps(online_data))

bot_history = {}
summary = {}
graph_list = []

lasthour = list(online_data.keys())[-1]
for hour in online_data:
    tmpdata = {"online":True,"server":0,"reading":0}
    for bot in online_data[hour]:
        tmpdata["server"] += online_data[hour][bot].get("server",0)
        tmpdata["reading"] += online_data[hour][bot].get("reading",0)
    if hour != lasthour:
        online_data[hour]["all"] = tmpdata
    else:
        latest_data["all"] = tmpdata

for bot in latest_data.keys():
    time_list = []
    online_list = []
    if bot == "all":
        server_available = True
        server_list = []
        reading_available = True
        reading_list = []
    else:
        server_available = bots[bot].get("server") is not None or latest_data[bot].get("server") is not None
        server_list = []
        reading_available = bots[bot].get("reading") is not None or latest_data[bot].get("reading") is not None
        reading_list = []
        if not server_available or not reading_available:
            for hour in online_data:
                botdata = online_data[hour].get(bot)
                if botdata != None:
                    if botdata.get("server") != None:server_available = True
                    if botdata.get("reading") != None:reading_available = True
    total = 0
    up = 0
    summary[bot] = {}

    server_count_first = None
    server_count_last = None

    last_online = None
    for hour in online_data.keys():
        if bot in online_data[hour]:
            total += 1
            date = datetime.fromtimestamp(int(hour), timezone(timedelta(hours=9)))
            time_list.append(date)
            if online_data[hour][bot]["online"]:
                up += 1
                online_list.append(True)
                if "reading" in online_data[hour][bot]:
                    reading_list.append(online_data[hour][bot]["reading"])
                    summary[bot]["reading"] = online_data[hour][bot]["reading"]
                else:
                    reading_list.append(None)
                if "server" in online_data[hour][bot]:
                    server_list.append(online_data[hour][bot]["server"])
                    summary[bot]["server"] = online_data[hour][bot]["server"]
                    if server_count_first == None:
                        server_count_first = online_data[hour][bot]["server"]
                    if online_data[hour][bot]["server"] != None:
                        server_count_last = online_data[hour][bot]["server"]
                else:
                    server_list.append(None)
                last_online = hour
            else:
                online_list.append(False)
                reading_list.append(None)
                server_list.append(None)
    summary[bot]["uptime"] = str(math.floor(up/total*100*100)/100)+"%"
    try:
        summary[bot]["invited"] = server_count_last - server_count_first
    except:pass
    try:
        summary[bot]["is_online"] = is_onlines[bot]
    except:
        summary[bot]["is_online"] = False
    summary[bot]["last_online"] = last_online

    offline_spans = []
    in_off = False
    for i, t in enumerate(time_list):
        if online_list[i] is False and not in_off:
            if i - 1 > 0:
                span_start = time_list[i - 1]
            else:
                span_start = t
            in_off = True
        elif online_list[i] is True and in_off:
            span_end = t
            offline_spans.append([span_start.timestamp(), span_end.timestamp()])
            in_off = False
    if in_off:
        offline_spans.append([span_start.timestamp(), time_list[-1].timestamp()])
    summary[bot]["offline_spans"] = offline_spans

    # どちらもFalseの場合はグラフ生成を中止
    if not reading_available and not server_available:
        print(f"Bot {bot}: 読み上げ・サーバー両方のデータが利用できないため、グラフを生成しません")
        continue

    # 利用可能なグラフの数に応じてレイアウトを決定
    num_plots = sum([reading_available, server_available])

    reading_spans = []
    in_off = False
    for i, t in enumerate(time_list):
        if reading_list[i] is None and not in_off:
            if i - 1 > 0:
                span_start = time_list[i - 1]
            else:
                span_start = t
            in_off = True
        elif reading_list[i] is not None and in_off:
            span_end = t
            reading_spans.append((span_start, span_end))
            in_off = False

    if in_off:
        reading_spans.append((span_start, time_list[-1]))

    server_spans = []
    in_off = False
    for i, t in enumerate(time_list):
        if server_list[i] is None and not in_off:
            if i - 1 > 0:
                span_start = time_list[i - 1]
            else:
                span_start = t
            in_off = True
        elif server_list[i] is not None and in_off:
            span_end = t
            server_spans.append((span_start, span_end))
            in_off = False

    if in_off:
        server_spans.append((span_start, time_list[-1]))

    if num_plots == 2:
        # 両方のグラフを作成（上下に配置）
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

        # 上のグラフ: 同時接続数
        ax1.plot(time_list, reading_list, label="同時接続数", linewidth=1.5, color='#2288ff')

        for span_start, span_end in reading_spans:
            ax1.axvspan(span_start, span_end, color="#ddd", alpha=1)

        ax1.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax1.yaxis.get_major_formatter().set_useOffset(False)
#        ax1.set_ylabel("同時接続数")
        ax1.set_title("同時接続数の推移")
#        ax1.legend(loc="upper right")
        ax1.grid(True, alpha=0.3)

        # 下のグラフ: サーバー数
        ax2.plot(time_list, server_list, label="サーバー数", linewidth=1.5, color='#2288ff')

        for span_start, span_end in server_spans:
            ax2.axvspan(span_start, span_end, color="#ddd", alpha=1)

        ax2.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax2.yaxis.get_major_formatter().set_useOffset(False)
#        ax2.set_xlabel("時刻")
#        ax2.set_ylabel("サーバー数")
        ax2.set_title("サーバー数の推移")
#        ax2.legend(loc="upper right")
        ax2.grid(True, alpha=0.3)

    else:
        # 1つのグラフのみ作成
        fig, ax = plt.subplots(figsize=(12, 4))

        if reading_available:
            ax.plot(time_list, reading_list, label="読み上げ中", linewidth=1.5, color='#2288ff')
            ax.set_title("同時接続数の推移")
            spans = reading_spans
#            ax.set_ylabel("読み上げ中")
        elif server_available:
            ax.plot(time_list, server_list, label="サーバー数", linewidth=1.5, color='#2288ff')
            ax.set_title("サーバー数の推移")
            spans = server_spans
#            ax.set_ylabel("サーバー数")

        for span_start, span_end in spans:
            ax.axvspan(span_start, span_end, color="#ddd", alpha=1)

        ax.set_xlabel("時刻")
#        ax.set_title("日時別の使用状況")
#        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.3)

    fig.autofmt_xdate()

    plt.tight_layout()
    plt.savefig("output/"+bot+".png")

    buf = io.StringIO()
    canvas = FigureCanvasSVG(fig)
    canvas.print_svg(buf)
    svg_raw = buf.getvalue()
    with open("output/"+bot+".svg", "w", encoding="utf-8") as f:
        f.write(scour.scourString(svg_raw, options=opts))
    graph_list.append(bot)

with open("data/summary.json", mode="w") as f:
    f.write(json.dumps(summary))

with open("data/bot_avatars.json", mode="w") as f:
    f.write(json.dumps(avatars))

with open("data/bot_names.json", mode="w") as f:
    f.write(json.dumps(bot_names))

with open("output/graph_list.html", mode="w") as f:
    f.write('<img src="'+('.svg"/><br><img src="'.join(graph_list))+'.svg?_='+str(now_hour_id)+'"/>')

with open("output/all.json", mode="w") as f:
    f.write(json.dumps([summary, avatars, requests.get("https://zenn-ttsbot-article-summary.siyukatu.workers.dev/export").json(), {"updated_at": time.time()}], ensure_ascii=False))
