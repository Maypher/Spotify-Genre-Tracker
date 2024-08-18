
# Spotify Genre Tracker

If you're like me you don't really have an answer to 
the question **"What type of music do you listen to?"**.
You either play the same few playlists over and over again
or just listen to whatever the first thing you happen to put
your eyes on.

The goal of this cli program is to broaden your music 
taste by keeping track of all the music genres you listen to and having a set time goal for each of them.

## Usage

The Spotify API is meant to be used server side so in order to
run it locally a few unusual steps are required. If I see this project take off I might set it up to work on a server and make it
publicly available.

1. Login to your Spotify account in the [developer dashboard](https://developer.spotify.com/dashboard).
2. Click "Create app".
3. Fill in the required information. 
- `Name` and `description` are irrelevant so write whatever you want here.
- `Website` can be left blank.
- `redirect uri`: This url is used for authentication purposes. Use any localhost url you have. For example, the one used during development is `http://localhost:8888/callback`.
- `API/SDK`: Only the Web API is required for this project to work.
4. Clone this repository.
5. In a `.env` file set the `client_secret` key to your app's client id.
6. Run the program by typing `python main.py` in the command line.
7. Input 1 to authenticate against the Spotify API.
8. After authorizing the app you should be redirected to the `redirect uri` that you set in the app setup. This should show a connection error unless you're running a server on that port. Either way just copy the url and paste it into the program.

Now you should have access to all commands. Start listening to anything on Spotify and the program will keep track of it!


## Acknowledgements

This project uses the Python programming language and the Spotify API. Special thanks to [Andytlr](https://gist.github.com/andytlr/4104c667a62d8145aa3a) for a list of a lot of Spotify genres. Although extensive, it is by no means exhaustive, the program will notify you if 
any genres not already in the database is found. Please contact me so I can add it into future releases of the program.

---

The information is stored in a local sqlite database in the `./database` directory. This also includes the refresh token used to
authenticate against the Spotify servers. Although no issues should
arise if this token gets compromised as it only uses read-only
permissions, I'm open to ideas on how to store the token locally
without risk of it being stolen.

## Environment Variables

This project uses two configuration files: `.env` and `config.cfg`.

`client_secret (.env)`: The client id of your Spotify app. 

`goal_time (config.cfg)`: The time in hours that should be achieved for every genre (Default=5).

