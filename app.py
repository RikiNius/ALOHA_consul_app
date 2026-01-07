import streamlit as st
import pandas as pd
import datetime
import json

# --- 設定 ---
st.set_page_config(page_title="ALOHA Mentoring Base", layout="wide")

# --- マスタデータ（定数） ---
SUBJECTS = {
    '理系': ['英語', '数学(理系)', '国語', '物理', '化学', '生物'],
    '文系': ['英語', '数学(文系)', '国語', '世界史', '日本史', '地理']
}

# 表示用のラベル変換マップ（二次試験用）
SCORE_LABELS_NIJI = {
    'eng': '英語', 'math': '数学', 'jp': '国語',
    'sci1': '理科①', 'sci2': '理科②',
    'soc1': '社会①', 'soc2': '社会②'
}

# 表示用のラベル変換マップ（共通テスト用）
SCORE_LABELS_KYOTSU = {
    'eng_r': '英語R', 'eng_l': '英語L',
    'math_1': '数IA', 'math_2': '数IIBC',
    'jp': '国語', 'info': '情報',
    # 文系用
    'k_soc1': '社会①', 'k_soc2': '社会②',
    'k_sci_base1': '理科基礎①', 'k_sci_base2': '理科基礎②',
    # 理系用
    'k_sci1': '理科①', 'k_sci2': '理科②'
}

# --- データベース接続 (Google Sheets) ---
try:
    from streamlit_gsheets import GSheetsConnection
    conn = st.connection("gsheets", type=GSheetsConnection)
    DB_MODE = True
except:
    DB_MODE = False

COLUMNS = ["日付", "担当メンター", "生徒氏名", "学年", "文理", "志望科類", "模試名", "課題", "データJSON"]

# データ読み込み関数
def load_data():
    if DB_MODE:
        try:
            df = conn.read(worksheet="logs", ttl=0)
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = None
            return df
        except Exception:
            return pd.DataFrame(columns=COLUMNS)
    else:
        if "demo_data" not in st.session_state:
            st.session_state.demo_data = pd.DataFrame(columns=COLUMNS)
        return st.session_state.demo_data

# データ保存関数
def save_data(new_row_df):
    current_df = load_data()
    if not current_df.empty:
        for col in COLUMNS:
            if col not in current_df.columns:
                current_df[col] = None
    
    updated_df = pd.concat([new_row_df, current_df], ignore_index=True)
    
    if DB_MODE:
        try:
            conn.update(worksheet="logs", data=updated_df)
            return True
        except Exception as e:
            st.error(f"保存エラー: {e}")
            return False
    else:
        st.session_state.demo_data = updated_df
        return True

# --- 初期化関数 (Reset) ---
def init_session_state():
    # アクションリストの初期化（policyを追加）
    if 'actions' not in st.session_state:
        st.session_state.actions = [
            {'subject': '英語', 'priority': '高', 'policy': '', 'specificTask': '鉄壁 Section 1-5', 'deadline': '次回まで'}
        ]

def clear_inputs():
    """入力フォームのリセット処理（値を明示的に空にする）"""
    # テキスト入力系
    text_keys = [
        "in_mentor", "in_student", "in_target", "in_exam", "in_issue",
        # 二次試験
        "in_s_eng", "in_s_math", "in_s_jp", "in_s_sci1", "in_s_sci2", "in_s_soc1", "in_s_soc2",
        # 共通テスト
        "in_k_eng_r", "in_k_eng_l", "in_k_math_1", "in_k_math_2", "in_k_jp", "in_k_info",
        "in_k_soc1", "in_k_soc2", "in_k_sci_base1", "in_k_sci_base2", "in_k_sci1", "in_k_sci2"
    ]
    for key in text_keys:
        if key in st.session_state:
            st.session_state[key] = ""

    # セレクトボックス等の初期化（必要に応じて）
    if "in_grade" in st.session_state:
        st.session_state["in_grade"] = "高3"
    
    # アクションリストの初期化
    st.session_state.actions = [
        {'subject': '英語', 'priority': '高', 'policy': '', 'specificTask': '鉄壁 Section 1-5', 'deadline': '次回まで'}
    ]

init_session_state()

# --- UI構築 ---

st.title("🎓 UTokyo Mentoring Base")

tab_new, tab_search, tab_preview = st.tabs(["📝 新規面談・保存", "🔍 過去ログ検索", "📄 レポート出力"])

# ==========================================
# 1. 新規作成タブ
# ==========================================
with tab_new:
    st.subheader("面談記録の入力")
    
    def add_action(stream_val):
        initial_subject = SUBJECTS[stream_val][0]
        st.session_state.actions.append({
            'subject': initial_subject, 'priority': '中', 'policy': '', 'specificTask': '', 'deadline': '1週間後'
        })
    def remove_action(index):
        st.session_state.actions.pop(index)

    # 入力フォーム
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            mentor_name = st.text_input("担当メンター", key="in_mentor")
            student_name = st.text_input("生徒氏名", key="in_student")
            stream = st.radio("文理", ["理系", "文系"], horizontal=True, key="in_stream")
        with c2:
            date_val = st.date_input("実施日", datetime.date.today(), key="in_date")
            grade = st.selectbox("学年", ["高3", "高2", "高1", "既卒"], key="in_grade")
            default_target = "理科一類" if stream == "理系" else "文科一類"
            target = st.text_input("志望科類", value=default_target, key="in_target")

    st.divider()

    # 模試・課題
    st.caption("成績入力")
    exam_col1, exam_col2 = st.columns([1, 2])
    with exam_col1:
        exam_type = st.radio("模試種別", ["東大二次(本番レベル)", "共通テスト"], key="in_exam_type")
    with exam_col2:
        exam_name = st.text_input("模試名 (例: 第1回東大実戦)", key="in_exam")

    scores = {}
    
    # === 模試入力エリア ===
    if exam_type == "東大二次(本番レベル)":
        sc = st.columns(5)
        with sc[0]: scores['eng'] = st.text_input("英語", key="in_s_eng")
        with sc[1]: scores['math'] = st.text_input("数学", key="in_s_math")
        with sc[2]: scores['jp'] = st.text_input("国語", key="in_s_jp")
        
        if stream == "理系":
            with sc[3]: scores['sci1'] = st.text_input("理科①", key="in_s_sci1")
            with sc[4]: scores['sci2'] = st.text_input("理科②", key="in_s_sci2")
        else:
            with sc[3]: scores['soc1'] = st.text_input("社会①", key="in_s_soc1")
            with sc[4]: scores['soc2'] = st.text_input("社会②", key="in_s_soc2")
    
    else:
        # === 共通テスト ===
        st.markdown("**基礎科目**")
        kc1, kc2, kc3 = st.columns(3)
        with kc1: 
            scores['eng_r'] = st.text_input("英語R", key="in_k_eng_r")
            scores['eng_l'] = st.text_input("英語L", key="in_k_eng_l")
        with kc2:
            scores['math_1'] = st.text_input("数IA", key="in_k_math_1")
            scores['math_2'] = st.text_input("数IIBC", key="in_k_math_2")
        with kc3:
            scores['jp'] = st.text_input("国語", key="in_k_jp")
            scores['info'] = st.text_input("情報", key="in_k_info")
        
        st.markdown("**理科・社会**")
        ks1, ks2, ks3, ks4 = st.columns(4)
        
        if stream == "文系":
            with ks1: scores['k_soc1'] = st.text_input("社会①", key="in_k_soc1")
            with ks2: scores['k_soc2'] = st.text_input("社会②", key="in_k_soc2")
            with ks3: scores['k_sci_base1'] = st.text_input("理科基礎①", key="in_k_sci_base1")
            with ks4: scores['k_sci_base2'] = st.text_input("理科基礎②", key="in_k_sci_base2")
        else:
            with ks1: scores['k_soc1'] = st.text_input("社会①", key="in_k_soc1_r")
            with ks2: scores['k_soc2'] = st.text_input("社会②", key="in_k_soc2_r")
            with ks3: scores['k_sci1'] = st.text_input("理科①", key="in_k_sci1")
            with ks4: scores['k_sci2'] = st.text_input("理科②", key="in_k_sci2")

    current_issue = st.text_area("課題認識", key="in_issue")

    st.divider()

    # アクション
    st.caption("ネクストアクション")
    for i, action in enumerate(st.session_state.actions):
        with st.expander(f"Action {i+1}: {action['subject']}", expanded=True):
            # 1行目: 教科・優先度・期限
            ac1, ac2, ac3 = st.columns([2, 1, 2])
            with ac1:
                subj_list = SUBJECTS[stream]
                s_idx = subj_list.index(action['subject']) if action['subject'] in subj_list else 0
                st.session_state.actions[i]['subject'] = st.selectbox("教科", subj_list, index=s_idx, key=f"s_{i}")
            with ac2:
                p_opts = ["高", "中", "低"]
                curr_p = action.get('priority', "中")
                st.session_state.actions[i]['priority'] = st.selectbox("優先", p_opts, index=p_opts.index(curr_p), key=f"p_{i}")
            with ac3:
                st.session_state.actions[i]['deadline'] = st.text_input("期限", action['deadline'], key=f"d_{i}")
            
            # 2行目: 方針（自由入力）
            st.session_state.actions[i]['policy'] = st.text_input("方針設定", action.get('policy', ''), key=f"pol_{i}", placeholder="例: 部分点を確実に取るための記述強化")

            # 3行目: 具体的タスク
            st.session_state.actions[i]['specificTask'] = st.text_input("具体的タスク", action['specificTask'], key=f"t_{i}", placeholder="例: 鉄壁Section1-5を毎日実施")
            
            if st.button("削除", key=f"del_{i}"):
                remove_action(i)
                st.rerun()
    
    if st.button("＋ アクション追加"):
        add_action(stream)
        st.rerun()

    st.divider()

    # 保存ボタン
    if st.button("💾 この内容を保存する", type="primary"):
        if not student_name:
            st.error("生徒氏名を入力してください")
        else:
            full_data = {
                "mentor": mentor_name,
                "scores": scores,
                "exam_type": exam_type,
                "actions": st.session_state.actions,
                "stream": stream
            }
            new_row = pd.DataFrame([{
                "日付": date_val.strftime('%Y-%m-%d'),
                "担当メンター": mentor_name,
                "生徒氏名": student_name,
                "学年": grade,
                "文理": stream,
                "志望科類": target,
                "模試名": exam_name,
                "課題": current_issue,
                "データJSON": json.dumps(full_data, ensure_ascii=False)
            }])
            
            if save_data(new_row):
                st.success("保存しました！")
                clear_inputs() # フォームをリセット
                st.rerun()
            else:
                if not DB_MODE:
                    st.warning("⚠️ データベース未設定のため、一時保存しました（リロードで消えます）。")
                    clear_inputs()
                    st.rerun()

# ==========================================
# 2. 検索タブ
# ==========================================
with tab_search:
    st.subheader("過去ログ検索")
    
    df = load_data()
    
    if df.empty:
        st.info("まだ保存されたデータはありません。")
    else:
        search_name = st.text_input("生徒名で検索", placeholder="名前の一部を入力")
        
        if search_name:
            if '生徒氏名' in df.columns:
                filtered_df = df[df['生徒氏名'].str.contains(search_name, na=False)]
            else:
                filtered_df = df
        else:
            filtered_df = df

        filtered_df = filtered_df.sort_index(ascending=False)

        display_cols = [c for c in ["日付", "担当メンター", "生徒氏名", "学年", "文理", "志望科類", "課題"] if c in df.columns]
        st.dataframe(filtered_df[display_cols], use_container_width=True)

        st.divider()
        st.write("▼ 詳細を確認したい行を選択")
        
        if not filtered_df.empty:
            def format_func(x):
                row = filtered_df.loc[x]
                return f"{row.get('日付', '')} - {row.get('生徒氏名', '')}"

            selected_index = st.selectbox("詳細を表示", filtered_df.index.tolist(), format_func=format_func)
            
            if selected_index is not None:
                row = filtered_df.loc[selected_index]
                json_data = row.get('データJSON')
                
                if pd.isna(json_data) or json_data == "" or json_data is None:
                    st.warning("詳細データなし")
                    st.write(f"概要: {row.get('課題', 'なし')}")
                else:
                    try:
                        detail = json.loads(json_data)
                        
                        st.markdown(f"**{row.get('生徒氏名')}** ({row.get('日付')})")
                        st.write(f"担当: {row.get('担当メンター')} / {row.get('文理')} / {row.get('志望科類')}")
                        st.info(f"課題: {row.get('課題')}")
                        
                        st.write("■ 成績")
                        exam_name_val = row.get('模試名')
                        exam_type_val = detail.get('exam_type', '東大二次(本番レベル)')
                        
                        if not pd.isna(exam_name_val) and str(exam_name_val).strip() != "":
                             st.markdown(f"📊 **{exam_name_val}** ({exam_type_val})")
                        
                        raw_scores = detail.get('scores', {})
                        
                        if raw_scores:
                            label_map = SCORE_LABELS_NIJI if exam_type_val == "東大二次(本番レベル)" else SCORE_LABELS_KYOTSU
                            score_display_data = {label_map.get(k, k): v for k, v in raw_scores.items() if v}
                            
                            if score_display_data:
                                score_df = pd.DataFrame([score_display_data])
                                st.table(score_df)
                            else:
                                st.caption("点数データなし")

                        st.write("■ アクション")
                        for act in detail.get('actions', []):
                            # 方針がある場合は表示
                            policy_text = act.get('policy', '')
                            policy_display = f"【方針】{policy_text} / " if policy_text else ""
                            
                            st.write(f"- 【{act['subject']}】 **{act['specificTask']}**")
                            st.caption(f"　 └ {policy_display}優先度: {act.get('priority','-')} (期限: {act['deadline']})")
                            
                    except json.JSONDecodeError:
                        st.error("データの形式が正しくありません。")

# ==========================================
# 3. プレビュー（出力）タブ
# ==========================================
with tab_preview:
    st.subheader("レポート出力")
    
    report_source = st.radio("出力するデータを選択", ["現在入力中の内容", "過去の保存データ"], horizontal=True)

    target_data = {}
    
    if report_source == "現在入力中の内容":
        target_data = {
            "date": date_val.strftime('%Y/%m/%d'),
            "mentor": mentor_name,
            "student": student_name,
            "grade": grade,
            "stream": stream,
            "target": target,
            "issue": current_issue,
            "actions": st.session_state.actions
        }
    else:
        df = load_data()
        if df.empty:
            st.warning("保存されたデータがありません。")
        else:
            # --- 修正: レポート用の検索機能 ---
            st.caption("検索フィルタ")
            rep_search = st.text_input("生徒名で絞り込み", key="rep_search_input")
            
            df_sorted = df.sort_index(ascending=False)
            
            # フィルタリング適用
            if rep_search:
                if '生徒氏名' in df_sorted.columns:
                    df_sorted = df_sorted[df_sorted['生徒氏名'].str.contains(rep_search, na=False)]
            
            if df_sorted.empty:
                st.warning("該当するデータが見つかりません。")
            else:
                def format_report_func(x):
                    r = df_sorted.loc[x]
                    return f"{r.get('日付', '')} - {r.get('生徒氏名', '')}"
                
                rep_idx = st.selectbox("レポートにする記録を選択", df_sorted.index.tolist(), format_func=format_report_func)
                
                if rep_idx is not None:
                    row = df_sorted.loc[rep_idx]
                    json_raw = row.get('データJSON')
                    if json_raw:
                        try:
                            d = json.loads(json_raw)
                            target_data = {
                                "date": row.get('日付'),
                                "mentor": row.get('担当メンター'),
                                "student": row.get('生徒氏名'),
                                "grade": row.get('学年'),
                                "stream": row.get('文理'),
                                "target": row.get('志望科類'),
                                "issue": row.get('課題'),
                                "actions": d.get('actions', [])
                            }
                        except:
                            st.error("データの読み込みに失敗しました")

    # レポート生成
    if target_data:
        report_text = f"【東大志望者面談シート】\n"
        report_text += f"日付: {target_data['date']} / 担当: {target_data['mentor']}\n"
        report_text += f"生徒: {target_data['student']} ({target_data['grade']})\n"
        report_text += f"文理: {target_data['stream']} / 志望: {target_data['target']}\n"
        report_text += f"課題: {target_data['issue']}\n\n"
        report_text += f"■ ネクストアクション\n"
        
        for idx, act in enumerate(target_data['actions']):
            # 方針を含めて出力
            p_text = act.get('policy', '')
            p_str = f"方針: {p_text} / " if p_text else ""
            
            report_text += f"{idx+1}. 【{act['subject']}】 {act['specificTask']}\n   ({p_str}期限: {act['deadline']})\n"
        
        st.code(report_text)
        st.caption("右上のコピーボタンでコピーできます")
