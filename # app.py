# app.py
import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd

# --------------------------
# 設定
# --------------------------
SCORE_FILE = "scores.json"
ADMIN_PASSWORD = "xinadmin"  # 管理後台密碼（你可以改成你要的）

# --------------------------
# 題庫（你已最終確認的題目）
# --------------------------
QUESTIONS = [
    {
        "q": "哪一個對我來說比較重要？",
        "options": ["愛情", "金錢", "健康", "友情"],
        "answer": "金錢"
    },
    {
        "q": "你覺得我會因為什麼最容易生氣？",
        "options": ["吵醒我", "不回訊息", "亂答非題", "說我矮"],
        "answer": "吵醒我"
    },
    {
        "q": "我最愛在什麼時候睡覺？",
        "options": ["一早睡", "下午睡", "半夜睡", "看心情"],
        "answer": "一早睡"
    },
    {
        "q": "我喜歡怎樣的人？",
        "options": ["直白", "活潑", "冷靜", "有主見"],
        "answer": "直白"
    },
    {
        "q": "我討厭別人怎樣？",
        "options": ["碎念", "太黏", "不讀不回", "亂約"],
        "answer": "太黏"
    },
    {
        "q": "我覺得哪一種聊天方式最舒服？",
        "options": ["慢慢回也沒差", "想到什麼就講什麼", "一次打一大串", "語音派"],
        "answer": "想到什麼就講什麼"
    },
    {
        "q": "我覺得雨天應該要做什麼？",
        "options": ["出門散步", "在家耍廢", "看電影", "睡覺"],
        "answer": "在家耍廢"
    },
    {
        "q": "如果我中了一點小錢，我會？",
        "options": ["大吃一頓犒賞自己", "出去玩一趟", "先存起來", "買想買很久的東西"],
        "answer": "大吃一頓犒賞自己"
    },
    {
        "q": "你最符合哪種生活步調？",
        "options": ["早起神清氣爽型", "熬夜靈感爆棚型", "隨便啦看心情型", "完全看朋友揪型"],
        "answer": "隨便啦看心情型"
    },
    {
        "q": "你最常遲到的理由？",
        "options": ["想買早餐", "睡過頭", "找不到東西", "塞車"],
        "answer": "睡過頭"
    }
]
TOTAL = len(QUESTIONS)


# --------------------------
# 檔案 I/O：讀/寫 scores.json（以 list 儲存多筆紀錄）
# --------------------------
def load_scores():
    if not os.path.exists(SCORE_FILE):
        return []
    try:
        with open(SCORE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                # 如果不是 list（舊格式），嘗試轉換
                return data
    except Exception:
        return []

def save_score_record(record):
    records = load_scores()
    records.append(record)
    with open(SCORE_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


# --------------------------
# App UI
# --------------------------
st.set_page_config(page_title="友誼大考驗", page_icon="🔥", layout="centered")
st.title("🔥 友誼大考驗 🔥")
st.write("先填名字，知道誰是真正懂我的人。")

# 初始化 session state
if "name" not in st.session_state:
    st.session_state.name = ""
if "page" not in st.session_state:
    st.session_state.page = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}  # {index: choice}
if "started" not in st.session_state:
    st.session_state.started = False

# --------------------------
# 名字輸入
# --------------------------
if not st.session_state.started:
    name = st.text_input("你的名字：", value=st.session_state.name)
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("開始測驗"):
            if name.strip() == "":
                st.warning("名字不能空白啦！")
            else:
                st.session_state.name = name.strip()
                st.session_state.started = True
                st.experimental_rerun()
    with col2:
        if st.button("稍後再玩"):
            st.info("好喔，等你想玩再開。")
    st.stop()

# --------------------------
# 答題頁面（單題一頁）
# --------------------------
page = st.session_state.page

if page < TOTAL:
    q = QUESTIONS[page]
    st.subheader(f"第 {page+1} 題 / {TOTAL}")
    st.write(q["q"])

    # radio 預設為上次選的答案（若有）
    prev_choice = st.session_state.answers.get(str(page))
    choice = st.radio("選項：", q["options"], index=(q["options"].index(prev_choice) if prev_choice in q["options"] else 0))

    cols = st.columns([1, 1, 1])
    with cols[0]:
        if st.button("上一題"):
            if page > 0:
                st.session_state.answers[str(page)] = choice
                st.session_state.page -= 1
                st.experimental_rerun()
    with cols[1]:
        if st.button("下一題"):
            st.session_state.answers[str(page)] = choice
            st.session_state.page += 1
            st.experimental_rerun()
    with cols[2]:
        if st.button("直接跳到最後"):
            st.session_state.answers[str(page)] = choice
            st.session_state.page = TOTAL
            st.experimental_rerun()

    st.write("---")
    st.write("若想改答案，按「上一題」回去修改。")
else:
    # 計分
    score = 0
    details = []
    for i, q in enumerate(QUESTIONS):
        user_answer = st.session_state.answers.get(str(i), "")
        correct = q["answer"]
        is_correct = (user_answer == correct)
        if is_correct:
            score += 1
        details.append({
            "index": i + 1,
            "question": q["q"],
            "your_answer": user_answer,
            "correct_answer": correct,
            "is_correct": is_correct
        })

    st.success(f"🎉 {st.session_state.name} 的最終得分：{score} / {TOTAL}")
    st.write("下面會把你的作答紀錄存起來（本機檔案：scores.json）")

    # 儲存紀錄（包含 timestamp）
    record = {
        "name": st.session_state.name,
        "score": score,
        "total": TOTAL,
        "answers": st.session_state.answers,
        "details": details,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_score_record(record)

    # 顯示個人逐題結果
    st.subheader("你的逐題結果")
    for d in details:
        icon = "✅" if d["is_correct"] else "❌"
        st.write(f"{icon} 第{d['index']}題：{d['question']}")
        st.write(f"> 你：{d['your_answer']}  / 正解：{d['correct_answer']}")
    st.write("---")

    # 顯示排行榜（依 score 排序，同分則時間較早者在前）
    st.subheader("📊 排行榜（最近紀錄）")
    all_records = load_scores()
    # 取最近每個人最高分（若要多次參賽紀錄都顯示，可修改這邊）
    df = pd.DataFrame(all_records)
    if not df.empty:
        # 排行邏輯：先取每位最新（或最高）分數，我這裡示範以「最高分」為排名依據；同分則以最新時間靠前
        best = df.sort_values(["name", "score", "timestamp"], ascending=[True, False, False]) \
                 .drop_duplicates(subset=["name"], keep="first")
        ranking = best.sort_values(["score", "timestamp"], ascending=[False, False])
        ranking = ranking.reset_index(drop=True)
        for idx, row in ranking.iterrows():
            st.write(f"**{idx+1}. {row['name']} — {row['score']} 分** （{row['timestamp']}）")
    else:
        st.write("目前還沒有任何紀錄。")

    st.write("---")
    if st.button("重新開始測驗"):
        st.session_state.page = 0
        st.session_state.answers = {}
        st.session_state.started = False
        st.session_state.name = ""
        st.experimental_rerun()

# --------------------------
# 管理後台（放在最下方） — 密碼可看所有紀錄、匯出 CSV
# --------------------------
st.sidebar.title("管理後台")
pw = st.sidebar.text_input("管理密碼：", type="password")
if st.sidebar.button("登入後台"):
    if pw == ADMIN_PASSWORD:
        st.sidebar.success("已登入管理後台")
        st.session_state.admin = True
    else:
        st.sidebar.error("密碼錯誤")
        st.session_state.admin = False

if st.session_state.get("admin", False):
    st.sidebar.markdown("**管理選項**")
    records = load_scores()
    if records:
        df_all = pd.DataFrame(records)
        # 展示表格
        st.sidebar.write("所有紀錄預覽（最新 10 筆）")
        st.sidebar.dataframe(df_all.sort_values("timestamp", ascending=False).head(10))

        # 匯出 CSV
        csv = df_all.to_csv(index=False, encoding="utf-8-sig")
        st.sidebar.download_button("下載所有紀錄 CSV", data=csv, file_name="scores_all.csv", mime="text/csv")

        # 檢視單一使用者細節
        st.sidebar.write("---")
        st.sidebar.write("查看某人紀錄")
        names = sorted(list({r["name"] for r in records}))
        sel_name = st.sidebar.selectbox("選擇名字：", ["(選擇)"] + names)
        if sel_name != "(選擇)":
            sub = [r for r in records if r["name"] == sel_name]
            if sub:
                st.sidebar.write(f"共 {len(sub)} 筆紀錄（由近到遠）")
                sub_sorted = sorted(sub, key=lambda x: x["timestamp"], reverse=True)
                for s in sub_sorted:
                    st.sidebar.write(f"- {s['timestamp']} — 分數：{s['score']} / {s['total']}")
                    st.sidebar.write(f"  答案：{s['answers']}")
            else:
                st.sidebar.write("沒有紀錄。")
    else:
        st.sidebar.write("目前沒有紀錄。")
