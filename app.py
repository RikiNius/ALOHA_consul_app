import streamlit as st
import datetime

# --- 設定 ---
st.set_page_config(page_title="UTokyo Mentoring Base", layout="wide")

# --- マスタデータ（定数） ---
STANDARD_ADVICE = {
    'custom': '（自由入力）',
    'math_partial': '【数学】完答より部分点を狙う記述力の強化',
    'eng_speed': '【英語】要約問題でのロジック把握とスピード向上',
    'eng_listen': '【英語】リスニングは毎日実施（シャドーイング）',
    'jp_classic': '【国語】古文単語・文法の基礎抜け漏れチェック',
    'sci_basic': '【理科】標準問題での計算ミスをゼロにする',
    'soc_flow': '【社会】用語暗記より歴史の流れ・因果関係の理解',
    'past_exam': '【過去問】解くだけでなく復習に3倍の時間をかける'
}

SUBJECTS = {
    '理系': ['英語', '数学(理系)', '国語', '物理', '化学', '生物', '地学', '社会'],
    '文系': ['英語', '数学(文系)', '国語', '世界史', '日本史', '地理', '倫政', '理科基礎']
}

# --- ステート管理（アクションリストの保持） ---
if 'actions' not in st.session_state:
    st.session_state.actions = [
        {'subject': '英語', 'priority': '高', 'standardAdvice': 'eng_listen', 'specificTask': '鉄壁 Section 1-5', 'deadline': '次回まで'}
    ]

# ヘルパー関数: アクション追加
def add_action():
    initial_subject = SUBJECTS[st.session_state.get('stream', '理系')][0]
    st.session_state.actions.append({
        'subject': initial_subject,
        'priority': '中',
        'standardAdvice': 'custom',
        'specificTask': '',
        'deadline': '1週間後'
    })

# ヘルパー関数: アクション削除
def remove_action(index):
    st.session_state.actions.pop(index)

# --- UI構築 ---

st.title("🎓 UTokyo Mentoring Base")
st.markdown("東大志望者向け面談シート作成ツール")

# タブで「編集」と「プレビュー」を切り替え
tab_edit, tab_preview = st.tabs(["✏️ 編集モード", "📄 レポートプレビュー"])

# ==========================================
# 編集タブ
# ==========================================
with tab_edit:
    # 1. 基本情報
    with st.container():
        st.subheader("1. 基本情報")
        col1, col2 = st.columns(2)
        with col1:
            mentor_name = st.text_input("担当メンター名", placeholder="東大 太郎")
            student_name = st.text_input("生徒氏名", placeholder="受験 花子")
            stream = st.radio("文理選択", ["理系", "文系"], horizontal=True, key='stream')
        
        with col2:
            date = st.date_input("実施日", datetime.date.today())
            grade = st.selectbox("学年", ["高3", "高2", "高1", "既卒"])
            default_target = "理科一類" if stream == "理系" else "文科一類"
            target = st.text_input("志望科類", value=default_target)

    st.divider()

    # 2. 模試・成績
    with st.container():
        st.subheader("2. 模試・現状分析")
        exam_name = st.text_input("参照模試名", placeholder="例: 第1回東大実戦模試")
        
        sc_cols = st.columns(5)
        with sc_cols[0]:
            eng_score = st.text_input("英語", placeholder="--")
        with sc_cols[1]:
            math_score = st.text_input("数学", placeholder="--")
        with sc_cols[2]:
            jp_score = st.text_input("国語", placeholder="--")
        
        if stream == "理系":
            with sc_cols[3]:
                sci1_score = st.text_input("理科①", placeholder="物理")
            with sc_cols[4]:
                sci2_score = st.text_input("理科②", placeholder="化学")
            soc1_score, soc2_score = "-", "-"
        else:
            with sc_cols[3]:
                soc1_score = st.text_input("社会①", placeholder="世史")
            with sc_cols[4]:
                soc2_score = st.text_input("社会②", placeholder="地理")
            sci1_score, sci2_score = "-", "-"
            
        current_issue = st.text_area("課題認識（定性コメント）", placeholder="例: 数学の計算スピード不足。古文単語の抜け。", height=80)

    st.divider()

    # 3. ネクストアクション（動的フォーム）
    with st.container():
        st.subheader("3. ネクストアクション")
        
        # 各アクションの表示
        for i, action in enumerate(st.session_state.actions):
            with st.expander(f"アクション #{i+1} : {action['subject']}", expanded=True):
                c1, c2, c3 = st.columns([2, 2, 2])
                
                # 科目選択
                current_subj_list = SUBJECTS[stream]
                subj_index = 0
                if action['subject'] in current_subj_list:
                    subj_index = current_subj_list.index(action['subject'])
                
                with c1:
                    new_subj = st.selectbox("教科", current_subj_list, index=subj_index, key=f"subj_{i}")
                    st.session_state.actions[i]['subject'] = new_subj
                
                with c2:
                    prio_opts = ["高", "中", "低"]
                    prio_index = prio_opts.index(action['priority'])
                    new_prio = st.selectbox("優先度", prio_opts, index=prio_index, key=f"prio_{i}")
                    st.session_state.actions[i]['priority'] = new_prio

                with c3:
                    new_deadline = st.text_input("期限", value=action['deadline'], key=f"dead_{i}")
                    st.session_state.actions[i]['deadline'] = new_deadline

                # アドバイスの型
                adv_keys = list(STANDARD_ADVICE.keys())
                adv_index = 0
                if action['standardAdvice'] in adv_keys:
                    adv_index = adv_keys.index(action['standardAdvice'])
                
                new_adv = st.selectbox(
                    "★ 指導の型（アドバイス）", 
                    options=adv_keys, 
                    format_func=lambda x: STANDARD_ADVICE[x], 
                    index=adv_index, 
                    key=f"adv_{i}"
                )
                st.session_state.actions[i]['standardAdvice'] = new_adv

                # 具体タスク
                new_task = st.text_input("具体的タスク", value=action['specificTask'], key=f"task_{i}", placeholder="例: 鉄壁Section5を3周")
                st.session_state.actions[i]['specificTask'] = new_task
                
                # 削除ボタン
                if st.button("🗑️ このアクションを削除", key=f"del_{i}"):
                    remove_action(i)
                    st.rerun() # 即時反映のためリロード

        # 追加ボタン
        if st.button("➕ アクションを追加する", type="primary"):
            add_action()
            st.rerun()

# ==========================================
# プレビュータブ
# ==========================================
with tab_preview:
    st.subheader("📋 面談レポート")
    st.info("以下のテキストをコピーして、LINEやSlackで生徒に送信してください。")

    # テキスト生成ロジック
    report_text = f"【東大志望者面談シート】\n"
    report_text += f"日付: {date.strftime('%Y/%m/%d')} / 担当: {mentor_name}\n"
    report_text += f"生徒: {student_name} ({grade}) -> 志望: {target}\n\n"
    
    report_text += f"■ 現状分析・模試結果 ({exam_name})\n"
    report_text += f"英:{eng_score} / 数:{math_score} / 国:{jp_score}\n"
    if stream == "理系":
        report_text += f"理1:{sci1_score} / 理2:{sci2_score}\n"
    else:
        report_text += f"社1:{soc1_score} / 社2:{soc2_score}\n"
    
    report_text += f"\n課題認識: {current_issue}\n\n"
    report_text += f"■ ネクストアクション\n"
    
    for idx, act in enumerate(st.session_state.actions):
        advice_text = STANDARD_ADVICE.get(act['standardAdvice'], "")
        if act['standardAdvice'] == 'custom':
            advice_text = "特になし"
            
        report_text += f"{idx+1}. 【{act['subject']}】(優先度:{act['priority']})\n"
        report_text += f"   タスク: {act['specificTask']}\n"
        report_text += f"   ポイント: {advice_text}\n"
        report_text += f"   期限: {act['deadline']}\n"

    # コピー用コードブロック表示
    st.code(report_text, language="text")
    
    # プレビュー用の見た目（オプション）
    with st.expander("詳細プレビューを確認する"):
        st.write(report_text)
