import streamlit as st
import pandas as pd

st.set_page_config(page_title="百家樂推測助手", page_icon="🎲", layout="centered")
st.title("🎲 百家樂推測助手）")
st.markdown("輸入莊/閒/和，後台綜合大路＋大眼仔＋小路＋蟑螂路，僅輸出最終推測（不顯示路單）。")

# init
if "results" not in st.session_state:
    st.session_state.results = []

# input buttons
col1, col2, col3, col4 = st.columns([1,1,1,1])
with col1:
    if st.button("莊"):
        st.session_state.results.append("莊")
with col2:
    if st.button("閒"):
        st.session_state.results.append("閒")
with col3:
    if st.button("和"):
        st.session_state.results.append("和")
with col4:
    if st.button("倒退"):
        if st.session_state.results:
            st.session_state.results.pop()

# controls
colA, colB = st.columns([1,1])
with colA:
    analyze = st.button("開始推測")
with colB:
    if st.button("清空"):
        st.session_state.results = []

# show basic record (compact)
st.markdown("**當前紀錄（前 80 局）**：" + (" → ".join(st.session_state.results[-80:]) if st.session_state.results else "無"))

# -------------------------
# helper: build simplified big road columns
# -------------------------
def build_big_road_columns(results):
    """
    簡化大路生成：
    - 忽略 '和'（tie）在建立列的邏輯（但保留在紀錄中）
    - 如果當前結果和上一次非 tie 結果相同 -> 同列 append
    - 否則 -> 新列開始
    回傳 columns（list of lists），每列為同一方的連勝序列
    """
    cols = []
    last_non_tie = None
    for r in results:
        if r == "和":
            # 不改變列結構（簡化），實際大路會在該格標和，但我們不顯示
            continue
        if last_non_tie is None:
            cols.append([r])
            last_non_tie = r
        else:
            if r == last_non_tie:
                # append to last column
                cols[-1].append(r)
            else:
                # new column
                cols.append([r])
                last_non_tie = r
    return cols

# -------------------------
# helper: derive red/blue for big-eye / small-road / cockroach (simplified)
# -------------------------
def derive_subroad_colors(columns):
    """
    使用簡化判定：
    - big eye (大眼仔): compare col i vs col i-1 (if length equal -> red, else blue)
    - small road (小路): compare col i vs col i-2 (if length equal -> red, else blue)
    - cockroach (蟑螂路): compare col i vs col i-3 (if length equal -> red, else blue)
    回傳三個 lists of 'red'/'blue'
    """
    lens = [len(c) for c in columns]
    n = len(lens)
    bigeye = []
    small = []
    cock = []
    # big eye starts from index 1
    for i in range(1, n):
        bigeye.append("red" if lens[i] == lens[i-1] else "blue")
    # small road starts from index 2
    for i in range(2, n):
        small.append("red" if lens[i] == lens[i-2] else "blue")
    # cockroach starts from index 3
    for i in range(3, n):
        cock.append("red" if lens[i] == lens[i-3] else "blue")
    return bigeye, small, cock

# -------------------------
# helper: combine results into a single suggestion
# -------------------------
def combine_prediction(results):
    # if no non-tie entries, can't predict
    non_tie = [r for r in results if r != "和"]
    if not non_tie:
        return None, "資料不足（尚未有莊或閒局）"

    # counts
    total = len(results)
    banker = results.count("莊")
    player = results.count("閒")
    tie = results.count("和")

    # build big road
    cols = build_big_road_columns(results)

    # derive subroad colors
    bigeye, small, cock = derive_subroad_colors(cols)

    # count reds / blues
    red_count = sum(1 for x in (bigeye + small + cock) if x == "red")
    blue_count = sum(1 for x in (bigeye + small + cock) if x == "blue")
    total_checks = red_count + blue_count

    # fallback: if no subroad checks (too few columns), use simple frequency as weak signal
    if total_checks == 0:
        # weak confidence based on simple freq diff
        if banker > player:
            return "莊", f"基礎頻率偏莊（莊 {banker} vs 閒 {player}），信心 {min(60, 50 + (banker-player)*5)}%"
        elif player > banker:
            return "閒", f"基礎頻率偏閒（閒 {player} vs 莊 {banker}），信心 {min(60, 50 + (player-banker)*5)}%"
        else:
            return "觀望", "莊閒頻率相等，建議觀望"

    # 主流派（順勢）：多紅 -> 順勢（延續最後一局） ; 多藍 -> 逆勢（反向）
    stability = int(round((red_count / total_checks) * 100)) if total_checks>0 else 0

    # determine last non-tie result
    last_non_tie = None
    for r in reversed(results):
        if r != "和":
            last_non_tie = r
            break

    if red_count > blue_count:
        # 順勢：延續最後一局
        predicted = last_non_tie
        note = f"多數副路顯示紅（{red_count}紅 / {blue_count}藍），傾向順勢延續"
        confidence = int(min(95, 50 + (stability-50)//1 + abs(banker-player)))  # combine factors
    elif blue_count > red_count:
        # 逆勢：切換
        predicted = "莊" if last_non_tie=="閒" else "閒"
        note = f"多數副路顯示藍（{blue_count}藍 / {red_count}紅），傾向反轉"
        confidence = int(min(95, 45 + (100-stability)//1 + abs(banker-player)))
    else:
        predicted = "觀望"
        note = f"紅藍相等（{red_count} / {blue_count}），建議觀望"
        confidence = 50

    # slightly boost/dampen confidence based on overall imbalance
    diff = abs(banker - player)
    confidence = min(99, confidence + min(10, diff*2))

    return predicted, f"{note} | 穩定度 {stability}% | 信心指數 {confidence}%"

# -------------------------
# analysis trigger
# -------------------------
if analyze:
    pred, message = combine_prediction(st.session_state.results)
    if pred is None:
        st.warning(message)
    else:
        # produce a concise final line (no road visuals)
        if pred == "觀望":
            st.info("💡 綜合分析建議：觀望（不明確）")
            st.write(message)
        else:
            label = "莊" if pred == "莊" else "閒"
            st.success(f"💡 綜合分析建議：建議押 **{label}**")
            st.write(message)

# always show quick stats for user reference
if st.session_state.results:
    total = len(st.session_state.results)
    st.write(f"總局數：{total}  ｜  莊：{st.session_state.results.count('莊')}  ｜  閒：{st.session_state.results.count('閒')}  ｜  和：{st.session_state.results.count('和')}")
else:
    st.write("目前尚無任何紀錄，請輸入。")
