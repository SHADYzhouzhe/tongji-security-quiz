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
def set_background(image_file):
    try:
        with open(image_file, "rb") as f:
            encoded_string = base64.b64encode(f.read()).decode()
        css = f"""
        <style>
        .stApp {{
            background-image: url(data:image/jpeg;base64,{encoded_string});
            background-size: cover;
            background-attachment: fixed;
        }}
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
        st.markdown("""
        <style>
        .stApp {
            background-color: #f0f4f8; 
        }
        </style>
        """, unsafe_allow_html=True)

set_background("bg.jpg")

# ==========================================
# 2. 侧边栏：加入二维码大屏展示
# ==========================================
with st.sidebar:
    st.header("📱 扫码手机参与")
    st.write("欢迎来到同济大学测绘与地理信息学院展位！")
    
    if os.path.exists("qrcode.png"):
        st.image("qrcode.png", caption="打开微信扫一扫", use_container_width=True)
    else:
        st.info("💡 提示：正在等待二维码图片上线...")
    
    st.divider()
    st.write("🌟 **活动规则：**")
    st.write("1. 从 120 题中随机抽取 20 题")
    st.write("2. 满分100分，按分数区间获取奖品")
    st.write("3. 🎁 **奖项设置**：全对一等奖 (2名)，错一题二等奖 (3名)，其余三等奖 (19名)。名额发完自动向后顺延！")

# ==========================================
# 3. 读取 Excel 题库
# ==========================================
@st.cache_data
def load_question_bank():
    questions = []
    try:
        # 指定 engine="openpyxl" 确保读取真正的 xlsx 文件
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
    st.warning("请确保 `questions.xlsx` 已经放在正确的位置，并且是真正的 Excel 格式！")
else:
    tab1, tab2 = st.tabs(["📝 参与答题", "🏆 英雄榜 (实时排名)"])

    with tab1:
        # 如果还没交卷，显示答题表单
        if not st.session_state.has_submitted:
            st.info(f"本次挑战共 {len(st.session_state.selected_questions)} 道题，由系统为您随机生成。")
            
            with st.form("quiz_form"):
                user_name = st.text_input("👤 请在此输入您的姓名（用于领奖）：", max_chars=10)
                st.divider()
                
                user_answers = []
                for i, q in enumerate(st.session_state.selected_questions):
                    # 自动切除可能附带的双重序号
                    clean_question = q['question'].split(".", 1)[-1].strip() if "." in q['question'] else q['question']
                    st.markdown(f"**{i+1}. {clean_question}**")
                    
                    shuffled_options = q["options"].copy()
                    random.seed(q['id']) 
                    random.shuffle(shuffled_options)
                    
                    ans = st.radio("请选择", shuffled_options, key=f"q_{i}", index=None, label_visibility="collapsed")
                    user_answers.append(ans)
                    st.markdown("---")
                    
                submitted = st.form_submit_button("✅ 提交答卷", type="primary", use_container_width=True)

            if submitted:
                if not user_name.strip():
                    st.error("⚠️ 必须填写姓名才能交卷哦！")
                elif None in user_answers:
                    st.warning("⚠️ 还有题目未作答，请检查一遍！")
                else:
                    # ===== 查重逻辑开始 =====
                    if os.path.exists("results.csv"):
                        df_existing = pd.read_csv("results.csv", encoding="utf-8-sig")
                        if user_name in df_existing["姓名"].values:
                            st.error(f"⚠️ 提示：系统记录显示【{user_name}】已经参与过本次答题，请勿重复提交！将机会留给其他同学吧~")
                            st.stop()
                    # ===== 查重逻辑结束 =====
                    
                    # 计分
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

        # 如果已经交卷，显示最终成绩
        else:
            st.success("🎉 交卷成功！您的成绩已安全录入系统。")
            st.metric(label="最终得分", value=f"{st.session_state.get('final_score', 0)} 分")
            st.info("👉 请点击上方的【🏆 英雄榜】查看您目前的排名和奖项！")

    with tab2:
        st.header("🏆 荣誉排行榜")
        st.write("系统会自动根据 **分数优先、时间优先** 的原则进行实时排名，并按奖品余量自动顺延奖项。")
        
        if os.path.exists("results.csv"):
            df_results = pd.read_csv("results.csv", encoding="utf-8-sig")
            df_sorted = df_results.sort_values(by=["得分", "交卷时间"], ascending=[False, True]).reset_index(drop=True)
            
            prizes = []
            
            # 初始化各奖项名额
            quota_1 = 2   # 一等奖名额
            quota_2 = 3   # 二等奖名额
            quota_3 = 19  # 三等奖名额
            
            for index, row in df_sorted.iterrows():
                score = row["得分"]
                
                # 1. 确定选手成绩对应的“理论应得奖项”级别
                # (满分100，20题每题5分，错一题即得95分)
                if score == 100:
                    intended_level = 1
                elif score == 95:
                    intended_level = 2
                else:
                    intended_level = 3
                    
                # 2. 根据名额和顺延规则实际分配奖项
                if intended_level == 1 and quota_1 > 0:
                    prizes.append("🥇 一等奖")
                    quota_1 -= 1
                elif intended_level <= 2 and quota_2 > 0:
                    # 如果是一等奖但名额不够，或者本身就是二等奖，且二等奖有名额
                    prizes.append("🥈 二等奖")
                    quota_2 -= 1
                elif intended_level <= 3 and quota_3 > 0:
                    # 如果前两个奖项名额都不够，或者本身就是三等奖，且三等奖有名额
                    prizes.append("🥉 三等奖")
                    quota_3 -= 1
                else:
                    # 所有对应的奖池名额都耗尽了
                    prizes.append("🎖️ 参与奖 (名额已满)")
                    
            df_sorted["获得奖项"] = prizes
            st.dataframe(df_sorted, use_container_width=True, hide_index=True)
        else:
            st.info("🧐 榜单空空如也，快去【参与答题】抢首杀吧！")
