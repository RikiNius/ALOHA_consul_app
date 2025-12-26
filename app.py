import streamlit as st
import pandas as pd
import datetime
import json

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

# --- データベース接続 (Google Sheets) ---
# 設定ファイル(secrets)がある場合は接続、なければデモモード(session_state)
try:
    from streamlit_gsheets import GSheetsConnection
    conn = st.connection("gsheets", type=GSheetsConnection)
    DB_MODE = True
except:
    DB_MODE = False

# データ読み込み関数
def load_data():
    if DB_MODE:
        try:
            # ワークシート名を指定して読み込み（キャッシュ時間を短く設定）
            df = conn.read(worksheet="logs", ttl=0)
            return df
        except Exception:
            # シートが空、または存在しない場合
            return pd.DataFrame(columns=["日付", "生徒氏名", "学年", "志望", "模試名", "課題", "データJSON"])
    else:
        # デモモード（一時保存）
        if "demo_data" not in st.session_state:
            st.session_state.demo_data = pd.DataFrame(columns=["日付", "生徒氏名", "学年", "志望", "模試名", "課題", "データJSON"])
        return st.session_state.demo_data

# データ保存関数
def save_data(new_row_df):
    current_df = load_data()
    updated_df = pd.concat([new_row_df, current_df], ignore_index=True)
    
    if DB_MODE:
        try:
            conn.update(worksheet="logs", data=updated_df)
            st.success("✅ データベース（スプレッドシート）に保存しました！")
        except Exception as e:
            st.error(f"保存エラー: {e}")
    else:
        st.session_state.demo_data = updated_df
        st.warning("⚠️ データベース未設定のため、一時保存しました（リロードすると消えます）。")

# --- UI構築 ---

st.title("🎓 UTokyo Mentoring Base")

# タブ切り替え
tab_new, tab_search, tab_preview = st.tabs(["📝 新規面談・保存", "🔍 過去ログ検索", "📄 レポート出力"])

# ==========================================
# 1. 新規作成タブ
# ==========================================
with tab_new:
    st.subheader("面談記録の入力")
    
    # --- ステート管理（入力用） ---
    if 'actions' not in st.session_state:
        st.session_state.actions = [
            {'subject': '英語', 'priority': '高', 'standardAdvice': 'eng_listen', 'specificTask': '鉄壁 Section 1-5', 'deadline': '次回まで'}
        ]

    # ヘルパー関数
    def add_action(stream_val):
        initial_subject = SUBJECTS[stream_val][0]
        st.session_state.actions.append({
            'subject': initial_subject, 'priority': '中', 'standardAdvice': 'custom', 'specificTask': '', 'deadline': '1週間後'
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
    exam_name = st.text_input("参照模試名", key="in_exam")
    sc = st.columns(5)
    scores = {}
    with sc[0]: scores['eng'] = st.text_input("英語", key="in_s_eng")
    with sc[1]: scores['math'] = st.text_input("数学", key="in_s_math")
    with sc[2]: scores['jp'] = st.text_input("国語", key="in_s_jp")
    if stream == "理系":
        with sc[3]: scores['sci1'] = st.text_input("理科①", key="in_s_sci1")
        with sc[4]: scores['sci2'] = st.text_input("理科②", key="in_s_sci2")
    else:
        with sc[3]: scores['soc1'] = st.text_input("社会①", key="in_s_soc1")
        with sc[4]: scores['soc2'] = st.text_input("社会②", key="in_s_soc2")
    
    current_issue = st.text_area("課題認識", key="in_issue")

    st.divider()

    # アクション
    st.caption("ネクストアクション")
    for i, action in enumerate(st.session_state.actions):
        with st.expander(f"Action {i+1}: {action['subject']}", expanded=True):
            ac1, ac2, ac3 = st.columns([2, 2, 2])
            with ac1:
                subj_list = SUBJECTS[stream]
                s_idx = subj_list.index(action['subject']) if action['subject'] in subj_list else 0
                st.session_state.actions[i]['subject'] = st.selectbox("教科", subj_list, index=s_idx, key=f"s_{i}")
            with ac2:
                p_opts = ["高", "中", "低"]
                st.session_state.actions[i]['priority'] = st.selectbox("優先", p_opts, index=p_opts.index(action['priority']), key=f"p_{i}")
            with ac3:
                st.session_state.actions[i]['deadline'] = st.text_input("期限", action['deadline'], key=f"d_{i}")
            
            # アドバイス型
            ak = list(STANDARD_ADVICE.keys())
            a_idx = ak.index(action['standardAdvice']) if action['standardAdvice'] in ak else 0
            st.session_state.actions[i]['standardAdvice'] = st.selectbox("型", ak, format_func=lambda x: STANDARD_ADVICE[x], index=a_idx, key=f"a_{i}")
            st.session_state.actions[i]['specificTask'] = st.text_input("タスク", action['specificTask'], key=f"t_{i}")
            
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
            # 保存用データ作成
            full_data = {
                "mentor": mentor_name,
                "scores": scores,
                "actions": st.session_state.actions,
                "stream": stream
            }
            new_row = pd.DataFrame([{
                "日付": date_val.strftime('%Y-%m-%d'),
                "生徒氏名": student_name,
                "学年": grade,
                "志望": target,
                "模試名": exam_name,
                "課題": current_issue,
                "データJSON": json.dumps(full_data, ensure_ascii=False) # 詳細データはJSON形式で1列に格納
            }])
            
            save_data(new_row)

# ==========================================
# 2. 検索タブ
# ==========================================
with tab_search:
    st.subheader("過去ログ検索")
    
    df = load_data()
    
    if df.empty:
        st.info("まだ保存されたデータはありません。")
    else:
        # 検索フィルタ
        search_name = st.text_input("生徒名で検索", placeholder="名前の一部を入力")
        
        if search_name:
            filtered_df = df[df['生徒氏名'].str.contains(search_name, na=False)]
        else:
            filtered_df = df

        st.dataframe(filtered_df[['日付', '生徒氏名', '学年', '模試名', '課題']], use_container_width=True)

        # 詳細表示
        st.divider()
        st.write("▼ 詳細を確認したい行の「データJSON」")
        selected_indices = st.selectbox("詳細を表示する生徒を選択（上から順）", filtered_df.index.tolist(), format_func=lambda x: f"{filtered_df.loc[x, '日付']} - {filtered_df.loc[x, '生徒氏名']}")
        
        if selected_indices is not None:
            row = filtered_df.loc[selected_indices]
            try:
                detail = json.loads(row['データJSON'])
                
                st.markdown(f"**{row['生徒氏名']}** ({row['日付']})")
                st.info(f"課題: {row['課題']}")
                
                st.write("■ 成績")
                st.json(detail['scores'])
                
                st.write("■ アクション")
                for act in detail['actions']:
                    st.write(f"- 【{act['subject']}】: {act['specificTask']} ({act['deadline']})")
            except:
                st.error("データ形式が古いため詳細を表示できません")

# ==========================================
# 3. プレビュー（出力）タブ
# ==========================================
with tab_preview:
    st.subheader("コピー用テキスト")
    # 入力中の内容から生成
    report_text = f"【東大志望者面談シート】\n"
    report_text += f"日付: {date_val.strftime('%Y/%m/%d')} / 担当: {mentor_name}\n"
    report_text += f"生徒: {student_name} ({grade}) -> 志望: {target}\n"
    report_text += f"課題: {current_issue}\n\n"
    report_text += f"■ ネクストアクション\n"
    for idx, act in enumerate(st.session_state.actions):
        adv = STANDARD_ADVICE.get(act['standardAdvice'], "") if act['standardAdvice'] != 'custom' else "特になし"
        report_text += f"{idx+1}. 【{act['subject']}】 {act['specificTask']}\n   (Pt:{adv} / {act['deadline']})\n"
    
    st.code(report_text)
