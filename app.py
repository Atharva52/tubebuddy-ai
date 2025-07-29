# 🎀 TubeBuddy.AI – Your Smart YouTube Analyzer

import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
import google.generativeai as genai

# 🔐 API KEYS (Replace with your actual working keys)
from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# 🔧 Initialize Gemini model
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# 📌 Function to convert user input to channel ID
def get_channel_id_from_input(input_str):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    try:
        if "youtube.com/channel/" in input_str:
            return input_str.split("/channel/")[1].split("/")[0]
        elif "youtube.com/" in input_str and "@" in input_str:
            handle = input_str.split("@")[1].split("/")[0]
        elif input_str.startswith("@"):  # handle
            handle = input_str[1:]
        else:
            return input_str

        request = youtube.search().list(q=handle, type="channel", part="snippet", maxResults=1)
        response = request.execute()
        if response.get("items"):
            return response["items"][0]["snippet"]["channelId"]
        return None
    except Exception as e:
        print(f"Error resolving channel ID: {e}")
        return None

# 📊 YouTube API class
class YouTubeAnalyzer:
    def __init__(self, channel_id):
        self.channel_id = channel_id
        self.youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    def get_channel_stats(self):
        try:
            request = self.youtube.channels().list(part="snippet,statistics", id=self.channel_id)
            response = request.execute()
            return response["items"][0] if response.get("items") else {}
        except Exception as e:
            print(f"Error fetching channel stats: {e}")
            return {}

    def get_video_list(self):
        video_data = []
        try:
            request = self.youtube.search().list(part="snippet", channelId=self.channel_id, maxResults=50, order="date")
            response = request.execute()
            for item in response.get("items", []):
                if item["id"].get("videoId"):
                    video_data.append({
                        "videoId": item["id"]["videoId"],
                        "title": item["snippet"].get("title", ""),
                        "description": item["snippet"].get("description", ""),
                        "publishedAt": item["snippet"].get("publishedAt", "")
                    })
            return video_data
        except Exception as e:
            print(f"Error fetching video list: {e}")
            return []

    def get_video_stats(self, video_id):
        try:
            request = self.youtube.videos().list(part="statistics", id=video_id)
            response = request.execute()
            return response["items"][0]["statistics"] if response.get("items") else {}
        except Exception as e:
            print(f"Error fetching video stats: {e}")
            return {}

# 🤖 AI Title Optimizer
def suggest_titles(title, description):
    prompt = f"""
    Improve this YouTube video title for higher engagement. Also suggest 2 alternate options.

    Title: {title}
    Description: {description}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI error: {e}"

# 🤖 AI Channel Summary
def generate_channel_summary(videos):
    top_titles = "\n".join([v["title"] for v in videos[:5]])
    prompt = f"""
    Based on the following top video titles, summarize the content strategy and provide 3 growth suggestions:

    {top_titles}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI error: {e}"

# 🌐 Streamlit UI Setup
st.set_page_config(page_title="TubeBuddy.AI", layout="wide")
st.title("🎀 TubeBuddy.AI – Your Smart YouTube Analyzer")

# 🔄 Layout Columns
left_col, main_col = st.columns([1, 5])

# 📂 Tabs in main area
with main_col:
    tabs = st.tabs(["🔍 Channel Overview", "🎬 Videos", "🧠 AI Insights"])

# 👉 Settings in sidebar (left)
with left_col:
    st.subheader("⚙️ Settings")
    dark_mode = st.toggle("🌗 Toggle Dark Mode")
    st.info("💡 Did you know? YouTube processes over 500 hours of content every minute!")

# 🎯 Input Area and Analyze Button
with main_col:
    st.markdown("Enter a YouTube channel ID, URL, or @handle to begin analysis.")
    input_channel = st.text_input("🔗 Channel Input", key="input")
    analyze_btn = st.button("🚀 Analyze Channel", key="analyze")

    if input_channel and analyze_btn:
        with st.spinner("🔍 Resolving and analyzing channel..."):
            channel_id = get_channel_id_from_input(input_channel)
            if not channel_id:
                st.error("❌ Could not resolve channel ID from input.")
            else:
                yt = YouTubeAnalyzer(channel_id)
                stats = yt.get_channel_stats()
                videos = yt.get_video_list()

                if stats:
                    snippet = stats.get("snippet", {})
                    statistics = stats.get("statistics", {})

                    with tabs[0]:
                        st.subheader("📌 Channel Overview")
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            thumbnail = snippet.get("thumbnails", {}).get("high", {}).get("url", "")
                            if thumbnail:
                                st.image(thumbnail, width=160)
                        with col2:
                            st.markdown(f"**🎬 Title:** {snippet.get('title', 'N/A')}")
                            st.markdown(f"**📄 Description:** {snippet.get('description', 'N/A')}")
                            st.markdown(f"**👥 Subscribers:** {statistics.get('subscriberCount', 'N/A')}")
                            st.markdown(f"**👁️ Total Views:** {statistics.get('viewCount', 'N/A')}")
                            st.markdown(f"**📼 Total Videos:** {statistics.get('videoCount', 'N/A')}")
                            published = snippet.get("publishedAt", "N/A")
                            st.markdown(f"**📅 Published On:** {published[:10] if published else 'N/A'}")

                    with tabs[1]:
                        st.subheader("🎬 Recent Videos")
                        df_videos = pd.DataFrame(videos)
                        st.dataframe(df_videos, use_container_width=True)

                    with tabs[2]:
                        st.subheader("🧠 Channel Strategy Summary")
                        with st.spinner("Generating insights..."):
                            summary = generate_channel_summary(videos)
                            st.markdown(summary)

                        st.subheader("🎯 Title Optimizer")
                        selected = st.selectbox("Pick a video title to optimize", df_videos["title"])
                        if selected and st.button("✨ Suggest Better Titles"):
                            video = next(v for v in videos if v["title"] == selected)
                            ai_titles = suggest_titles(video["title"], video.get("description", ""))
                            st.markdown(ai_titles)
                else:
                    st.error("❌ Channel not found or data unavailable.")
