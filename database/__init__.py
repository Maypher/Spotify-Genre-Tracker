import os
import sqlite3
from rich.console import Console
from rich.style import Style
import re
from pathlib import Path

class DatabaseManager:
    """
    Handles all connections and transactions to the local database
    """
    database_location: Path
    migration_dir: Path
    connection: sqlite3.Connection
    cursor: sqlite3.Cursor
    console: Console

    SUCCESS_STYLE = Style(color="green")
    ERROR_STYLE = Style(color="red")
    WARN_STYLE = Style(color="yellow")

    def __init__(self, database_location: str | None = None) -> None:
        self.database_location = Path(database_location) if database_location else Path(__file__).parent.joinpath("./database.db")
        self.migration_dir = Path(__file__).parent.joinpath("./migrations/")
        self.console = Console()
        

    def __enter__(self):
        if not self.database_location.exists():
            self.console.print(f"Database at location `{self.database_location}` not found. New database created.", style=self.WARN_STYLE)
            
        self.connection = sqlite3.connect(self.database_location)
        self.cursor = self.connection.cursor()
        return self
    
    def __exit__(self, exc_type, exc_val, traceback):
        if exc_type:
            self.console.print(f"Exception [bold]{exc_type}: {exc_val}[/bold]", style=self.ERROR_STYLE)

        self.cursor.close()
        self.connection.close()

        return True

    def migration_upgrade(self):
        """
        Reads the migrations files from the provided directory and applies them to the database.
        Migration files must be in the format `xxx_up.sql` where `xxx` is a 3 digit number.
        """

        with os.scandir(self.migration_dir) as dir:
            upgrade_re = re.compile("[0-9]{3}_up.sql")
            file_index_re = re.compile("[0-9]{3}")

            up_files = [file for file in dir if upgrade_re.match(file.name)]

            # Get the latest applied migration as to not apply previous ones again
            migration_version = self.cursor.execute("PRAGMA user_version").fetchone()[0]

            # If the amount of migration files is greater than or equal to the database version then
            # it means no migrations are pending. 
            if migration_version >= len(up_files):
                return

            self.console.print("Applying latest migrations...", style=self.WARN_STYLE)

            for index, migration_file in enumerate(up_files):
                # Get the index from the filename
                file_index = int(file_index_re.search(migration_file.name).group(0))

                # Skip migrations that have already been applied
                if file_index <= migration_version:
                    continue

                # If the migration files aren't numbered properly then throw an error.
                if file_index == index + 1:
                    with open(migration_file, "r") as sql_file:
                        sql_command = ""
                        # Read command by command because for big files `file.read()` doesn't return the entire content.
                        # So far it only happens it then first migrations where all genres must be added to the database.
                        for line in sql_file:
                            line = line.strip()
                            # Skip empty lines or comments
                            if line == "" or line.startswith("--"):
                                continue
                            
                            sql_command += line + " "
                            
                            if line.endswith(";"):
                                self.cursor.execute(sql_command)
                                sql_command = ""
                        # Execute any remaining SQL command (in case file doesn't end with a newline)
                        if sql_command.strip():
                            self.cursor.execute(sql_command)
                else:
                    raise IndexError(f"Migration with ID {index + 1} not found. Rolled back all migrations.")

                # Update the user version as to not apply the same migrations twice
                migration_version += 1
                self.cursor.execute(f"PRAGMA user_version = {migration_version}")
                self.console.print(f"Migration {migration_version} applied successfully!", style=self.SUCCESS_STYLE)
        
        self.connection.commit()
        self.console.print("All migrations applied successfully. The database is up to date!", style=self.SUCCESS_STYLE)

        



with DatabaseManager() as db:
    db.migration_upgrade()
