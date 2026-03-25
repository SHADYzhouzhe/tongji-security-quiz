import streamlit as st
import random
import pandas as pd
import os
import datetime
import base64

# ==========================================
# 0. 页面基础配置
# ==========================================
st.set_page_config(page_title="国安有我 青春护航", page_icon="🛡️", layout="centered")


# ==========================================
# 1. 核心功能：修改答题背景
# ==========================================
# 替换背景的核心在于使用 CSS 样式注入。这里我为你写好了一个函数。
def set_background(image_file):
    try:
        with open(image_file, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode()
        # 这里的 CSS 将把背景图应用到整个网页，并且设置半透明的白色遮罩让文字更清晰
        css = f"""
        <style>
        .stApp {{
            background-image: url(data:image/jpeg;base64,{encoded_string});
            background-size: cover;
            background-attachment: fixed;
        }}
        /* 给主要内容区域加一个半透明白色底板，防止背景图太花看不清字 */
        .stApp > header {{
            background-color: transparent;
        }}
        .block-container {{
            background-color: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            padding: 2rem;
            margin-top: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    except FileNotFoundError:
        # 如果找不到背景图 bg.jpg，就只用简单的纯色背景
        st.markdown("""
        <style>
        .stApp {
            background-color: #f0f4f8; /* 浅蓝灰色背景 */
        }
        </style>
        """, unsafe_allow_html=True)


# 调用更换背景的函数 (确保你的文件夹里有一张 bg.jpg，如果没有它会自动变成浅蓝灰色)
set_background("bg.jpg")

# ==========================================
# 2. 侧边栏：加入二维码大屏展示
# ==========================================
with st.sidebar:
    st.header("📱 扫码手机参与")
    st.write("欢迎来到同济大学测绘与地理信息学院展位！")
    try:
        # 读取同文件夹下的二维码图片
        st.image("qrcode.png", caption="打开微信扫一扫", use_container_width=True)
    except FileNotFoundError:
        st.info("💡 提示：将生成的二维码命名为 qrcode.png 放在同文件夹下，这里就会显示出来供大家扫码啦！")

    st.divider()
    st.write("🌟 **活动规则：**")
    st.write("1. 从 120 题中随机抽取 20 题")
    st.write("2. 满分 100 分，按分数和速度排名")
    st.write("3. 一等奖 1 名，二等奖 3 名，三等奖 5 名")


# ==========================================
# 3. 读取 Excel 题库
# ==========================================
@st.cache_data
def load_question_bank():
    questions = []
    try:
        df = pd.read_excel("questions.xlsx", engine="openpyxl")
        for index, row in df.iterrows():
            options = [str(row['选项A']), str(row['选项B']), str(row['选项C']), str(row['选项D'])]
            options = [opt for opt in options if opt != 'nan' and opt.strip() != '']
            questions.append({
                "id": index,
                "question": str(row['题目']),
                "options": options,
                "answer": str(row['正确答案']).strip()
            })
        return questions
    except Exception as e:
        st.error(f"⚠️ 读取题库失败：{e}")
        return []


all_questions = load_question_bank()

# ==========================================
# 4. 抽题与答题逻辑
# ==========================================
if all_questions:
    if 'selected_questions' not in st.session_state:
        sample_size = min(20, len(all_questions))
        st.session_state.selected_questions = random.sample(all_questions, sample_size)
    if 'has_submitted' not in st.session_state:
        st.session_state.has_submitted = False

st.title("🛡️ “国安有我 青春护航”知识挑战赛")

if not all_questions:
    st.warning("请确保 `questions.xlsx` 已经放在正确的位置！")
else:
    tab1, tab2 = st.tabs(["📝 参与答题", "🏆 英雄榜 (实时排名)"])

    with tab1:
        if not st.session_state.has_submitted:
            st.info(f"本次挑战共 {len(st.session_state.selected_questions)} 道题，由系统为您随机生成。")

            with st.form("quiz_form"):
                user_name = st.text_input("👤 请在此输入您的姓名（用于领奖）：", max_chars=10)
                st.divider()

                user_answers = []
                for i, q in enumerate(st.session_state.selected_questions):
                    st.markdown(f"**{i + 1}. {q['question']}**")
                    shuffled_options = q["options"].copy()
                    random.seed(q['id'])
                    random.shuffle(shuffled_options)

                    ans = st.radio(f"请选择", shuffled_options, key=f"q_{i}", index=None, label_visibility="collapsed")
                    user_answers.append(ans)
                    st.markdown("---")

                submitted = st.form_submit_button("✅ 提交答卷", type="primary", use_container_width=True)

            if submitted:
                if not user_name.strip():
                    st.error("⚠️ 必须填写姓名才能交卷哦！")
                elif None in user_answers:
                    st.warning("⚠️ 还有题目未作答，请检查一遍！")
                else:
                    score = 0
                    points_per_q = 100 / len(st.session_state.selected_questions)
                    for i, q in enumerate(st.session_state.selected_questions):
                        if user_answers[i] == q["answer"]:
                            score += points_per_q

                    record = {
                        "姓名": user_name,
                        "得分": int(score),
                        "交卷时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    df_new = pd.DataFrame([record])

                    if not os.path.exists("results.csv"):
                        df_new.to_csv("results.csv", index=False, encoding="utf-8-sig")
                    else:
                        df_new.to_csv("results.csv", mode='a', header=False, index=False, encoding="utf-8-sig")

                    st.session_state.has_submitted = True
                    st.session_state.final_score = int(score)
                    st.rerun()

        else:
            st.success("🎉 交卷成功！您的成绩已安全录入系统。")
            st.metric(label="最终得分", value=f"{st.session_state.final_score} 分")
            st.info("👉 请点击上方的【🏆 英雄榜】查看您目前的排名！")

    with tab2:
        st.header("🏆 荣誉排行榜")
        st.write("系统会自动根据 **分数优先、时间优先** 的原则进行实时排名。")

        if os.path.exists("results.csv"):
            df_results = pd.read_csv("results.csv")
            df_sorted = df_results.sort_values(by=["得分", "交卷时间"], ascending=[False, True]).reset_index(drop=True)

            prizes = []
            for index in range(len(df_sorted)):
                if index == 0:
                    prizes.append("🥇 一等奖")
                elif 1 <= index <= 3:
                    prizes.append("🥈 二等奖")
                elif 4 <= index <= 8:
                    prizes.append("🥉 三等奖")
                else:
                    prizes.append("🎖️ 参与奖")

            df_sorted["获得奖项"] = prizes
            # 格式化表格显示
            st.dataframe(df_sorted, use_container_width=True, hide_index=True)
        else:
            st.info("🧐 榜单空空如也，快去【参与答题】抢首杀吧！")
