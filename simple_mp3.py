
from tkinter import *
from tkinter import ttk , filedialog
from Media_player import AudioPlayerTk
import os
import json
from random import shuffle
from re import fullmatch

# TODO: change the display , to make them not ugly

class Mp3_player:
    LOOP_BACK = 1
    NEXT_SONG = 2
    NEXT_RANDOM = 3

    def __init__(self , songs , root):

        self.songs = songs

        self.__generate_random_index_stack()


        self.mp3_frame = ttk.Frame(root)

        self.next_random = False

        self.current_song_index = 0

        self.audio_player = AudioPlayerTk( self.mp3_frame , call_back_when_stop=self.play_next_song  )


        self.choices = StringVar( value = self.songs )
        self.songs_list_box = Listbox( self.mp3_frame , listvariable=self.choices )

        self.songs_list_box.bind("<<ListboxSelect>>", lambda e: self.user_select_new_song( self.songs_list_box.curselection() ))

        self.loop_back_icon = "🔁"
        self.random_icon = "🔀"
        self.next_song_icon = "⏬"

        self.next_button_value = StringVar( value = self.next_song_icon )

        self.next_mode = self.NEXT_SONG


        self.button_frame = ttk.Frame(self.mp3_frame)
        self.play_previous_song_button = ttk.Button(self.button_frame , text="⏮️" , command=self.play_prev_song , width=15)
        self.play_next_song_button = ttk.Button( self.button_frame , text="⏭️" , command=self.play_next_song , width=15)
        self.next_mode_button = ttk.Button( self.button_frame, textvariable=self.next_button_value  , command=self.trigger_next_mode , width=15)


        self.draw()

    def draw(self):

        self.mp3_frame.grid()
        self.audio_player.draw()

        # row start at 1 because the audio player frame is in the row 0
        self.songs_list_box.grid(row=1, sticky=NSEW)
        self.button_frame.grid(row=2 , sticky=NSEW)
        self.play_previous_song_button.grid(row=0, column=0 , sticky=NSEW )
        self.play_next_song_button.grid(row=0, column=1 , sticky=NSEW)
        self.next_mode_button.grid(row=0, column=2 , sticky=NSEW)


    def stop(self):
        self.audio_player.stop()
        self.mp3_frame.destroy()

    def __generate_random_index_stack(self):
        """
            this method will generate random index stack
            we do this to improve random quality , no songs is play more than a time
            while make sure all songs have a chance to y!
        """
        self.random_index_stack =  list(range(0 , len(self.songs) ))
        shuffle( self.random_index_stack )


    def trigger_next_mode(self):
        # the button now will have 3 mode with different clicks
        # at first it will be normal or playnext song in the playlist
        # if trigger the first time , it will be switch to random song mode or the next song is random
        # if trigger again , it will turn to loopback mode
        # if trigger again , return to normal mode !

        if self.next_button_value.get( ) == self.next_song_icon:

            self.audio_player.change_callback( self.play_next_random_song )
            self.next_button_value.set( self.random_icon )

        elif self.next_button_value.get() == self.random_icon:
            self.audio_player.change_callback( self.play_again )
            self.next_button_value.set( self.loop_back_icon )

        elif self.next_button_value.get() == self.loop_back_icon:

            self.audio_player.change_callback( self.play_next_song )
            self.next_button_value.set(self.next_song_icon)

    def play_next_song(self):

        # we clear the song that is currently selected
        self.songs_list_box.selection_clear( self.current_song_index )

        # prevent out of list songs
        self.current_song_index += 1

        if self.current_song_index >= len( self.songs ):
            self.current_song_index = 0

        self.audio_player.load_audio( self.songs[ self.current_song_index ] )

        # we make the list box appear the new selected
        self.songs_list_box.select_set( self.current_song_index )

    def play_prev_song(self):
        # we clear the song that is currently selected
        self.songs_list_box.selection_clear( self.current_song_index )

        # prevent out of list songs
        self.current_song_index -= 1

        if self.current_song_index < 0 :
            self.current_song_index = len( self.songs ) - 1

        self.audio_player.load_audio( self.songs[ self.current_song_index ] )
        self.songs_list_box.select_set( self.current_song_index )

    def play_next_random_song(self):
        # we clear the song that is currently selected
        self.songs_list_box.selection_clear( self.current_song_index )

        if len( self.random_index_stack ) <=0 :
            self.__generate_random_index_stack()

        self.current_song_index = self.random_index_stack.pop()

        self.audio_player.load_audio( self.songs[ self.current_song_index ] )
        self.songs_list_box.select_set( self.current_song_index )

    def user_select_new_song(self, song_indexes ):

        if len(song_indexes) == 0:
            # if the user does not select anything
            return

        self.audio_player.load_audio( self.songs[ song_indexes[0] ]) # the curseselection return list of index , but if single selection , the list will never be more than 1 element
        self.current_song_index = song_indexes[0]

        # the reason why these lines is commented because the tkinter auto switch the selection for us !
        #self.songs_list_box.select_set( self.current_song_index )
        #self.songs_list_box.selection_clear( self.current_song_index )

    def load_new_songs(self , new_songs):
        self.songs = new_songs
        self.choices.set(value=self.songs)

    def play_again(self):
        self.audio_player.load_audio( self.songs[ self.current_song_index ] )


"""
    sửa lại ! 1 list box , ta select rồi có thể chọn các option như
    mở , sửa , xóa
    nút + sẽ tự động thêm 1 playlist mới !
"""

class Song_manager:


    def __init__(self, path_to_library: str , root):
        self.root = root
        self.mp3_player = Mp3_player( [] , root )

        self.songs = None
        self.playlists = {}
        self.path_to_library = path_to_library
        self.playlists_name =None


        self.sync_songs()
        self.sync_playlists()



        self.playlists_frame = ttk.Frame(root)
        self.playlist_choices =  StringVar(self.playlists_frame , value=self.playlists_name )
        self.playlists_listbox = Listbox(self.playlists_frame , listvariable=self.playlist_choices )
        self.playlist_label = ttk.Label(self.playlists_frame, text="playlists")

        self.create_new_playlist_button = ttk.Button(self.playlists_frame, text="➕" , command=self.create_new_playlist)
        self.delete_selected_playlist_button = ttk.Button(self.playlists_frame , text="🗑️" , command=self.delete_playlist)
        self.modify_playlist_button = ttk.Button(self.playlists_frame , text="⚙️" , command=self.modify_playlist )
        self.insert_playlist_button = ttk.Button(self.playlists_frame , text="↩️" , command=self.insert_playlist )


        self.draw()

    def stop(self):
        self.playlists_frame.destroy()
        self.mp3_player.stop()
        self.root.destroy()

    def draw(self):
        self.playlists_frame.grid(row=0 , column=1)
        self.playlist_label.grid(row=0 , columnspan=4)
        self.playlists_listbox.grid(row=1 , columnspan=4 , sticky=NSEW )
        self.create_new_playlist_button.grid(row=2 , column=0)
        self.delete_selected_playlist_button.grid(row=2 , column=1)
        self.modify_playlist_button.grid(row=2 , column=2)
        self.insert_playlist_button.grid(row=2,column=3)

    def insert_playlist(self):
        playlist_indexes = self.playlists_listbox.curselection()
        self.load_songs( playlist_indexes[0] )

    def sync_songs(self):
        os.chdir(self.path_to_library)
        self.songs = [ song for song in os.listdir() if os.path.isfile(song) and ( song.endswith(".mp3") or song.endswith(".wav") or song.endswith(".m4a") )  ]

    def sync_playlists(self):
        os.chdir(self.path_to_library)

        if not os.path.exists("playlists.json"):
            with open("playlists.json" , "w") as new_created_file:
                new_created_file.write("{}") # write an empty brackets for this json to be considered valid

        # we add and playlist that contains all the current song !
        self.playlists["all songs"] = self.songs

        with open("playlists.json" , "r") as new_created_file:
            # the self.playlists will be a map of playlist name and songs!
            self.playlists |= json.load( new_created_file )

        playlists_keys = list( self.playlists.keys() )

        for playlist_key in playlists_keys:
            if self.playlists[ playlist_key ] is None:
                # remove the playlist that is empty . Therefore , we will not load this empty playlist
                # and it will be discard after we save somethings!
                self.playlists.pop( playlist_key )

        # we need a list of playlist name to keep track of the playlist selected
        self.playlists_name = list( self.playlists.keys() )

    def load_songs(self, playlist_index):

        # the curse selection will return a list of index
        # the problem is the self.playlists is a dict while the selected playlists is the index of the playlist in the list of playlists_name

        self.mp3_player.load_new_songs( self.playlists[ self.playlists_name[ playlist_index ]  ] )

    def modify_playlist(self):

        # no play list is selected
        if len( self.playlists_listbox.curselection() ) == 0:
            return

        self.selected_playlist = self.playlists_name[ self.playlists_listbox.curselection()[0] ]

        # user can't modify or delete the all songs playlist !
        if self.selected_playlist == 'all songs':
            return

        song_selection_toplevel = Toplevel(self.playlists_frame)
        songs_choices = StringVar(song_selection_toplevel, value=self.songs)

        # multiple songs can be choosen
        self.songs_listbox = Listbox( song_selection_toplevel , selectmode=EXTENDED , listvariable=songs_choices )
        self.songs_listbox.bind("<<ListboxSelect>>" , self.__multiple_selection_list_box )



        # get all the index of the current songs in the playlist
        self.selected_index = set()
        if self.playlists[ self.selected_playlist ] is not None:

            quick_search_song = set( self.playlists[ self.selected_playlist ]    )
            for index , song in enumerate(self.songs):
                if song in quick_search_song:

                    self.selected_index.add( index )
        self.__selection_set_selected_song(self.selected_index , self.songs_listbox)


        playlist_name_label = ttk.Label(song_selection_toplevel, text="playlist name:")
        self.playlist_name_value = StringVar(song_selection_toplevel , value=self.selected_playlist)
        playlist_name_entry = ttk.Entry(song_selection_toplevel , textvariable=self.playlist_name_value )

        songs_label = ttk.Label(song_selection_toplevel , text="songs")
        self.log_message_value = StringVar(song_selection_toplevel , value="")
        self.log_messages_label = ttk.Label(song_selection_toplevel , textvariable=self.log_message_value )

        confirm_changes_button = ttk.Button(song_selection_toplevel , text="save changes" , command=self.__confirm_changes)

        # Configure styles
        style = ttk.Style( song_selection_toplevel)

        # Accept style
        style.configure('Accept.TLabel',
                        font=('Helvetica', 12, 'bold'),
                        foreground='green')

        # Denied style
        style.configure('Denied.TLabel',
                        font=('Helvetica', 12, 'bold'),
                        foreground='red')

        song_selection_toplevel.grid()
        playlist_name_label.grid(row=0 , column=0 , sticky=W)
        playlist_name_entry.grid(row=0 , column=1 , sticky=NSEW)
        songs_label.grid(row=1 , columnspan=2 , sticky=W)
        self.songs_listbox.grid(row=2 , columnspan = 2 , sticky=NSEW)
        self.log_messages_label.grid(row=3 , columnspan=2 , sticky=W )
        confirm_changes_button.grid(row=4 , columnspan=2 , sticky=NSEW)

    def __selection_set_selected_song(self, indexes: set , listbox_to_set):
        # clear all the selection
        listbox_to_set.selection_clear(0, END )

        for index in indexes:
            listbox_to_set.selection_set( index )

    def __multiple_selection_list_box(self, new_index):

        # nothing is selected
        if len( self.songs_listbox.curselection() ) == 0:
            return

        new_index = self.songs_listbox.curselection()[0]

        if new_index in self.selected_index:
            self.selected_index.remove( new_index )
        else:
            self.selected_index.add( new_index )

        self.__selection_set_selected_song(self.selected_index , self.songs_listbox )

    def __confirm_changes(self):
        NAME_EXIST = 0
        INVALID_NAME = 1
        ACCEPTED = 2


        # trim the leading white spaces
        self.playlist_name_value.set( self.playlist_name_value.get().strip() )

        error_code = self.__get_error_code( self.playlist_name_value.get() )

        if error_code == ACCEPTED:
            self.log_message_value.set("complete ! you can now close this windows")
            self.log_messages_label.configure( style='Accept.TLabel' )

            #TODO: write function to save changes here !
            # change the playlist name
            self.__change_playlist_name(self.selected_playlist , self.playlist_name_value.get() )
            # change songs in this playlist it have

            new_songs = []

            for index in self.songs_listbox.curselection():
                new_songs.append( self.songs[index ] )

            # change the songs in this playlist
            self.playlists[ self.playlist_name_value.get() ] = new_songs

            # save changes
            self.__backup_playlist()

            return


        self.log_messages_label.configure( style='Denied.TLabel')

        message = ""

        if error_code == NAME_EXIST:
            message = "this name is existed , please choose another name"
        if error_code == INVALID_NAME:
            message= """playlist can only contains number , character
,whitespaces and can't be empty !
"""
        self.log_message_value.set(message)

    def __get_error_code(self , name):
        NAME_EXIST = 0
        INVALID_NAME = 1
        ACCEPTED = 2

        # if the user haven't change the name !
        if self.selected_playlist == name:
            return ACCEPTED

        if name in self.playlists_name:
            return NAME_EXIST
        if not fullmatch(r'[0-9a-zA-Z ]+' , name ):
            return INVALID_NAME
        return ACCEPTED









    def create_new_playlist(self):
        iteration = 1
        name = "empty playlist"

        # prevent duplicate name !
        while name + str(iteration) in self.playlists_name:
            iteration += 1

        name = name + str(iteration)

        self.playlists_name.append(name)
        self.playlist_choices.set(value=self.playlists_name)
        # empty track
        self.playlists[ name ] = None


    def __change_playlist_name(self , old_name , new_name):
        # abort if the name to change does not exist
        if old_name not in self.playlists_name:
            return

        self.playlists_name.remove( old_name )
        self.playlists_name.append( new_name )

        self.playlist_choices.set( value=self.playlists_name )
        self.playlists[ new_name ] = self.playlists.pop(old_name)



    def __backup_playlist(self):

        # we don't need to save all songs playlist since this playlist is immune and it will be all sound files in the directory
        self.playlists.pop("all songs")

        # save changes !
        with open("playlists.json" , "w") as file_obj:
            file_obj.write(json.dumps( self.playlists ))

        # add again to prevent further errors
        self.playlists[ "all songs" ] = self.songs

    def delete_playlist(self ):
        # print("hello shit ?")

        # no playlist is selected
        if len( self.playlists_listbox.curselection() ) == 0 :
            return

        selected_playlist = self.playlists_name[ self.playlists_listbox.curselection()[0] ]

        # user can't modify or delete the all songs playlist !
        if selected_playlist == 'all songs':
            return


        self.playlists.pop(selected_playlist)
        self.playlists_name = list( self.playlists.keys() )
        self.playlist_choices.set( value=self.playlists_name )

        print( "delete " + selected_playlist )

        # save to the json
        self.__backup_playlist()



def main():
    path_to_library = filedialog.askdirectory()

    root = Tk()

    song_manager = Song_manager( path_to_library , root )


    root.protocol("WM_DELETE_WINDOW", song_manager.stop )
    root.mainloop()



if __name__ == "__main__":
    main()