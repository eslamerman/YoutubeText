import boto3
import os
import yt_dlp as youtube_dl
from botocore.exceptions import ClientError
import openai
import streamlit as st
from whisper import Whisper

# Access secrets from Streamlit Cloud
aws_access_key_id = st.secrets["aws"]["aws_access_key_id"]
aws_secret_access_key = st.secrets["aws"]["aws_secret_access_key"]

# AWS S3 Setup
session = boto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

s3 = session.resource('s3')
bucket_name = 'erman-demo-1'

# Function to download YouTube video and extract audio
def download_youtube_video(youtube_url, download_path="downloads"):
    os.makedirs(download_path, exist_ok=True)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(download_path, 'video.%(ext)s'),
        'quiet': True
    }
    
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])
    
    # Return path to the downloaded file
    return os.path.join(download_path, 'video.mp4')

# Function to transcribe audio to text using Whisper
def transcribe_audio(audio_file_path):
    # Load Whisper model (ensure you have Whisper installed and configured)
    model = Whisper("base")  # You can use "small", "medium", "large" for better accuracy
    result = model.transcribe(audio_file_path)
    return result['text']

# Function to upload file to S3
def upload_to_s3(filename, bucket_name, key):
    try:
        s3.meta.client.upload_file(Filename=filename, Bucket=bucket_name, Key=key)
        print("File uploaded successfully.")
    except ClientError as e:
        print(f"Error uploading file: {e}")

# Streamlit UI setup
st.title("YouTube Video to Text Transcription")

# Get YouTube URL from the user
youtube_url = st.text_input("Enter YouTube Video URL")

if youtube_url:
    # Download YouTube video
    video_path = download_youtube_video(youtube_url)
    
    # Convert audio to text
    audio_file_path = video_path  # Assuming the video is already in the correct format
    transcribed_text = transcribe_audio(audio_file_path)
    
    # Save the transcribed text to a file
    text_filename = "transcribed_text.txt"
    with open(text_filename, "w") as file:
        file.write(transcribed_text)
    
    # Upload the text file to S3
    upload_to_s3(text_filename, bucket_name, key=text_filename)
    
    # Display the transcribed text in the Streamlit app
    st.text_area("Transcribed Text", transcribed_text, height=300)
