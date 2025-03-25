import re
import os
import time
from pytubefix import YouTube
from pytubefix.cli import on_progress
from moviepy import VideoFileClip, AudioFileClip

class YtDownload():
    def __init__(self):
        self.link = ""
        self.title = ""
        self.yt = None
        self.path = os.path.join(os.path.expanduser('~'), 'Downloads')
        self.youtube_regex = r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/|youtube\.com/playlist\?list=|youtube\.com/.*[?&]v=)([a-zA-Z0-9_-]{11})$'
        self.remove_from_before()

    def remove_from_before(self):
        files = os.listdir(self.path)
        for item in files:
            if re.search("tempVideo.*", item):
                os.remove(os.path.join(self.path, item))
            if re.search("tempAudio.*", item):
                os.remove(os.path.join(self.path, item))

    def download_audio(self, audio):
        retry = 10
        print("INFO : Downloading Audio...Please wait...\n")
        while retry != 0:
            try:
                self.yt.streams.get_by_itag(audio.itag).download(self.path, "tempAudio." + audio.mime_type.replace("audio/", ""))
                return True
            except:
                time.sleep(2)
                print("INFO : Retry Download Audio...Please wait...\n")
                retry -= 1
        return False

    def download_video(self, video):
        retry = 10
        print("INFO : Downloading Video...Please wait...\n")
        while retry != 0:
            try:
                self.yt.streams.get_by_itag(video.itag).download(self.path, "tempVideo." + video.mime_type.replace("video/", ""))
                return True
            except:
                time.sleep(2)
                print("INFO : Retry Download Audio...Please wait...\n")
                retry -= 1
        return False

    def menu(self):
        self.link = input("Enter the movie link : ")
        if not re.match(self.youtube_regex, self.link):
            print("ERR : The video link is not valid")
        else:
            self.yt = YouTube(self.link, on_progress_callback = on_progress)
            self.title = re.sub(r'[^a-zA-Z0-9]', '', self.yt.title)
            videos = self.yt.streams.filter(progressive=False).filter(type="video")
            audios = self.yt.streams.filter(progressive=False).filter(type="audio")
            audio = audios[0]
            for item in audios:
                if int(item.abr.replace("kbps", "")) > int(audio.abr.replace("kbps", "")):
                    audio = item
            for index, item in enumerate(videos):
                menu_strings = f"{index + 1}. Resolution : {item.resolution} -- Format : {item.mime_type} -- FileSize : {(item.filesize + audio.filesize) / (1024 * 1024):.2f} MiB"
                print(menu_strings)
            index = int(input("Enter number of choice you want to download : ")) - 1
            # Download Video
            video_path = os.path.join(self.path, "tempVideo." + videos[index].mime_type.replace("video/", ""))
            video_status = self.download_video(videos[index])
            # Download Audio
            audio_path = os.path.join(self.path, "tempAudio." + audio.mime_type.replace("audio/", ""))
            audio_status = self.download_audio(audio)
            print("INFO : Merging video and audio...Please wait...\n")
            #Merge video and audio
            if video_status and audio_status:
                video_clip = VideoFileClip(video_path)
                audio_clip = AudioFileClip(audio_path)
                final_clip = video_clip.with_audio(audio_clip)
                final_output_path = os.path.join(self.path, f"{self.title}.{videos[index].mime_type.replace("video/", "")}")
                final_clip.write_videofile(final_output_path, codec='libx264', audio_codec='aac')
                video_clip.close()
                audio_clip.close()

                os.remove(video_path)
                os.remove(audio_path)

            else:
               print("ERR : Something went wrong. Try again") 


YtDownload().menu()