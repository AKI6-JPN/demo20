import streamlit as st
from streamlit.components.v1 import html
import json
import datetime
import pandas as pd
import io
import uuid


import gspread
from google.auth import service_account

# (1) Google Spread Sheetsにアクセス
def connect_gspread(key):
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gspread_service_account"], 
        scopes=scope
    )
    gc = gspread.authorize(credentials)
    worksheet = gc.open_by_key(key).sheet1
    return worksheet

# スプレッドシートに接続
spread_sheet_key = "1RWaKK45o8Ynzai0BOpO3eM2slQXewG1SXELp5nJZKvA"
ws = connect_gspread(spread_sheet_key)

# (2) Google Spread Sheets上の値を更新
# (２−１)あるセルの値を更新（行と列を指定）
ws.update_cell(1,1,"test1")
ws.update_cell(2,1,1)
ws.update_cell(3,1,2)

# (２−２)あるセルの値を更新（ラベルを指定）
ws.update_acell('C1','test2')
ws.update_acell('C2',1)
ws.update_acell('C3',2)

# (2-3)ある範囲のセルの値を更新
ds = ws.range('E1:G3')
ds[0].value = 1
ds[1].value = 2
ds[2].value = 3
ds[3].value = 4
ds[4].value = 5
ds[5].value = 6
ds[6].value = 7
ds[7].value = 8
ds[8].value = 9
ws.update_cells(ds)



st.set_page_config(page_title="共創カレンダー", page_icon="📅", layout="wide")

st.title("📅 共創カレンダー")

# Initialize events list
if "events" not in st.session_state:
    st.session_state.events = []

# Notification settings
if "notifications" not in st.session_state:
    st.session_state.notifications = []

# Search history
if "search_history" not in st.session_state:
    st.session_state.search_history = []

# Dynamic genre and color management
if "genres" not in st.session_state:
    st.session_state.genres = ["就活", "遊び", "大学イベント", "勉強", "その他"]

# Fixed 10-color palette
FIXED_COLOR_PALETTE = [
    "#FF4500",  # OrangeRed
    "#F79428",  # Marigold
    "#FFD700",  # Gold
    "#ADFF2F",  # GreenYellow
    "#32CD32",  # LimeGreen
    "#008080",  # Teal
    "#1E90FF",  # DodgerBlue
    "#6A5ACD",  # SlateBlue
    "#8A2BE2",  # BlueViolet
    "#FF3399",  # AzaleaPink
]

if "color_map" not in st.session_state:
    st.session_state.color_map = {}
    # Assign colors from the palette to existing genres
    for i, genre in enumerate(st.session_state.genres):
        st.session_state.color_map[genre] = FIXED_COLOR_PALETTE[i % len(FIXED_COLOR_PALETTE)]

# Initialize genre color selection session state
if 'selected_new_genre_color' not in st.session_state:
    st.session_state.selected_new_genre_color = FIXED_COLOR_PALETTE[0] # Default to the first color

# --- Sidebar ---
with st.sidebar:
    st.header("🎯 カレンダー設定")
    
    # Genre filter
    st.subheader("ジャンルフィルター")
    genre_filter = st.multiselect("ジャンルを選択", options=st.session_state.genres, default=st.session_state.genres)
    
    # Date filter
    st.subheader("期間フィルター")
    col1, col2 = st.columns(2)
    with col1:
        start_date_filter = st.date_input("開始日", value=datetime.date.today() - datetime.timedelta(days=30))
    with col2:
        end_date_filter = st.date_input("終了日", value=datetime.date.today() + datetime.timedelta(days=60))
    
    # Search function
    st.subheader("🔍 検索")
    search_query_input = st.text_input("イベント検索", placeholder="タイトルまたは説明で検索...", key="main_search_input")
    
    # Initialize search_query in session_state if it's not there
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""

    if search_query_input and search_query_input not in st.session_state.search_history:
        st.session_state.search_history.append(search_query_input)
        if len(st.session_state.search_history) > 10:
            st.session_state.search_history.pop(0)
    
    # Search history
    if st.session_state.search_history:
        st.subheader("検索履歴")
        for i, query in enumerate(reversed(st.session_state.search_history[-5:])):
            if st.button(f"🔍 {query}", key=f"search_history_{i}"):
                st.session_state.search_query = query
                st.rerun()
    
    # Use the search_query from session_state if a history button was clicked, otherwise from input
    search_query = st.session_state.search_query if st.session_state.search_query else search_query_input

    st.markdown("---")
    
    # Genre management
    st.subheader("⚙️ ジャンル管理")

    # カラーピッカーをStreamlitのボタンで実装
    st.write("新しいジャンルのカラーを選択:")
    color_cols = st.columns(5)
    for i, color_code in enumerate(FIXED_COLOR_PALETTE):
        col_idx = i % 5
        with color_cols[col_idx]:
            is_selected = color_code == st.session_state.selected_new_genre_color
            border_style = "3px solid #0066cc" if is_selected else "1px solid #ccc"
        
            # カラーボックスを表示
            st.markdown(f"""
            <div style="
                width: 30px;
                height: 30px;
                background-color: {color_code};
                border: {border_style};
                border-radius: 4px;
                margin: 2px auto;
                cursor: pointer;
                box-sizing: border-box;
            "></div>
            """, unsafe_allow_html=True)
        
            # 色選択ボタン
            if st.button("選択", key=f"color_btn_{i}", help=f"色: {color_code}"):
                st.session_state.selected_new_genre_color = color_code
                st.rerun()

    # 現在選択されている色を表示
    st.markdown(f"""
        選択中の色: 
        <span style='
            width: 25px; 
            height: 25px; 
            background-color: {st.session_state.selected_new_genre_color}; 
            display: inline-block; 
            vertical-align: middle; 
            border-radius: 50%;
            border: 2px solid #333;
            margin-left: 10px;
        '></span>
        """, unsafe_allow_html=True)

    # ジャンル追加後のリセット用のカウンター
    if 'genre_add_counter' not in st.session_state:
        st.session_state.genre_add_counter = 0

    # ジャンル追加フォーム
    new_genre_name = st.text_input("新しいジャンル名", key=f"new_genre_input_{st.session_state.genre_add_counter}")

    if st.button("ジャンル追加", key="add_genre_button"):
        if new_genre_name and new_genre_name.strip():
            if new_genre_name not in st.session_state.genres:
                st.session_state.genres.append(new_genre_name)
                st.session_state.color_map[new_genre_name] = st.session_state.selected_new_genre_color
                st.success(f"ジャンル「{new_genre_name}」を追加しました！")
            
                # 次のジャンル追加のために色を次の色に自動変更
                current_color_index = FIXED_COLOR_PALETTE.index(st.session_state.selected_new_genre_color)
                next_color_index = (current_color_index + 1) % len(FIXED_COLOR_PALETTE)
                st.session_state.selected_new_genre_color = FIXED_COLOR_PALETTE[next_color_index]
            
                # カウンターを増やしてテキスト入力をリセット
                st.session_state.genre_add_counter += 1
                st.rerun()
            else:
                st.warning(f"ジャンル「{new_genre_name}」は既に存在します。")
        else:
            st.warning("ジャンル名を入力してください。")

    # 既存ジャンルの削除
    if st.session_state.genres:
        st.write("---")
        st.write("既存ジャンルの削除:")
        genres_to_delete = st.multiselect("削除するジャンルを選択", options=st.session_state.genres, key="delete_genres_select")
        if st.button("選択したジャンルを削除", key="delete_genres_button"):
            for genre_to_del in genres_to_delete:
                if genre_to_del in st.session_state.genres:
                    st.session_state.genres.remove(genre_to_del)
                    if genre_to_del in st.session_state.color_map:
                        del st.session_state.color_map[genre_to_del]
            st.success("選択したジャンルを削除しました。")
            st.rerun()

    st.markdown("---")
    
    # Add event
    st.subheader("➕ イベント追加")
    with st.form("add_event"):
        title = st.text_input("タイトル*")
        description = st.text_area("説明", height=68)
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("開始日", value=datetime.date.today(), key="add_start_date")
            start_time = st.time_input("開始時刻", value=datetime.time(9, 0), key="add_start_time")
        with col2:
            end_date = st.date_input("終了日", value=datetime.date.today(), key="add_end_date")
            end_time = st.time_input("終了時刻", value=datetime.time(17, 0), key="add_end_time")
        
        genre = st.selectbox("ジャンル", options=st.session_state.genres, key="add_genre")
        registration = st.selectbox("事前申し込み", options=["必要", "不要"], key="add_registration")
        
        # Repeat settings
        repeat = st.selectbox("繰り返し", options=["なし", "毎日", "毎週", "毎月", "毎年"], key="add_repeat")
        
        submitted = st.form_submit_button("追加")

        if submitted and title:
            start_datetime_str = f"{start_date.isoformat()}T{start_time.isoformat()}"
            end_datetime_str = f"{end_date.isoformat()}T{end_time.isoformat()}"

            # Base event
            new_event_base = {
                "id": str(uuid.uuid4()),
                "title": title,
                "start": start_datetime_str,
                "end": end_datetime_str,
                "genre": genre,
                "registration": registration,
                "description": description,
            }
            
            # Repetition handling
            if repeat == "なし":
                st.session_state.events.append(new_event_base)
            else:
                current_date = start_date
                # Limit repeating events to one year from the start date for practicality
                end_limit = start_date + datetime.timedelta(days=365) 
                
                while current_date <= end_limit:
                    event_copy = new_event_base.copy()
                    event_copy["id"] = str(uuid.uuid4())  # Generate new ID for each repeat
                    
                    current_start_datetime = datetime.datetime.combine(current_date, start_time)
                    original_start_date_obj = datetime.date.fromisoformat(new_event_base["start"].split("T")[0])
                    original_end_date_obj = datetime.date.fromisoformat(new_event_base["end"].split("T")[0])
                    duration = original_end_date_obj - original_start_date_obj
                    current_end_datetime = datetime.datetime.combine(current_date + duration, end_time)

                    event_copy["start"] = current_start_datetime.isoformat(timespec='seconds')
                    event_copy["end"] = current_end_datetime.isoformat(timespec='seconds')
                    
                    st.session_state.events.append(event_copy)
                    
                    if repeat == "毎日":
                        current_date += datetime.timedelta(days=1)
                    elif repeat == "毎週":
                        current_date += datetime.timedelta(weeks=1)
                    elif repeat == "毎月":
                        # Logic to correctly add a month, handling end-of-month issues
                        next_month = current_date.month + 1
                        next_year = current_date.year
                        if next_month > 12:
                            next_month = 1
                            next_year += 1
                        
                        try:
                            current_date = current_date.replace(year=next_year, month=next_month)
                        except ValueError: # Handle cases like Jan 31 + 1 month = Feb 31 (invalid)
                            current_date = (current_date.replace(day=1) + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
                    elif repeat == "毎年":
                        current_date = current_date.replace(year=current_date.year + 1)
                    
                    if current_date > end_limit:
                        break
            
            st.success(f"イベント「{title}」を追加しました！")
            st.rerun()
        elif submitted and not title:
            st.warning("タイトルは必須です。")

    st.markdown("---")
    
    # Statistics
    st.subheader("📊 統計情報")
    total_events = len(st.session_state.events)
    genre_counts = {}
    
    for event in st.session_state.events:
        genre = event["genre"]
        genre_counts[genre] = genre_counts.get(genre, 0) + 1
    
    st.metric("総イベント数", total_events)
    
    if genre_counts:
        st.write("**ジャンル別:**")
        for genre, count in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True):
            st.markdown(f"• <span style='color: {st.session_state.color_map.get(genre, 'gray')};'>●</span> {genre}: {count}件", unsafe_allow_html=True)

    st.markdown("---")
    
    # Data management
    st.subheader("📂 データ管理")

    # CSV save
    if st.session_state.events:
        df_all = pd.DataFrame(st.session_state.events)
        # IDカラムを除外
        if 'id' in df_all.columns:
            df_all = df_all.drop('id', axis=1)
    
        df_all = df_all.rename(columns={
            "start": "開始日時",
            "end": "終了日時",
            "title": "タイトル",
            "genre": "ジャンル",
            "registration": "事前申し込み",
            "description": "説明",
        })
    
        csv_buffer = io.StringIO()
        df_all.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
        csv_data = csv_buffer.getvalue()
    
        st.download_button(
            label="📥 CSVダウンロード",
            data=csv_data.encode("utf-8-sig"),
            file_name=f"events_{datetime.date.today().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    # CSV upload
    uploaded_file = st.file_uploader("📤 CSVアップロード", type=['csv'])
    if uploaded_file:
        try:
            encodings = ["utf-8-sig", "cp932", "utf-8"]
            df = None
        
            for encoding in encodings:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
        
            if df is not None:
                column_mapping = {
                    "開始日": "start", "開始日時": "start",
                    "終了日": "end", "終了日時": "end",
                    "タイトル": "title",
                    "ジャンル": "genre",
                    "事前申し込み": "registration",
                    "説明": "description",
                }
            
                new_events = []
            
                for _, row in df.iterrows():
                    try:
                        event = {"id": str(uuid.uuid4())}  # Generate new ID for uploaded events
                        for col, value in row.items():
                            if col in column_mapping:
                                key = column_mapping[col]
                                if key in ["start", "end"] and pd.notna(value):
                                    try:
                                        dt_obj = pd.to_datetime(str(value))
                                        event[key] = dt_obj.isoformat(timespec='seconds')
                                    except:
                                        # Fallback for invalid date/time formats
                                        if key == "start":
                                            event[key] = datetime.datetime.now().isoformat(timespec='seconds')
                                        else:
                                            event[key] = (datetime.datetime.now() + datetime.timedelta(hours=1)).isoformat(timespec='seconds')
                                else:
                                    event[key] = str(value) if pd.notna(value) else ""
                    
                        # Ensure essential fields are present
                        if "title" not in event or not event["title"]:
                            event["title"] = "無題"
                        if "start" not in event:
                            event["start"] = datetime.datetime.now().isoformat(timespec='seconds')
                        if "end" not in event:
                            start_dt = datetime.datetime.fromisoformat(event["start"])
                            event["end"] = (start_dt + datetime.timedelta(hours=1)).isoformat(timespec='seconds')
                        if "genre" not in event or event["genre"] not in st.session_state.genres:
                            event["genre"] = "その他" # Assign to "その他" if genre is missing or invalid
                            if "その他" not in st.session_state.genres: # Add "その他" if it doesn't exist
                                st.session_state.genres.append("その他")
                                st.session_state.color_map["その他"] = FIXED_COLOR_PALETTE[len(st.session_state.genres) % len(FIXED_COLOR_PALETTE)]
                        if "registration" not in event or event["registration"] not in ["必要", "不要"]:
                            event["registration"] = "不要"
                        if "description" not in event:
                            event["description"] = ""
                    
                        new_events.append(event)
                    
                    except Exception as e:
                        st.warning(f"CSVの行の処理中にエラーが発生しました（一部スキップ）: {e} - 行データ: {row.to_dict()}")
                        continue
            
                if new_events:
                    st.session_state.events = new_events
                    # Update genres and color map from uploaded events
                    for event in new_events:
                        if event["genre"] not in st.session_state.genres:
                            st.session_state.genres.append(event["genre"])
                            st.session_state.color_map[event["genre"]] = FIXED_COLOR_PALETTE[len(st.session_state.genres) % len(FIXED_COLOR_PALETTE)]
                    st.success(f"CSVから{len(new_events)}件のイベントを読み込みました。")
                    st.rerun()
                else:
                    st.error("有効なイベントデータが見つかりませんでした。CSVの形式を確認してください。")
            else:
                st.error("CSVファイルを読み込めませんでした。エンコーディングを確認してください。")
            
        except Exception as e:
            st.error(f"CSVファイルの処理中にエラーが発生しました: {e}")

    # Delete all button
    if st.button("🗑️ 全イベント削除", type="secondary"):
        st.session_state.events = []
        st.success("すべてのイベントを削除しました。")
        st.rerun()

# --- Main Content ---

# Notification area
st.subheader("🔔 通知")
current_time = datetime.datetime.now()
st.session_state.notifications = [] # Clear previous notifications

for event in st.session_state.events:
    event_start_dt = datetime.datetime.fromisoformat(event["start"])
    notification_offset = event.get("notification_offset", "なし")

    notify_time = None
    if notification_offset == "5分前":
        notify_time = event_start_dt - datetime.timedelta(minutes=5)
    elif notification_offset == "15分前":
        notify_time = event_start_dt - datetime.timedelta(minutes=15)
    elif notification_offset == "30分前":
        notify_time = event_start_dt - datetime.timedelta(minutes=30)
    elif notification_offset == "1時間前":
        notify_time = event_start_dt - datetime.timedelta(hours=1)
    elif notification_offset == "1日前":
        notify_time = event_start_dt - datetime.timedelta(days=1)

    # Check if notification is due and not in the past relative to the event start
    if notify_time and current_time >= notify_time and current_time < event_start_dt:
        st.session_state.notifications.append(f"「{event['title']}」が{notification_offset}に開始します！ ({event_start_dt.strftime('%Y-%m-%d %H:%M')})")

if st.session_state.notifications:
    for notification in st.session_state.notifications:
        st.info(notification)
else:
    st.info("現在の通知はありません。")

# Today's events
today = datetime.date.today()
today_events = [e for e in st.session_state.events if datetime.datetime.fromisoformat(e["start"]).date() == today]

if today_events:
    st.subheader("📅 今日のイベント")
    for event in today_events:
        genre_color = st.session_state.color_map.get(event["genre"], "gray")
        start_time_str = datetime.datetime.fromisoformat(event["start"]).strftime("%H:%M")
        end_time_str = datetime.datetime.fromisoformat(event["end"]).strftime("%H:%M")
        st.markdown(f"""
        <div style="border-left: 4px solid {genre_color}; padding: 10px; margin: 5px 0; background-color: #f0f0f0;">
            <strong>{event['title']}</strong> ({event['genre']})
            <br><small>{start_time_str} - {end_time_str} | {event['description']}</small>
            {f"<br><small>タグ: {', '.join(event['tags'])}</small>" if event.get('tags') else ""}
        </div>
        """, unsafe_allow_html=True)

# Upcoming events
upcoming_events = [e for e in st.session_state.events 
                    if datetime.datetime.fromisoformat(e["start"]).date() > today]
upcoming_events.sort(key=lambda x: x["start"])

if upcoming_events:
    st.subheader("🔜 直近のイベント (今後5件)")
    for event in upcoming_events[:5]:
        start_dt = datetime.datetime.fromisoformat(event["start"])
        days_until = (start_dt.date() - today).days
        genre_color = st.session_state.color_map.get(event["genre"], "gray")
        st.markdown(f"""
        <div style="border-left: 4px solid {genre_color}; padding: 8px; margin: 3px 0; background-color: #fafafa;">
            <strong>{event['title']}</strong> - {days_until}日後 ({start_dt.strftime('%Y-%m-%d %H:%M')})
        </div>
        """, unsafe_allow_html=True)

# Event filtering for calendar display
filtered_events = []
for e in st.session_state.events:
    event_start_datetime = datetime.datetime.fromisoformat(e["start"])
    event_end_datetime = datetime.datetime.fromisoformat(e["end"])

    # Genre filter
    if e["genre"] not in genre_filter:
        continue

    # Date filter
    if event_start_datetime.date() < start_date_filter or event_start_datetime.date() > end_date_filter:
        continue
    
    # Search filter
    if search_query:
        if (search_query.lower() not in e["title"].lower() and 
            search_query.lower() not in e["description"].lower()):
            continue
    
    # Settings for FullCalendar display
    event_copy = e.copy()
    
    event_copy["backgroundColor"] = st.session_state.color_map.get(e["genre"], "gray") 
    event_copy["textColor"] = "#FFFFFF"
    event_copy["borderColor"] = st.session_state.color_map.get(e["genre"], "gray")
    
    # Check if it's an all-day event
    if event_start_datetime.date() != event_end_datetime.date() and \
       event_start_datetime.time() == datetime.time(0,0,0) and \
       event_end_datetime.time() == datetime.time(0,0,0):
        event_copy["allDay"] = True
    else:
        event_copy["allDay"] = False 

    event_copy["extendedProps"] = {
        "genre": e["genre"],
        "registration": e["registration"],
        "description": e["description"],
        "notification_offset": e.get("notification_offset", "なし"),
        "tags": e.get("tags", []),
        "original_id": e["id"]
    }

    filtered_events.append(event_copy)

# FullCalendar JavaScript code
calendar_code = f"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <link href='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.css' rel='stylesheet' />
    <script src='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.js'></script>
    <style>
      #calendar {{
        max-width: 100%;
        margin: 20px auto;
        font-family: Arial, sans-serif;
      }}
      .fc-event {{
        border-radius: 3px;
        border: none;
        padding: 2px;
        font-size: 0.9em;
      }}
      .fc-event-title {{
        font-weight: bold;
      }}
      .fc-daygrid-event {{
        margin: 1px;
      }}
    </style>
  </head>
  <body>
    <div id='calendar'></div>
    <script>
      document.addEventListener('DOMContentLoaded', function() {{
        var calendarEl = document.getElementById('calendar');
        var calendar = new FullCalendar.Calendar(calendarEl, {{
          initialView: 'dayGridMonth',
          headerToolbar: {{
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
          }},
          height: 'auto',
          locale: 'ja',
          events: {json.dumps(filtered_events)},
          eventDidMount: function(info) {{
            info.el.style.backgroundColor = info.event.backgroundColor;
            info.el.style.color = info.event.textColor;
            info.el.style.borderColor = info.event.borderColor;
          }},
          eventClick: function(info) {{
            // Display event details in an alert for now
            var eventData = {{
              title: info.event.title,
              start: info.event.startStr,
              end: info.event.endStr || info.event.startStr,
              genre: info.event.extendedProps.genre,
              description: info.event.extendedProps.description,
              registration: info.event.extendedProps.registration
            }};
            
            var message = "タイトル: " + eventData.title + "\\n" +
                         "ジャンル: " + eventData.genre + "\\n" +
                         "開始: " + eventData.start + "\\n" +
                         "終了: " + eventData.end + "\\n" +
                         "説明: " + eventData.description + "\\n" +
                         "申し込み: " + eventData.registration;
            
            alert(message);
          }},
          eventMouseEnter: function(info) {{
            info.el.style.transform = 'scale(1.02)';
            info.el.style.zIndex = '1000';
          }},
          eventMouseLeave: function(info) {{
            info.el.style.transform = 'scale(1)';
            info.el.style.zIndex = 'auto';
          }}
        }});
        calendar.render();
      }});
    </script>
  </body>
</html>
"""

st.subheader("📆 カレンダー表示")
st.info(f"表示中のイベント: {len(filtered_events)}件")

# Display the calendar. No 'key' argument for html() directly.
html(calendar_code, height=700)

# Process the clicked event data if available from the `postMessage` from the calendar
if "clicked_event_data_from_calendar" in st.session_state and st.session_state.clicked_event_data_from_calendar:
    clicked_event_data_json = st.session_state.clicked_event_data_from_calendar
    clicked_event = json.loads(clicked_event_data_json)
    st.subheader("イベント詳細")
    st.markdown(f"**タイトル:** {clicked_event.get('title')}")
    st.markdown(f"**ジャンル:** {clicked_event.get('genre')}")
    st.markdown(f"**説明:** {clicked_event.get('description', 'なし')}")
    st.markdown(f"**事前申し込み:** {clicked_event.get('registration')}")
    
    # Ensure datetime parsing handles potential timezone info ('Z')
    start_dt = datetime.datetime.fromisoformat(clicked_event['start'].replace('Z', '+00:00')) 
    end_dt = datetime.datetime.fromisoformat(clicked_event['end'].replace('Z', '+00:00')) if clicked_event['end'] else start_dt # Handle cases where end might be null
    
    st.markdown(f"**開始:** {start_dt.strftime('%Y-%m-%d %H:%M')}")
    st.markdown(f"**終了:** {end_dt.strftime('%Y-%m-%d %H:%M')}")
    st.markdown("---")
    # Clear the session state to prevent the details from reappearing on subsequent reruns
    del st.session_state.clicked_event_data_from_calendar


# Event list and editing
st.subheader("📝 イベント管理")

# Sort function
sort_options = ["日付順", "タイトル順", "ジャンル順"] 
sort_by = st.selectbox("並び順", sort_options)

# Sort events
if sort_by == "日付順":
    sorted_events = sorted(enumerate(st.session_state.events), key=lambda x: x[1]["start"])
elif sort_by == "タイトル順":
    sorted_events = sorted(enumerate(st.session_state.events), key=lambda x: x[1]["title"])
else:  # ジャンル順
    sorted_events = sorted(enumerate(st.session_state.events), key=lambda x: x[1]["genre"])

# Bulk operations
if st.session_state.events:
    st.subheader("🔧 一括操作")
    col1, col2 = st.columns(2) 
    
    with col1:
        selected_genre_bulk = st.selectbox("ジャンル一括変更", ["選択してください"] + st.session_state.genres, key="bulk_genre_select")
        if selected_genre_bulk != "選択してください":
            if st.button("ジャンル一括変更実行"):
                for event in st.session_state.events:
                    event["genre"] = selected_genre_bulk
                st.success(f"すべてのイベントのジャンルを「{selected_genre_bulk}」に変更しました。")
                st.rerun()
    
    with col2:
        if st.button("過去のイベント削除"):
            original_count = len(st.session_state.events)
            st.session_state.events = [e for e in st.session_state.events 
                                       if datetime.datetime.fromisoformat(e["start"]).date() >= today]
            deleted_count = original_count - len(st.session_state.events)
            st.success(f"過去のイベント {deleted_count}件を削除しました。")
            st.rerun()

# Event editing
if sorted_events:
    for original_idx, e in sorted_events:
        # Parse existing datetime strings
        event_start_dt = datetime.datetime.fromisoformat(e['start'])
        event_end_dt = datetime.datetime.fromisoformat(e['end'])

        genre_circle_color = st.session_state.color_map.get(e["genre"], "gray")
        
        # CORRECTED: Use simple string with Unicode/emoji and Streamlit Markdown
        # No 'unsafe_allow_html=True' here for st.expander title
        expander_title_str = f"● **{e['title']}** ({event_start_dt.strftime('%Y-%m-%d %H:%M')})"

        # Pass the plain string to st.expander
        with st.expander(expander_title_str): 
            col1, col2 = st.columns(2)
            
            with col1:
                new_title = st.text_input(f"タイトル", e['title'], key=f"title_{original_idx}")
                new_description = st.text_area(f"説明", e.get('description', ''), height=68, key=f"desc_{original_idx}")
                new_start_date = st.date_input(f"開始日", event_start_dt.date(), key=f"start_date_{original_idx}")
                new_start_time = st.time_input(f"開始時刻", event_start_dt.time(), key=f"start_time_{original_idx}")
            
            with col2:
                new_genre = st.selectbox(f"ジャンル", st.session_state.genres, index=st.session_state.genres.index(e['genre']), key=f"genre_{original_idx}")
                new_registration = st.selectbox(f"事前申し込み", ["必要", "不要"], index=["必要", "不要"].index(e['registration']), key=f"reg_{original_idx}")
                new_end_date = st.date_input(f"終了日", event_end_dt.date(), key=f"end_date_{original_idx}")
                new_end_time = st.time_input(f"終了時刻", event_end_dt.time(), key=f"end_time_{original_idx}")

            col_btn1, col_btn2, col_btn3 = st.columns(3)
            
            with col_btn1:
                if st.button("💾 更新", key=f"update_{original_idx}"):
                    updated_start_datetime_str = f"{new_start_date.isoformat()}T{new_start_time.isoformat()}"
                    updated_end_datetime_str = f"{new_end_date.isoformat()}T{new_end_time.isoformat()}"

                    st.session_state.events[original_idx] = {
                        "title": new_title,
                        "start": updated_start_datetime_str,
                        "end": updated_end_datetime_str,
                        "genre": new_genre,
                        "registration": new_registration,
                        "description": new_description,
                    }
                    st.success(f"「{new_title}」を更新しました。")
                    st.rerun()
            
            with col_btn2:
                if st.button("📋 複製", key=f"copy_{original_idx}"):
                    copied_event = e.copy()
                    copied_event["title"] = f"{e['title']} (コピー)"
                    st.session_state.events.append(copied_event)
                    st.success(f"「{e['title']}」を複製しました。")
                    st.rerun()

            with col_btn3:
                if st.button("🗑️ 削除", key=f"delete_{original_idx}"):
                    deleted_title = st.session_state.events[original_idx]["title"]
                    st.session_state.events.pop(original_idx)
                    st.success(f"「{deleted_title}」を削除しました。")
                    st.rerun()
else:
    st.info("イベントがありません。サイドバーから新しいイベントを追加してください。")

# Footer
st.markdown("---")
st.markdown("📅 **共創カレンダー** - より効率的なスケジュール管理を")