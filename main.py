import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import glob

for p in glob.glob('output/*.png'):
    if os.path.isfile(p):
        os.remove(p)

# サンプルデータの作成
# 時刻（10分おき、24時間分）
time_index = pd.date_range("2025-06-28 00:00", periods=24*6, freq="10T")
# Ping 値（オンライン時は 30〜100ms の乱数、オフライン時は NaN）
ping = np.random.uniform(30, 100, size=len(time_index))
# 例えば深夜の 02:00〜04:00 と、夕方の 18:00〜19:30 はオフラインとする
offline_mask = ((time_index >= "2025-06-28 02:00") & (time_index < "2025-06-28 04:00")) | \
               ((time_index >= "2025-06-28 18:00") & (time_index < "2025-06-28 19:30"))
ping[offline_mask] = np.nan

# DataFrame にまとめ
df = pd.DataFrame({"ping": ping}, index=time_index)

# プロット
fig, ax = plt.subplots(figsize=(12, 4))

# 折れ線：オンライン（NaN 部分は自動的に途切れる）
ax.plot(df.index, df["ping"], label="Ping (ms)", linewidth=1.5)

# オフライン期間を暗く塗りつぶす
for start, end in zip(
    df.index[offline_mask & (~offline_mask.shift(fill_value=False))],
    df.index[(offline_mask.shift(fill_value=False) & ~offline_mask)]
):
    ax.axvspan(start, end, color="gray", alpha=0.3)

# 軸ラベル・タイトル
ax.set_xlabel("時刻")
ax.set_ylabel("Ping (ms)")
ax.set_title("Ping 推移グラフ(テスト)")
ax.legend(loc="upper right")

# x軸の見やすさ調整
fig.autofmt_xdate()

plt.tight_layout()
plt.savefig("output/test2.png")
