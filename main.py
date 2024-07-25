import cli
from dotenv import load_dotenv
from database import DatabaseManager
from datetime import timedelta

def main():
    load_dotenv()

    time_goal = timedelta(hours=5)
    program = cli.Program(time_goal)

    program.run()


if __name__ == "__main__":
    main()
