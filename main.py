import matplotlib.pyplot as plt
import os
import glob
import random
import discord
import requests
import json
import re
import time
import math
from datetime import datetime, timedelta
from matplotlib import rcParams
from matplotlib import font_manager

font_path = "./NotoSansJP-Medium.ttf"
font_prop = font_manager.FontProperties(fname=font_path)
rcParams['font.family'] = font_prop.get_name()

intents = discord.Intents.none()
intents.members = True
intents.presences = True
intents.guilds = True

client = discord.Client(intents=intents)

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
    "972456281782775859": {
        "regex": r"(\d+)\/(\d+) サーバー",
        "reading": 1,
        "server": 2
    },
}

now_hour_id = math.floor(time.time() / 3600)

online_data = {}
try:
    with open("data/history.json") as f:
        online_data = json.loads(f.read())
    for hour in online_data.keys():
        if int(hour) < now_hour_id - 24 * 7:
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

client.run("MTM4ODE0NjQ1NzM2NTcwODkxMg.G_74Ny.pZyueQOBe-T-_Dn_AC1kqw8-WK-u9mhI69mNac")

print(latest_data)

if latest_data:
    online_data[str(now_hour_id)] = latest_data

with open("data/history.json", mode="w") as f:
    f.write(json.dumps(online_data))

bot_history = {}
for bot in latest_data.keys():
    time_list = []
    server_list = []
    reading_list = []
    for hour in online_data.keys():
        if bot in online_data[hour]:
            date = datetime.fromtimestamp(int(hour) * 3600)
            time_list.append(date)
            if online_data[hour][bot]["online"]:
                if "reading" in online_data[hour][bot]:
                    reading_list.append(online_data[hour][bot]["reading"])
                else:
                    reading_list.append(None)
                if "server" in online_data[hour][bot]:
                    server_list.append(online_data[hour][bot]["server"])
                else:
                    server_list.append(None)
            else:
                reading_list.append(None)
                server_list.append(None)

    spans = []
    in_off = False
    for i, t in enumerate(time_list):
        if reading_list[i] is None and not in_off:
            span_start = t
            in_off = True
        elif reading_list[i] is not None and in_off:
            span_end = t
            spans.append((span_start, span_end))
            in_off = False

    if in_off:
        spans.append((span_start, time_list[-1]))
    
    fig, ax = plt.subplots(figsize=(12, 4))

    ax.plot(time_list, reading_list, label="読み上げ中", linewidth=1.5)
    
    for span_start, span_end in spans:
        ax.axvspan(span_start, span_end, color="gray", alpha=0.3)
    
    ax.set_xlabel("時刻")
    ax.set_ylabel("読み上げ中")
    ax.set_title("日時別の使用状況")
    ax.legend(loc="upper right")
    
    fig.autofmt_xdate()
    
    plt.tight_layout()
    plt.savefig("output/"+bot+".png")
