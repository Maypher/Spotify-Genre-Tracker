from api.client import Client

from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.table import Table
from rich import box

import sys

class Program:
    ERROR_STYLE = "red"
    SUCCESS_STYLE = "green"

    console: Console
    backend: Client
    refresh_token: str | None

    def __init__(self, refresh_token: str | None = None) -> None:
        self.console = Console()
        self.backend = Client()
        self.refresh_token = refresh_token

    def run(self):
        self.print_spotify_logo()
        
        while True:
            if self.refresh_token:
                # Print full options
                pass
            else:
                self.anonymous_prompt_menu()

    def anonymous_prompt_menu(self) -> int:
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
                self.backend.authenticator.request_auth_code()
                redirected_url = Prompt.ask("Enter redirect URL: ")
                try:
                    self.backend.authenticator.request_access_token(redirected_url)
                except PermissionError as e:
                    self.console.print(e, style=self.ERROR_STYLE)
                else:
                    self.console.print("Authentication successful", style=self.SUCCESS_STYLE)
            case 2:
                self.console.print("Goodbye!")
                sys.exit()

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
