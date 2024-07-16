import threading
import queue
from collections import deque
from tkinter import *
from tkinter import ttk
from pydub import AudioSegment
import simpleaudio as sa
from time import time, sleep
from enum import Enum

# TODO: change the draw function to make it more beautiful
# TODO: adding more style and color to the GUI

# TODO: we need to change self.music_player_command_queue
# this new queue is deque  if in a short period of time , user change volume from -1 -2 -3 -4 -6  and then stop
# we do not need to instant stop and start audio at -1  -2 -3 - 4 -6 . We just need to start at -6
# so that , the query does not stack up and more perfomance . we do the same with every command like rewind and fast forward

TIMER_INTERVAL = 0.1 # the time to roundup timer action to 1 s
COVER_TIME = 1.5 # add more second to make sure that the music finished

class PlayerState(Enum):
    PLAYING = "playing"
    PAUSE = "pause"

class Timer(threading.Thread):
    def __init__(self, time_string_var, time_progress, timer_command_queue, music_player_command_queue , call_back_when_time_end = None ):

        self.call_back_when_time_end = call_back_when_time_end

        self.loop = False
        super().__init__()
        self.music_player_command_queue = music_player_command_queue
        self.command_queue = timer_command_queue
        self.timer = 0
        self.time_progress = time_progress
        self.total_length = 0
        self.state = PlayerState.PAUSE
        self.stop_event = threading.Event()
        self.time_string_var = time_string_var
        self.last_update_time = 0



    def __update_timer(self, add_time: float):
        self.timer += add_time
        self.timer = max(self.timer, 0)

    def __update_time_string_var(self):
        minute = f"{int(self.timer // 60):02}"
        second = f"{int(self.timer % 60):02}"
        total_minute = f"{int(self.total_length // 60):02}"
        total_second = f"{int(self.total_length % 60):02}"
        self.time_string_var.set(f"{minute}:{second} / {total_minute}:{total_second}")

    def __update_time_progress(self):
        self.time_progress.configure(value=(float(self.timer) / float(self.total_length) * 100))

    def update_all(self, add_time: float):
        if self.state == PlayerState.PLAYING:
            self.__update_timer(add_time)
        self.__update_time_progress()
        self.__update_time_string_var()

    def loop_back(self):
        self.timer = 0
        self.update_all(0)
        self.music_player_command_queue.put("play_again")

    def run(self):

        while not self.stop_event.is_set():

            current_time = time()

            if self.last_update_time == 0:
                self.last_update_time = current_time
            if not self.command_queue.empty():
                command = self.command_queue.get()
                if command == "pause":
                    self.state = PlayerState.PAUSE
                    continue
                self.state = PlayerState.PLAYING
                if command == "unpause":
                    self.update_all(0)
                elif command == "fast_forward":
                    self.update_all(3)
                elif command == "rewind":
                    self.update_all(-3)
                elif command == "play_again":
                    self.timer = 0
            elapsed_time = current_time - self.last_update_time

            if self.timer >= self.total_length:
                # if self.loop:
                #     self.loop_back()
                # else:
                if self.call_back_when_time_end is not None:
                    self.call_back_when_time_end()


            self.update_all(elapsed_time)

            self.last_update_time = current_time



            sleep(TIMER_INTERVAL)

    def stop(self):
        self.stop_event.set()

class MusicPlayer(threading.Thread):
    def __init__(self, audio_path, command_queue, timer , volume = 0):


        super().__init__()
        self.timer = timer
        self.audio_path = audio_path
        self.command_queue = command_queue
        self.volume = volume


        # check if mp3 , wav or m4a
        if audio_path.endswith(".mp3"):
            self.audio = AudioSegment.from_mp3(audio_path)
        elif audio_path.endswith(".wav"):
            self.audio = AudioSegment.from_wav(audio_path)
        else:
            self.audio = AudioSegment.from_file(audio_path)


        self.total_length = len(self.audio) / 1000.0 + COVER_TIME
        self.stop_event = threading.Event()
        self.state = PlayerState.PAUSE
        self.play_obj = None
        self.start_pos = 0

    def play_audio(self, start_time=0 , volume=0):
        self.stop_audio()
        self.start_pos = start_time * 1000
        play_segment = self.audio[self.start_pos:] + volume
        self.play_obj = sa.play_buffer(play_segment.raw_data, num_channels=play_segment.channels, bytes_per_sample=play_segment.sample_width, sample_rate=play_segment.frame_rate)

    def stop_audio(self):
        if self.play_obj and self.play_obj.is_playing():
            self.play_obj.stop()

    def run(self):
        while not self.stop_event.is_set():

            if not self.command_queue.empty():

                command = self.command_queue.get()

                if command == "play":
                    # we have to add self.volume incase the use select the new song but the volume is modified
                    self.play_audio(0 , self.volume)
                elif command == "pause":
                    self.stop_audio()
                elif command == "unpause":
                    current_pos = self.timer.timer
                    self.play_audio(current_pos , self.volume)
                elif command == "fast_forward":
                    current_pos = self.timer.timer + 3.0
                    self.play_audio(current_pos , self.volume )
                    self.timer.timer = current_pos
                elif command == "rewind":
                    current_pos = max(0, self.timer.timer - 3.0)
                    self.play_audio(current_pos , self.volume)
                    self.timer.timer = current_pos
                # TODO: since we have a callback when the song ends so this feature is no need . Remove it
                elif command == "play_again":
                    self.play_audio(0 , self.volume)
                    self.timer.timer = 0
                else: # if the command is a num , then we want to play the audio with volume

                    # update the volume
                    self.volume = command

                    # if the audio is playing , then continue playing with new volume
                    if self.play_obj and self.play_obj.is_playing():
                        self.stop_audio()
                        current_pos = self.timer.timer
                        self.play_audio(current_pos , self.volume )

            sleep(TIMER_INTERVAL)

    def stop(self):
        self.stop_event.set()
        self.stop_audio()

class AudioPlayerTk:
    def __init__(self, root, audio_path: str = None , call_back_when_stop = None ):

        self.call_back_when_stop = call_back_when_stop

        self.audio_player_frame = ttk.Frame(root)

        self.timer_frame = ttk.Frame(self.audio_player_frame)
        self.time_progress = ttk.Progressbar(self.timer_frame, orient=HORIZONTAL, length=200, value=0)
        self.current_time = StringVar(self.timer_frame, value="")
        self.current_time_label = ttk.Label(self.timer_frame, textvariable=self.current_time)

        self.timer = None
        self.music_player = None

        # this variable to prevent adjacent duplicate  volume query
        self.last_scale_volume = 0

        style = ttk.Style(self.audio_player_frame)

        style.configure('disable.TButton' , foreground="#000000" , background="#EEEEEE" )
        style.configure('enable.TButton', foreground="#EEEEEE" , background="#000000")

        self.fast_forward_icon = "⏩"
        self.rewind_icon = "⏪"
        self.pause_icon = "⏸️"
        self.play_icon = "▶️"

        self.cancel_loop_back_icon = "❌"
        self.state = PlayerState.PAUSE




        self.button_frame = ttk.Frame(self.audio_player_frame)
        self.play_pause_button = ttk.Button(self.button_frame, text=self.play_icon, command=self.play_pause , width=15 )
        self.fast_forward_button = ttk.Button(self.button_frame, text=self.fast_forward_icon, command=self.fast_forward , width=15)
        self.rewind_button = ttk.Button(self.button_frame, text=self.rewind_icon, command=self.rewind , width=15)

        self.volume_frame = ttk.Frame(self.audio_player_frame)
        self.volume_scale = IntVar( self.volume_frame , value = 0.0 )

        self.volume_scale_bar = ttk.Scale( self.audio_player_frame , orient=HORIZONTAL , length=200 , from_=-13.0 , to=13.0 , variable=self.volume_scale , command=self.change_volume )

        self.now_playing_song_frame = ttk.Frame(self.audio_player_frame)
        self.now_playing_song = StringVar(self.now_playing_song_frame , "now playing: ")
        self.now_playing_song_label = ttk.Label(self.now_playing_song_frame , textvariable=self.now_playing_song)

        if audio_path is not None:
            self.load_audio(audio_path)



        self.draw()

    def change_callback(self , new_callback):
        """
            this method is call in the outside obj
            in cases it want to chang the method to be callback

            can be use with play next song when song time end or play next random song
        """


        self.call_back_when_stop = new_callback

        if self.timer is None:
            return

        self.timer.call_back_when_time_end = new_callback


    def load_audio(self, audio_path ):

        self.timer_command_queue = queue.Queue()
        self.music_player_command_queue = queue.Queue()

        # self.music_player and self.timer is always be with each other , so they must be both None or not None
        if self.timer is not None or self.music_player is not None:
            # stop the running thread and keep the settings ( like volume , callback , ... )
            self.music_player.stop()
            self.timer.stop()







        self.now_playing_song.set(value = f"now playing: {audio_path}" )

        # when we first load the music , nothing is play
        self.state = PlayerState.PAUSE
        self.play_pause_button.configure(text=self.play_icon)

        self.timer_command_queue = queue.Queue()
        self.music_player_command_queue = queue.Queue()

        # since a thread once stop can't be start again so we have to create a new obj
        self.timer = Timer(self.current_time, self.time_progress, self.timer_command_queue, self.music_player_command_queue , call_back_when_time_end=self.call_back_when_stop )
        self.music_player = MusicPlayer(audio_path, self.music_player_command_queue, self.timer)

        # keep the old settings and things
        self.timer.total_length = self.music_player.total_length
        self.music_player.volume = self.volume_scale.get()

        self.music_player.start()
        self.timer.start()

        # play the song when we first load it !
        self.play_pause()

    def draw(self):

        self.audio_player_frame.grid(row=0 , sticky=NSEW)

        self.button_frame.grid(row=0,  sticky=NSEW )
        self.rewind_button.grid(row = 0 ,  column=1 , sticky=NSEW )
        self.play_pause_button.grid(row = 0 , column=2 , sticky=NSEW)
        self.fast_forward_button.grid(row = 0 , column=3 , sticky=NSEW)

        # both the progress and scale will take 80 % of the frame while the labels only need 20 %


        self.volume_scale_bar.grid(row=1 , column=0 , sticky=NSEW)



        self.timer_frame.grid(row=2 , sticky=NSEW)
        self.timer_frame.columnconfigure(0 , weight=80)
        self.timer_frame.columnconfigure(1 , weight=20)
        self.time_progress.grid(row=0, column=0, sticky=NSEW)
        self.current_time_label.grid(row=0 , column=1 , sticky=NSEW )

        self.now_playing_song_label.grid(row=3 , sticky=NSEW)


    def change_volume(self, volume):
        # we trim the floating point from the scaling to prevent overdraw
        self.volume_scale.set( round(self.volume_scale.get() , 2) )





        # prevent duplicate adjacent query
        if self.last_scale_volume == self.volume_scale.get():
            return

        self.last_scale_volume = self.volume_scale.get()

        print( self.volume_scale.get() )

        self.music_player_command_queue.put( self.volume_scale.get() )

    def play_pause(self):
        if self.timer is None or self.music_player is None:
            return # exit when there is no track selected

        if self.state == PlayerState.PAUSE:
            self.state = PlayerState.PLAYING
            self.play_pause_button.configure(text=self.pause_icon)
            self.music_player_command_queue.put("unpause")
            self.timer_command_queue.put("unpause")
        elif self.state == PlayerState.PLAYING:
            self.state = PlayerState.PAUSE
            self.play_pause_button.configure(text=self.play_icon)
            self.music_player_command_queue.put("pause")
            self.timer_command_queue.put("pause")

    def fast_forward(self):
        if self.timer is None or self.music_player is None:
            return # exit when there is no track selected

        self.music_player_command_queue.put("fast_forward")
        self.timer_command_queue.put("fast_forward")
        self.play_pause_button.configure(text=self.pause_icon)

    def rewind(self):
        if self.timer is None or self.music_player is None:
            return # exit when there is no track selected

        self.music_player_command_queue.put("rewind")
        self.timer_command_queue.put("rewind")
        self.play_pause_button.configure(text=self.pause_icon)

    def loop_back(self):
        if self.timer is None or self.music_player is None:
            return # exit when there is no track selected

        self.timer.loop = not self.timer.loop



    def play_again(self):
        if self.timer is None or self.music_player is None:
            return # exit when there is no track selected

        self.music_player_command_queue.put("play_again")
        self.timer_command_queue.put("play_again")
        self.play_pause_button.configure(text=self.pause_icon)

    def stop(self):
        if self.music_player is not None:
            self.music_player.stop()
            self.timer.stop()
        self.audio_player_frame.destroy()





def main():
    root = Tk()
    audio_player = AudioPlayerTk(root , "./y2mate.com - GTA TBoGT I Keep On Walking RemixMashup.mp3")
    root.protocol("WM_DELETE_WINDOW", audio_player.stop)
    root.mainloop()

if __name__ == "__main__":
    main()