from api.client import Client, CurrentTrack
from database import DatabaseManager

from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.table import Table
from rich import box
from rich.style import Style
import threading

import time
from datetime import timedelta, datetime

class Program:
    SUCCESS_STYLE = Style(color="green")
    ERROR_STYLE = Style(color="red")

    console: Console
    backend: Client
    finish: bool

    def __init__(self, refresh_token: str | None = None) -> None:
        self.console = Console()
        self.finish = False

        if refresh_token:
            self.backend = Client(refresh_token)
        else:
            self.backend = Client()

    def run(self):
        self.print_spotify_logo()

        with DatabaseManager() as db:
            db.migration_upgrade()
        
        try:
            while not self.finish:
                    # If a refresh token exists it means the user is authenticated
                    if self.backend.authenticator.refresh_token:
                        # Print full options
                        self.prompt_menu()
                    else:
                        self.anonymous_prompt_menu()
        except KeyboardInterrupt:
            self.finish = True

    def anonymous_prompt_menu(self):
        """
        Prompt menu used when no API token is available. 
        """
        menu = Table(box=box.HEAVY)
        menu.title = "Available Commands"
        menu.show_lines = True

        menu.add_column("ID", style="blue")
        menu.add_column("Name")
        menu.add_column("Description")

        menu.add_row("1", "Authenticate", "Authenticate against the Spotify API to access all available commands.")
        menu.add_row("2", "Quit", "Exit the program.")

        self.console.print(menu)

        option = IntPrompt.ask(choices=["1", "2"])

        match option:
            case 1:
                # Authenticate against api
                self.backend.authenticator.request_auth_code()
                redirected_url = Prompt.ask("Enter redirect URL")
                try:
                    self.backend.authenticator.request_access_token(redirected_url)
                except (PermissionError, KeyError) as e:
                    # Use e.args[0] because for some reason the error gets printed between single quotes which makes it green.
                    # By doing it this way the double quotes are removed.
                    self.console.print(e.args[0], style=Program.ERROR_STYLE)
                else:
                    self.console.print("Authentication successful", style=Program.SUCCESS_STYLE)
                    self._start_listening_thread() # Starts the thread that constantly updates the database
            case 2:
                self.console.print("Goodbye!")
                self.finish = True

    def prompt_menu(self):
        """
        Prompt menu for authenticated user.
        """

        menu = Table(title="Available Commands", box=box.HEAVY)
        
        menu.add_column("ID", style="blue")
        menu.add_column("Name")
        menu.add_column("Description")

        menu.add_row("1", "View progress", "Displays the progress of all genres.")
        menu.add_row("2", "View genre(s) progress", "Displays the progress of the genres that match the given query.")
        menu.add_row("3", "Logout", "Logs out by removing the credentials of the authenticated user. (TODO)")
        menu.add_row("4", "Quit", "Terminates the program")

        self.console.print(menu)

        option = IntPrompt.ask(choices=["1", "2", "3", "4"])

        match option:
            case 1:
                # Get and display the progress of all genres
                pass
            case 2:
                # View a specific genre's progress
                pass
            case 3:
                # Logout
                pass
            case 4:
                # Quit
                self.finish = True

    def print_spotify_logo(self):
        self.console.print("""
                            .:--======--:.                            
                      :=*#@@@@@@@@@@@@@@@@@@#*=:                      
                  -+%@@@@@@@@@@@@@@@@@@@@@@@@@@@@%+-                  
               -#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#=               
            .*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@*:            
          :#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#:          
        .*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#.        
       =@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@=       
      *@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#      
    .%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%.    
    %@@@@@@@@#*+=-::..           ..::-=++*#@@@@@@@@@@@@@@@@@@@@@@%.   
   #@@@@@@@@:                                .-=*%@@@@@@@@@@@@@@@@#   
  =@@@@@@@@%                                       .-+#@@@@@@@@@@@@=  
  @@@@@@@@@@#-..:-==+***########**++=-:.                :=#@@@@@@@@@  
 =@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%#+=:.            %@@@@@@@= 
 #@@@@@@@@@@@@@@@@@@@@@@@%%%%%%@@@@@@@@@@@@@@@@@@#+-.       *@@@@@@@# 
 %@@@@@@@@@@@@%+=-:.               .::-=*#%@@@@@@@@@@@*=:.-*@@@@@@@@@ 
 @@@@@@@@@@@@%                              .-+*%@@@@@@@@@@@@@@@@@@@@ 
 @@@@@@@@@@@@@:    .:--=========--:..            .-+#@@@@@@@@@@@@@@@@ 
 #@@@@@@@@@@@@@@%@@@@@@@@@@@@@@@@@@@@@@#*+-:          -@@@@@@@@@@@@@# 
 =@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%*=:      +@@@@@@@@@@@@= 
  @@@@@@@@@@@@@@%#*+=-:::::::::::--=+*#@@@@@@@@@@@#+--*@@@@@@@@@@@@@  
  =@@@@@@@@@@@@#                         :-+#@@@@@@@@@@@@@@@@@@@@@@+  
   #@@@@@@@@@@@@=:-=+**##%%%%%%##*+=-:.       .=*@@@@@@@@@@@@@@@@@%   
   .%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%*=:      -@@@@@@@@@@@@@@@.   
    .%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%+-  =@@@@@@@@@@@@@@.    
      #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#.     
       =@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@+       
        .#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#:        
          -%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%-          
            :*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#:            
              .=#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%=.              
                 .-*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@*=.                 
                     .-+*%@@@@@@@@@@@@@@@@@@%#+-.                     
                           .::-==++++==--:.                           
                   
        """, style="#1ED760")

    def _update_genre_listen_time(self, genre_id: int, increment_by: int):
        """
        Updates the listen time of the genre of the currently playing song.
        """

        with DatabaseManager() as db:
            db.increment_genre_listen_time(genre_id, increment_by)

    def _currently_listening_update_loop(self, check_interval: float):
        """
        Made to be called from a different thread. Gets the currently playing song and updates it in the database.
        
        ---
        # Parameters
        - `check_interval`: How often to ping the player for the current song.
        """

        check_interval: timedelta = timedelta(seconds=check_interval)
        recorded_song: CurrentTrack | None = self.backend.get_current_track()
        recorded_time: int = timedelta(seconds=recorded_song.progress_s) if recorded_song else None # The time in seconds at the previous iteration of the loop

        while not self.finish:
            time_before_request = datetime.now()
            current_song: CurrentTrack | None = self.backend.get_current_track()
            request_time = datetime.now() - time_before_request

            # If no song was found before the start of the loop set it to the current song
            if not recorded_song:
                recorded_song = current_song

            # If the user hasn't changed the song since the previous iteration of the loop
            if current_song:
                # For the first iteration of the loop if no song is playing the set it to 0
                if not recorded_time:
                    recorded_time = timedelta(seconds=current_song.progress_s)

                current_time = timedelta(seconds=current_song.progress_s)

                if current_song.song_id == recorded_song.song_id:
                    dif_time: timedelta = current_time - recorded_time # The difference in time between the current moment and the last loop iteration

                    # The system could be cheated by manually forwarding the song.
                    # This makes sure it doesn't happen by checking if the time difference is greater than the check interval
                    if dif_time < check_interval + request_time:
                        with DatabaseManager() as db:
                            for genre in current_song.genres:
                                genre_data = db.get_genre_by_name(genre)

                                if not genre_data:
                                    self._create_new_genre(genre)
                                    genre_data = db.get_genre_by_name(genre)

                                self._update_genre_listen_time(genre_data[0], dif_time.seconds)
                else:
                    # The system could be cheated by manually changing the song and forwarding it
                    # This prevents it by checking if the time of the new song is greater than what the interval is
                    if (current_time < check_interval + request_time):
                        with DatabaseManager() as db:
                            for genre in current_song.genres:
                                genre_data = db.get_genre_by_name(genre)

                                if not genre_data:
                                    self._create_new_genre(genre)
                                    genre_data = db.get_genre_by_name(genre)

                                self._update_genre_listen_time(genre_data[0], current_time.seconds)
                    
                recorded_time = current_time

            time.sleep(check_interval.total_seconds())

    def _start_listening_thread(self):
        listenting_thread = threading.Thread(target=self._currently_listening_update_loop, args=(1.5, ))
        listenting_thread.start()
    
    def _create_new_genre(self, name: str):
        with DatabaseManager() as db:
            db.create_new_genre(name)
            self.console.print("You found a new genre! It has been added into the database. Please contact the developer so he can add it to future releases of program.", style=self.SUCCESS_STYLE)
