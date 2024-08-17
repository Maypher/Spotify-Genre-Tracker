import cli
from dotenv import load_dotenv
from datetime import timedelta
import configparser
from rich.console import Console

def main():
    load_dotenv()

    config = configparser.RawConfigParser()
    config.read("./config.cfg")

    customization_dict = dict(config.items('CUSTOMIZATION'))

    console = Console()

    try:
        time_goal = timedelta(hours=int(customization_dict["goal_time"]))
        program = cli.Program(time_goal)

        program.run()
    except ValueError as e:
        console.print(f"Unable to parse config file: {e.args[0]}", style="red")
    except KeyError as e:
        console.print(f"Unable to find config key: {e.args[0]}", style="red")

if __name__ == "__main__":
    main()
