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

for p in glob.glob('output/*.png'):
    if os.path.isfile(p):
        os.remove(p)

bots = {
    "1135864594146005042": {
        "regex": r"読み上げ中: (\d+)\/\d+ \| サーバー数: (\d+)\/\d+",
        "reading": 1,
        "server": 2
    },
    "1170665001443405854": {
        "regex": r"(\d+)Servers \| \d+Users \| VC:(\d+)",
        "reading": 2,
        "server": 1
    },
    "1330469772915245107": {},
    "1333819940645638154": {},
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
    "744238280928919704": {
        "regex": r"(\d+)servers \| joining (\d+)channels",
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
}

now_hour_id = math.floor(time.time() / 300) * 300

online_data = {}
try:
    try:
        with open("data/history.dat", mode="rb") as f:
            online_data = msgpack.unpackb(f.read())
    except:
        with open("data/history.json") as f:
            online_data = json.loads(f.read())
    for hour in online_data.keys():
        if int(hour) < now_hour_id - 14 * 24 * 60 * 60:
            del online_data[hour]
except:pass

latest_data = None

@client.event
async def on_ready():
    global latest_data
    print(f"Logged in as {client.user}")
    guild = client.get_guild(1387592992923324496)
    data = {}
    for bot in bots.keys():
        data[bot] = {
            "online": False
        }
    try:
        for member in guild.members:
            try:
                bot_id = str(member.id)
                if bot_id in bots:
                    online = member.status == bots[bot_id].get("online", discord.Status.online)
                    data[bot_id]["online"] = online
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
                    print(f"Bot ID: {bot_id}, Reading: {reading_count}, Servers: {server_count}, Online: {online}")
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

for bot in latest_data.keys():
    time_list = []
    server_available = latest_data[bot].get("server") is not None
    server_list = []
    reading_available = latest_data[bot].get("reading") is not None
    reading_list = []
    total = 0
    up = 0
    summary[bot] = {}
    for hour in online_data.keys():
        if bot in online_data[hour]:
            total += 1
            date = datetime.fromtimestamp(int(hour), timezone(timedelta(hours=9)))
            time_list.append(date)
            if online_data[hour][bot]["online"]:
                if "reading" in online_data[hour][bot] or "server" in online_data[hour][bot]:
                    up += 1
                if "reading" in online_data[hour][bot]:
                    reading_list.append(online_data[hour][bot]["reading"])
                    summary[bot]["reading"] = online_data[hour][bot]["reading"]
                else:
                    reading_list.append(None)
                if "server" in online_data[hour][bot]:
                    server_list.append(online_data[hour][bot]["server"])
                    summary[bot]["server"] = online_data[hour][bot]["server"]
                else:
                    server_list.append(None)
            else:
                reading_list.append(None)
                server_list.append(None)
    summary[bot]["uptime"] = str(math.floor(up/total*100*1000)/1000)+"%"

    spans = []
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
            spans.append((span_start, span_end))
            in_off = False

    if in_off:
        spans.append((span_start, time_list[-1]))

    # どちらもFalseの場合はグラフ生成を中止
    if not reading_available and not server_available:
        print(f"Bot {bot}: 読み上げ・サーバー両方のデータが利用できないため、グラフを生成しません")
        continue

    # 利用可能なグラフの数に応じてレイアウトを決定
    num_plots = sum([reading_available, server_available])

    if num_plots == 2:
        # 両方のグラフを作成（上下に配置）
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

        # 上のグラフ: 同時接続数
        ax1.plot(time_list, reading_list, label="同時接続数", linewidth=1.5, color='#2288ff')

        for span_start, span_end in spans:
            ax1.axvspan(span_start, span_end, color="gray", alpha=0.3)

        ax1.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax1.yaxis.get_major_formatter().set_useOffset(False)
#        ax1.set_ylabel("同時接続数")
        ax1.set_title("同時接続数の推移")
#        ax1.legend(loc="upper right")
        ax1.grid(True, alpha=0.3)

        # 下のグラフ: サーバー数
        ax2.plot(time_list, server_list, label="サーバー数", linewidth=1.5, color='#2288ff')

        for span_start, span_end in spans:
            ax2.axvspan(span_start, span_end, color="gray", alpha=0.3)

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
#            ax.set_ylabel("読み上げ中")
        elif server_available:
            ax.plot(time_list, server_list, label="サーバー数", linewidth=1.5, color='#2288ff')
            ax.set_title("サーバー数の推移")
#            ax.set_ylabel("サーバー数")

        for span_start, span_end in spans:
            ax.axvspan(span_start, span_end, color="gray", alpha=0.3)

        ax.set_xlabel("時刻")
        ax.set_title("日時別の使用状況")
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

with open("data/summary.json", mode="w") as f:
    f.write(json.dumps(summary))
