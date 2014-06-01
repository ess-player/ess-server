| Done | HTTP method | URL                                 | Description                                                             | Input/Output |
|------|-------------|-------------------------------------|-------------------------------------------------------------------------|--------------|
| X    | POST        | /player                             | Register a player                                                       | Input = {"name":name, "description":description} |
| X    | GET         | /player                             | Name and description of all players                                     | Output =  {"player":[{"current":…, "name":…, "description":…}, …]} |
| X    | DELETE      | /player                             | Delete all players                                                      | - |
| X    | GET         | /player/[playername]                | Name and description of [playername]                                    | Output = {"current":…, "name":…, "description":…}               |
| X    | GET         | /playlist                           | songlist and current of all playlists                                   | Output = {playername:{"current":{"song_id":song_id, "playlist_id":playlist_id}, "list":[{"song_id":song_id, "playlist_id":playlist_id}...]},...} |
| X    | DELETE      | /playlist                           | Delete all playlists                                                    | - |
| X    | GET         | /playlist/[playername]/current      | Get current of player [playername]                                      | Output = {"song_id":song_id, "playlist_id":playlist_id} |
| X    | PUT         | /playlist/[playername]/current      | Post current of player [playername]                                     | Input = {"song_id":song_id, "playlist_id":playlist_id} |
| X    | GET         | /playlist/[playername]              | Get songlist and current of [playername]                                | Output = {"current":{"song_id":song_id, "playlist_id":playlist_id}, "list":[{"song_id":song_id, "playlist_id":playlist_id}, ...]} |
| X    | POST        | /playlist/[playername]              | Post songlist of [playername]                                           | Output = {"list":[song_id, ..., song_id]} |
| X    | DELETE      | /playlist/[playername]              | Delete playlist of [playername]                                         | - |
|      | GET         | /song/[id]                          | Deliver Song with id [id]                                               | Output = Song as file |
|      | GET         | /                                   | -                                                                       | - |
|      | POST        | /                                   | -                                                                       | - |
| X    | POST        | /search                             | Post search and get matching result                                     | Input = {"search":searchword}; Output = {"songs":[{"album":album, "artist":artist, "date":date, "genre":genre, "id":id, "title":title, "played_time":played_time, "tracknumber":tracknumber}], ...} |
|      | GET         | /playlist/[playername]/[place]/up   | Move playlistentry of player [playername] on place [place] to [place]-1 | - |
|      | GET         | /playlist/[playername]/[place]/down | Move playlistentry of player [playername] on place [place] to [place]-1 | - |
|      | PUT         | /playlist/[playername]/[place]      | Post new playlistentry on place [place] of player [playername]          | Input = {"id":song_id} |
|      | DELETE      | /playlist/[playername]/[place]      | Delete playlistentry on place [place] of player [playername]            | - |
