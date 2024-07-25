import cli
from dotenv import load_dotenv
from database import DatabaseManager
from datetime import timedelta

def main():
    load_dotenv()

    with DatabaseManager() as db:
        refresh_token = db.get_refresh_token()

        time_goal = timedelta(hours=5)

        if refresh_token:
            program = cli.Program(time_goal, refresh_token[0])
        else:
            program = cli.Program(time_goal)
        
        program.run()


if __name__ == "__main__":
    main()
