import os
import sqlite3
from rich.console import Console
from rich.style import Style
import re
from pathlib import Path
from typing import Tuple, List
import traceback


GenreEntry = Tuple[int, str, int]
"""Represents a genre in the database. Values are as follows: `(id, name, listen time in seconds)`"""

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

    @property
    def database_version(self):
        return self.cursor.execute("PRAGMA user_version").fetchone()[0]

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
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.console.print(f"Exception [bold]{exc_type}: {exc_val}[/bold]", style=self.ERROR_STYLE)
            if os.environ.get("debug"):
                formatted_traceback = ''.join(traceback.format_exception(exc_type, exc_val, exc_tb))
                self.console.print(formatted_traceback)

        self.cursor.close()
        self.connection.close()

        return True

    def update_database_version(self, version: int):
        self.cursor.execute(f"PRAGMA user_version = {version}")

    def migration_upgrade(self):
        """
        Reads the migrations files from the provided directory and applies them to the database.
        Migration files must be in the format `xxx_up.sql` where `xxx` is a 3 digit number.
        """

        with os.scandir(self.migration_dir) as dir:
            self.console.print("Applying latest migrations...", style=self.WARN_STYLE)

            upgrade_re = re.compile("[0-9]{3}_up.sql")
            file_index_re = re.compile("[0-9]{3}")

            up_files = [file for file in dir if upgrade_re.match(file.name)]

            # Get the latest applied migration as to not apply previous ones again
            migration_version = self.database_version

            # If the amount of migration files is greater than or equal to the database version then
            # it means no migrations are pending. 
            if migration_version >= len(up_files):
                self.console.print("No pending migrations!", style=self.SUCCESS_STYLE)
                return

            for index, migration_file in enumerate(up_files):
                # Get the index from the filename
                file_index = int(file_index_re.search(migration_file.name).group(0))

                # Skip migrations that have already been applied
                if file_index <= migration_version:
                    continue

                # If the migration files aren't numbered properly then throw an error.
                if file_index == index + 1:
                   self._apply_migration_file(migration_file)
                else:
                    raise IndexError(f"Migration with ID {index + 1} not found. Rolled back all migrations.")

                # Update the user version as to not apply the same migrations twice
                migration_version += 1
                self.update_database_version(migration_version)
                self.console.print(f"Migration {migration_version} applied successfully!", style=self.SUCCESS_STYLE)
        
        self.connection.commit()
        self.console.print("All migrations applied successfully. The database is up to date!", style=self.SUCCESS_STYLE)

    def migration_rollback(self, rollback_version: int):
        """
        Reads the migration rollback files and undos all migrations down to `rollback_version`.
        Rollback files must be in the format `xxx_down.sql` where `xxx` is a 3 digit number that should undo
        the related migration.
        """

        # Get the latest applied migration to know where to start rolling back from
        migration_version = self.cursor.execute("PRAGMA user_version").fetchone()[0]

        # Can't rollback to a version that doesn't yet exist or to same version
        if migration_version == rollback_version:
            self.console.print(f"Database already in version {migration_version}. No changes have been made.", style=self.ERROR_STYLE)
            return
        elif migration_version < rollback_version:
            self.console.print(f"Can't rollback migration to future version. \nCurrent database version: {migration_version}\nRollback version: {rollback_version}", style=self.ERROR_STYLE)
            return

        with os.scandir(self.migration_dir) as dir:
            self.console.print(f"Rolling back to version {rollback_version}...", style=self.WARN_STYLE)

            downgrade_re = re.compile("[0-9]{3}_down.sql")
            file_index_re = re.compile("[0-9]{3}")

            down_files = [file for file in dir if downgrade_re.match(file.name)]
            down_files.sort(reverse=True, key= lambda file: file.name)

            if migration_version - rollback_version != len(down_files):
                self.console.print(f"Not enough rollback files found to rollback to version {rollback_version}.\n Rollback files found: {[file.name for file in down_files]}", style=self.ERROR_STYLE)
                return

            for migration_file in down_files:
                # Stop applying rollbacks when the desired version is reached
                if migration_version == rollback_version:
                    break

                # Get the index from the filename
                file_index = int(file_index_re.search(migration_file.name).group(0))

                # If the rollback files aren't numbered properly then throw an error.
                if file_index == migration_version:
                   self._apply_migration_file(migration_file)
                else:
                    raise IndexError(f"Rollback with ID {migration_version} not found. Rolled back all migrations.")

                # Update the user version as to not apply the same rollback twice
                migration_version -= 1
                self.cursor.execute(f"PRAGMA user_version = {migration_version}")
                self.console.print(f"Rollback {migration_version} applied successfully!", style=self.SUCCESS_STYLE)
        
        self.connection.commit()
        self.console.print(f"All rollbacks applied successfully. Database now at version {migration_version}!", style=self.SUCCESS_STYLE)
    
    def _apply_migration_file(self, migration_file: os.DirEntry):
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

    def get_genre_count(self) -> int:
        return self.cursor.execute("SELECT COUNT(*) FROM GENRE").fetchone()[0]

    def get_genre_by_id(self, id: int) -> GenreEntry:
        return self.cursor.execute(f"SELECT * FROM Genre WHERE id = {id}").fetchone()
    
    def get_genres_by_name(self, name: str) -> List[GenreEntry]:
        """
        Gets all the genres that match the given name.
        """
        return self.cursor.execute(f"SELECT * FROM Genre WHERE name LIKE '%{name}%' ORDER BY name").fetchall()
    
    def get_top_listens(self) -> List[GenreEntry]:
        return self.cursor.execute(f"SELECT * FROM Genre WHERE listened_time > 0 ORDER BY listened_time DESC").fetchall()

    def get_random_genre(self) -> GenreEntry:
        return self.cursor.execute("SELECT * FROM Genre ORDER BY RANDOM() LIMIT 1").fetchone()
    
    def increment_genre_listen_time(self, genre_id: int, increment_by: int):
        """
        Increment a genre's listened by the given amount of seconds.
        """
        self.cursor.execute(f"UPDATE Genre SET listened_time = listened_time + {increment_by} WHERE id = {genre_id}")
        self.connection.commit()

    def create_new_genre(self, name: str):
        try:
            self.cursor.execute(f'INSERT INTO Genre (name) VALUES ("{name}")')
            self.connection.commit()
        except sqlite3.IntegrityError:
            raise sqlite3.IntegrityError(f"Genre with name '{name}' already exists.")
