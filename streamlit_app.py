import streamlit as st
import yt_dlp
import os
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import make_chunks

# Function to download YouTube audio
def download_youtube_audio(url, output_path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    info = ydl.extract_info(url, download=False)
    filename = ydl.prepare_filename(info)
    audio_filename = os.path.splitext(filename)[0] + '.mp3'
    return audio_filename

# Function to convert MP3 audio to text
def convert_mp3_to_text(mp3_file):
    audio = AudioSegment.from_mp3(mp3_file)
    wav_file = mp3_file.rsplit('.', 1)[0] + '.wav'
    audio.export(wav_file, format="wav")

    recognizer = sr.Recognizer()
    chunk_length_ms = 60000  # 60 seconds
    chunks = make_chunks(audio, chunk_length_ms)

    full_text = []

    for i, chunk in enumerate(chunks):
        chunk_name = f'chunk{i}.wav'
        chunk.export(chunk_name, format="wav")

        with sr.AudioFile(chunk_name) as source:
            audio = recognizer.record(source)

        try:
            text = recognizer.recognize_google(audio, language='ar')
            full_text.append(text)
        except sr.UnknownValueError:
            st.warning(f"Could not understand audio in chunk {i+1}")
        except sr.RequestError as e:
            st.error(f"Error with recognition service: {e}")

        os.remove(chunk_name)

    os.remove(wav_file)
    return ' '.join(full_text) if full_text else None

# Main processing function
def process_audio_file(file_path, output_directory):
    text = convert_mp3_to_text(file_path)
    if text:
        text_file = os.path.join(output_directory, os.path.splitext(os.path.basename(file_path))[0] + '.txt')
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text)
        st.success(f"Text saved as: {text_file}")
    else:
        st.error("Failed to convert audio to text.")

# Streamlit App
st.sidebar.title("YouTube to Audio/Text App")
app_mode = st.sidebar.selectbox("Select Application", ["Download YouTube Audio", "Convert MP3 to Text"])

if app_mode == "Download YouTube Audio":
    st.title("Download YouTube Video as Audio")
    video_url = st.text_input("Enter YouTube Video URL:")
    output_directory = st.text_input("Enter Output Directory Path (e.g., './output/'):", "./output/")

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    if st.button("Download and Convert"):
        if video_url and output_directory:
            try:
                audio_file = download_youtube_audio(video_url, output_directory)
                st.success(f"Audio saved as: {audio_file}")
                process_audio_file(audio_file, output_directory)
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please enter both the video URL and output directory path.")

elif app_mode == "Convert MP3 to Text":
    st.title("Convert Existing MP3 to Text")
    mp3_file = st.file_uploader("Upload an MP3 File", type=['mp3'])
    output_directory = st.text_input("Enter Output Directory Path (e.g., './output/'):", "./output/")

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    if st.button("Convert to Text") and mp3_file is not None:
        mp3_path = os.path.join(output_directory, mp3_file.name)
        with open(mp3_path, 'wb') as f:
            f.write(mp3_file.getbuffer())
        
        process_audio_file(mp3_path, output_directory)
