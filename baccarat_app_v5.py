# baccarat_app_v8.py
import streamlit as st
import pandas as pd

st.set_page_config(page_title="百家樂推測助手", page_icon="🎲", layout="centered")
st.title("百家樂推測助手")
st.markdown("純娛樂")

# --- 初始化 session state ---
if "results" not in st.session_state:
    st.session_state.results = []

# --- 按鈕列（莊、閒、和、超6、倒退）---
cols = st.columns([1,1,1,1,1])
with cols[0]:
    if st.button("莊"):
        st.session_state.results.append("莊")
with cols[1]:
    if st.button("閒"):
        st.session_state.results.append("閒")
with cols[2]:
    if st.button("和"):
        st.session_state.results.append("和")
with cols[3]:
    if st.button("超6"):
        st.session_state.results.append("超6")
with cols[4]:
    if st.button("倒退"):
        if st.session_state.results:
            st.session_state.results.pop()

# --- 控制按鈕（推測、清空）---
c1, c2 = st.columns([1,1])
with c1:
    analyze = st.button("開始推測")
with c2:
    if st.button("清空"):
        st.session_state.results = []

# --- 顯示簡短紀錄（最後80局）---
st.markdown("**當前紀錄（前 80 局）**：" + (" → ".join(st.session_state.results[-80:]) if st.session_state.results else "無"))

# -------------------------
# helper: build simplified big road columns (keep original logic)
# -------------------------
def build_big_road_columns(results):
    cols = []
    last_non_tie = None
    for r in results:
        # treat '超6' as non-tie (it's a庄 variant) but we don't change columning behavior for appearance
        if r == "和":
            continue
        val = "莊" if r == "超6" else r
        if last_non_tie is None:
            cols.append([val])
            last_non_tie = val
        else:
            if val == last_non_tie:
                cols[-1].append(val)
            else:
                cols.append([val])
                last_non_tie = val
    return cols

def derive_subroad_colors(columns):
    lens = [len(c) for c in columns]
    n = len(lens)
    bigeye = []
    small = []
    cock = []
    for i in range(1, n):
        bigeye.append("red" if lens[i] == lens[i-1] else "blue")
    for i in range(2, n):
        small.append("red" if lens[i] == lens[i-2] else "blue")
    for i in range(3, n):
        cock.append("red" if lens[i] == lens[i-3] else "blue")
    return bigeye, small, cock

# -------------------------
# combine / prediction (保留主流派邏輯，並把超6視為莊；若最近為超6略降信心)
# -------------------------
def combine_prediction(results):
    non_tie = [r for r in results if r != "和"]
    if not non_tie:
        return None, "資料不足（尚未有莊或閒局）"

    total = len(results)
    banker = results.count("莊") + results.count("超6")
    player = results.count("閒")
    tie = results.count("和")
    super6_count = results.count("超6")

    # build big road using '莊' for '超6'
    cols = build_big_road_columns(results)

    bigeye, small, cock = derive_subroad_colors(cols)

    red_count = sum(1 for x in (bigeye + small + cock) if x == "red")
    blue_count = sum(1 for x in (bigeye + small + cock) if x == "blue")
    total_checks = red_count + blue_count

    if total_checks == 0:
        if banker > player:
            conf = min(60, 50 + (banker-player)*5)
            # 若包含超6，稍微降低信心
            if super6_count:
                conf = max(40, conf - super6_count*3)
            return "莊", f"基礎頻率偏莊（含超6 {super6_count}次）；信心 {conf}%"
        elif player > banker:
            return "閒", f"基礎頻率偏閒（閒 {player} vs 莊含超6 {banker}），信心 {min(60, 50 + (player-banker)*5)}%"
        else:
            return "觀望", "莊閒頻率相等，建議觀望"

    stability = int(round((red_count / total_checks) * 100)) if total_checks>0 else 0

    last_non_tie = None
    for r in reversed(results):
        if r != "和":
            last_non_tie = "莊" if r == "超6" else r
            last_raw = r
            break

    if red_count > blue_count:
        predicted = last_non_tie
        note = f"多數副路顯示紅（{red_count}紅 / {blue_count}藍），傾向順勢延續"
        confidence = int(min(95, 50 + (stability-50)//1 + abs(banker-player)))
    elif blue_count > red_count:
        predicted = "莊" if last_non_tie=="閒" else "閒"
        note = f"多數副路顯示藍（{blue_count}藍 / {red_count}紅），傾向反轉"
        confidence = int(min(95, 45 + (100-stability)//1 + abs(banker-player)))
    else:
        predicted = "觀望"
        note = f"紅藍相等（{red_count} / {blue_count}），建議觀望"
        confidence = 50

    # 若最近一局是超6，略降信心（實戰上超6常帶轉折）
    if 'last_raw' in locals() and last_raw == "超6":
        confidence = max(1, confidence - 7)

    # 若超6 出現頻率高，也小幅降低總信心
    confidence = max(1, confidence - min(8, super6_count * 2))

    diff = abs(banker - player)
    confidence = min(99, confidence + min(10, diff*2))

    return predicted, f"{note} | 穩定度 {stability}% | 信心指數 {confidence}%  (超6 次數：{super6_count})"

# -------------------------
# grid render (6 rows x 12 cols, column-major filling)
# -------------------------
ROWS = 6
COLS = 12
CELLS = ROWS * COLS

def render_grid(results):
    # create empty grid
    grid = [["" for _ in range(COLS)] for _ in range(ROWS)]
    # fill column-major: col0 row0..row5 then col1 row0..row5 ...
    idx = 0
    for r in results[-CELLS:]:  # keep last CELLS entries
        col = idx // ROWS
        row = idx % ROWS
        grid[row][col] = r
        idx += 1
        if idx >= CELLS:
            break

    # render with Streamlit columns
    # We'll build rows, each row has COLS columns
    for row in range(ROWS):
        row_cols = st.columns(COLS)
        for col in range(COLS):
            val = grid[row][col]
            color = "#1f2937"  # default dark (empty)
            text = ""
            if val == "莊":
                color = "#ef4444"  # red
                text = ""
            elif val == "閒":
                color = "#3b82f6"  # blue
                text = ""
            elif val == "和":
                color = "#10b981"  # green
                text = ""
            elif val == "超6":
                color = "#fb923c"  # orange (淡橘)
                text = "6"
            # small square HTML
            cell_html = f"""
            <div style="
                width:34px; height:34px; border-radius:6px; background:{color};
                display:flex; align-items:center; justify-content:center; color:white;
                font-weight:700; margin:3px auto;">
                <span style="font-size:14px">{text}</span>
            </div>
            """
            row_cols[col].markdown(cell_html, unsafe_allow_html=True)

# -------------------------
# analysis trigger
# -------------------------
if analyze:
    pred, message = combine_prediction(st.session_state.results)
    if pred is None:
        st.warning(message)
    else:
        if pred == "觀望":
            st.info("💡 綜合分析建議：觀望（不明確）")
            st.write(message)
        else:
            label = "莊" if pred == "莊" else "閒"
            st.success(f"💡 綜合分析建議：建議押 **{label}**")
            st.write(message)

# --- render grid ---
st.markdown("**格盤顯示（6×12）**")
render_grid(st.session_state.results)

# --- quick stats ---
if st.session_state.results:
    total = len(st.session_state.results)
    super6_count = st.session_state.results.count("超6")
    st.write(f"總局數：{total}  ｜  莊（含超6）：{st.session_state.results.count('莊') + super6_count}（超6：{super6_count}）  ｜  閒：{st.session_state.results.count('閒')}  ｜  和：{st.session_state.results.count('和')}")
else:
    st.write("目前尚無任何紀錄，請輸入。")
