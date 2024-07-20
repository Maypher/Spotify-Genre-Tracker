from api.client import Client, CurrentTrack
from database import DatabaseManager

from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.table import Table
from rich import box
from rich.style import Style

import sys

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
        
        while not self.finish:
            # If a refresh token exists it means the user is authenticated
            if self.backend.authenticator.refresh_token:
                # Print full options
                pass
            else:
                self.anonymous_prompt_menu()

    def anonymous_prompt_menu(self) -> int:
        """
        Prompt menu used when no API token is available. 
        """
        menu = Table(box=box.HEAVY)
        menu.title = "Available Commands"
        menu.show_lines = True

        menu.add_column("ID", style="red")
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
            case 2:
                self.console.print("Goodbye!")
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

    def _update_genre_listen_time(self, increment_by: int):
        """
        Updates the listen time of the genre of the currently playing song.
        """

        with DatabaseManager() as db:
            db.increment_genre_listen_time(increment_by)
    
    def currently_listening_update_loop(self):
        """
        Made to be called from a different thread. Gets the currently playing song and updates it in the database
        """
