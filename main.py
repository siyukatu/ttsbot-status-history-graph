import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import glob
import random
from datetime import datetime, timedelta

for p in glob.glob('output/*.png'):
    if os.path.isfile(p):
        os.remove(p)

# --- データ準備 ---

# 1. 時刻リスト（10分おき、24時間分）
start_time = datetime(2025, 6, 28, 0, 0)
time_list = [start_time + timedelta(minutes=10*i) for i in range(24*6)]

# 2. Ping 値リスト（オンラインは乱数、オフラインは None）
ping_list = []
for t in time_list:
    # オフライン時間帯を定義
    offline = (
        datetime(2025, 6, 28, 2, 0) <= t < datetime(2025, 6, 28, 4, 0)
        or datetime(2025, 6, 28, 18, 0) <= t < datetime(2025, 6, 28, 19, 30)
    )
    if offline:
        ping_list.append(None)
    else:
        ping_list.append(random.uniform(30, 100))  # 30〜100ms の乱数

# 3. オフライン期間のスパン検出
spans = []
in_off = False
for i, t in enumerate(time_list):
    if ping_list[i] is None and not in_off:
        # オフライン開始
        span_start = t
        in_off = True
    elif ping_list[i] is not None and in_off:
        # オフライン終了
        span_end = t
        spans.append((span_start, span_end))
        in_off = False
# 最後までオフラインだった場合の補完
if in_off:
    spans.append((span_start, time_list[-1]))

# --- プロット ---

fig, ax = plt.subplots(figsize=(12, 4))

# 折れ線：オンライン部分のみ描画（None は自動的に途切れる）
ax.plot(time_list, ping_list, label="Ping (ms)", linewidth=1.5)

# オフライン期間を暗く塗りつぶし
for span_start, span_end in spans:
    ax.axvspan(span_start, span_end, color="gray", alpha=0.3)

# 軸ラベル・タイトル
ax.set_xlabel("時刻")
ax.set_ylabel("Ping (ms)")
ax.set_title("Discord Bot の Ping 推移")
ax.legend(loc="upper right")

# x軸の日時を見やすく回転
fig.autofmt_xdate()

plt.tight_layout()
plt.savefig("output/test2.png")
