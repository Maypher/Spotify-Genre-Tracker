import cli
from dotenv import load_dotenv
from database import DatabaseManager

def main():
    load_dotenv()

    with DatabaseManager() as db:
        refresh_token = db.get_refresh_token()

        if refresh_token:
            program = cli.Program(refresh_token[0])
        else:
            program = cli.Program()
        
        program.run()


if __name__ == "__main__":
    main()
