import re
import os
import time
import shutil
import ffmpeg
from threading import Thread
from pytubefix import YouTube
from pytubefix.cli import on_progress
import zipfile

class YtDownload:
    def __init__(self):
        self.link = ""
        self.title = ""
        self.yt = None
        self.path = os.path.join(os.path.expanduser('~'), 'Downloads')
        self.youtube_regex = r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/|youtube\.com/playlist\?list=|youtube\.com/.*[?&]v=)([a-zA-Z0-9_-]{11})$'
        self.unzip_ffmpeg()
        self.remove_from_before()

    def unzip_ffmpeg(self):
        zip_file_path = "ffmpeg/ffmpeg.zip"
        if os.path.isfile(zip_file_path):
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall("ffmpeg")
            os.remove(zip_file_path)
    
    def remove_from_before(self):
        for item in os.listdir(self.path):
            if re.search("tempVideo.*|tempAudio.*", item):
                os.remove(os.path.join(self.path, item))

    def check_disk_space(self, required_space):
        total, used, free = shutil.disk_usage(self.path)
        return free > required_space

    def download_audio(self, audio):
        max_retries = 5
        retry_delay = 1
        output_file = f"tempAudio.{audio.mime_type.replace('audio/', '')}"
        print(f"INFO: Downloading Audio to {output_file}...Please wait...\n")
        for attempt in range(max_retries):
            try:
                self.yt.streams.get_by_itag(audio.itag).download(self.path, output_file)
                if os.path.exists(os.path.join(self.path, output_file)):
                    return True
                else:
                    print(f"ERR: Audio file {output_file} was not created.")
                    return False
            except Exception as e:
                print(f"INFO: Retry {attempt + 1}/{max_retries} for audio download...Error: {str(e)}")
                time.sleep(retry_delay)
                retry_delay *= 2
        print(f"ERR: Failed to download audio after {max_retries} attempts.")
        return False

    def download_video(self, video):
        max_retries = 5
        retry_delay = 1
        output_file = f"tempVideo.{video.mime_type.replace('video/', '')}"
        print(f"INFO: Downloading Video to {output_file}...Please wait...\n")
        for attempt in range(max_retries):
            try:
                self.yt.streams.get_by_itag(video.itag).download(self.path, output_file)
                if os.path.exists(os.path.join(self.path, output_file)):
                    return True
                else:
                    print(f"ERR: Video file {output_file} was not created.")
                    return False
            except Exception as e:
                print(f"INFO: Retry {attempt + 1}/{max_retries} for video download...Error: {str(e)}")
                time.sleep(retry_delay)
                retry_delay *= 2
        print(f"ERR: Failed to download video after {max_retries} attempts.")
        return False

    def download_video_audio(self, video, audio):
        video_path = os.path.join(self.path, f"tempVideo.{video.mime_type.replace('video/', '')}")
        audio_path = os.path.join(self.path, f"tempAudio.{audio.mime_type.replace('audio/', '')}")
        video_status = [False]
        audio_status = [False]

        def download_video_thread():
            video_status[0] = self.download_video(video)

        def download_audio_thread():
            audio_status[0] = self.download_audio(audio)

        video_thread = Thread(target=download_video_thread)
        audio_thread = Thread(target=download_audio_thread)
        video_thread.start()
        audio_thread.start()
        video_thread.join()
        audio_thread.join()

        return video_status[0], audio_status[0], video_path, audio_path

    def merge_video_audio(self, video_path, audio_path, output_path):
        if not os.path.exists(video_path):
            print(f"ERR: Video file not found at {video_path}")
            return False
        if not os.path.exists(audio_path):
            print(f"ERR: Audio file not found at {audio_path}")
            return False
        
        # Determine the path to ffmpeg.exe relative to the script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ffmpeg_path = os.path.join(script_dir, 'ffmpeg', 'ffmpeg.exe')
        
        # Check if ffmpeg.exe exists
        if not os.path.exists(ffmpeg_path):
            print(f"ERR: FFmpeg executable not found at {ffmpeg_path}. Please place FFmpeg binaries in the 'ffmpeg' folder beside the script.")
            return False
        
        try:
            video_stream = ffmpeg.input(video_path)
            audio_stream = ffmpeg.input(audio_path)
            ffmpeg.output(video_stream, audio_stream, output_path, vcodec='copy', acodec='copy', loglevel='quiet').run(overwrite_output=True, cmd=ffmpeg_path)
            print(f"INFO: Successfully merged to {output_path}")
            return True
        except ffmpeg.Error as e:
            print(f"ERR: Merging failed: {e.stderr.decode()}")
            return False
        except FileNotFoundError:
            print(f"ERR: FFmpeg executable not found at {ffmpeg_path}. Please ensure FFmpeg is correctly placed in the 'ffmpeg' folder.")
            return False

    def menu(self):
        self.link = input("Enter the movie link: ")
        if not re.match(self.youtube_regex, self.link):
            print("ERR: The video link is not valid")
            return
        self.yt = YouTube(self.link, on_progress_callback=on_progress)
        self.title = re.sub(r'[^a-zA-Z0-9]', '', self.yt.title)

        # Get all video streams (progressive and non-progressive)
        all_streams = self.yt.streams.filter(file_extension='mp4')
        video_streams = [stream for stream in all_streams if stream.resolution]
        if not video_streams:
            print("ERR: No video streams with valid resolutions found.")
            return

        print("\nAvailable video streams:")
        for index, stream in enumerate(video_streams):
            filesize_mb = stream.filesize / (1024 * 1024) if stream.filesize else "Unknown"
            resolution = stream.resolution or "Unknown"
            stream_type = "Progressive" if stream.is_progressive else "Video-only"
            print(f"{index + 1}. Resolution: {resolution} -- Format: {stream.mime_type} -- Type: {stream_type} -- FileSize: {filesize_mb:.2f} MiB")

        while True:
            try:
                index = int(input("\nEnter number of choice you want to download: ")) - 1
                if 0 <= index < len(video_streams):
                    break
                else:
                    print(f"ERR: Please enter a number between 1 and {len(video_streams)}")
            except ValueError:
                print("ERR: Invalid input. Please enter a valid number.")

        selected_stream = video_streams[index]
        required_space = selected_stream.filesize * 1.2
        if not self.check_disk_space(required_space):
            print(f"ERR: Insufficient disk space. Required: {required_space / (1024 * 1024):.2f} MiB")
            return

        if selected_stream.is_progressive:
            print("INFO: Downloading progressive stream...Please wait...\n")
            selected_stream.download(self.path, f"{self.title}.mp4")
            print(f"INFO: Downloaded to {self.path}/{self.title}.mp4")
        else:
            audios = self.yt.streams.filter(progressive=False, type="audio")
            if not audios:
                print("ERR: No audio streams available for merging.")
                return
            print("\nAvailable audio streams:")
            for index, audio in enumerate(audios):
                print(f"Audio {index + 1}: Bitrate: {audio.abr} -- Format: {audio.mime_type}")
            while True:
                try:
                    audio_index = int(input("Select audio stream (enter number): ")) - 1
                    if 0 <= audio_index < len(audios):
                        break
                    else:
                        print(f"ERR: Please enter a number between 1 and {len(audios)}")
                except ValueError:
                    print("ERR: Invalid input. Please enter a valid number.")
            audio = audios[audio_index]

            video_status, audio_status, video_path, audio_path = self.download_video_audio(selected_stream, audio)
            print("INFO: Merging video and audio...Please wait...\n")
            if video_status and audio_status:
                final_output_path = os.path.join(self.path, f"{self.title}.{selected_stream.mime_type.replace('video/', '')}")
                merge_status = self.merge_video_audio(video_path, audio_path, final_output_path)
                if merge_status:
                    os.remove(video_path)
                    os.remove(audio_path)
                else:
                    print("ERR: Merging failed.")
            else:
                print("ERR: Something went wrong. Try again")

if __name__ == "__main__":
    YtDownload().menu()