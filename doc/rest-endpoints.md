| Done | HTTP method | URL                                 | Description                                                             | Input/Output |
|------|-------------|-------------------------------------|-------------------------------------------------------------------------|--------------|
| X    | POST        | /player                             | Register a player                                                       | Input = JSON{"name":name, "description":description} |
| X    | GET         | /player                             | Name and description of all players                                     | Output = JSON {"player":[{"current":current, "name":name, "description":description}, ...]} |
| X    | DELETE      | /player                             | Delete all players                                                      | - |
| X    | GET         | /player/[playername]                | Name and description of [playername]                                    | Output = JSON{"current":current, "name":name, "description":description}               |
| X    | GET         | /playlist                           | songlist and current of all playlists                                   | Output = JSON{playername:{"current":current, "list":[song_id, ..., song_id]},...} |
| X    | DELETE      | /playlist                           | Delete all playlists                                                    | - |
| X    | GET         | /playlist/[playername]/current      | Get current of player [playername]                                      | Output = JSON{"id":song_id} |
| X    | POST        | /playlist/[playername]/current      | Post current of player [playername]                                     | Input = JSON{"id":song_id} |
| X    | GET         | /playlist/[playername]              | Get songlist and current of [playername]                                | Input = {"current":current, "list":[song_id, ..., song_id]} |
| X    | POST        | /playlist/[playername]              | Post songlist and current of [playername]                               | Output = {"current":current,"list":[song_id, ..., song_id]} |
| X    | DELETE      | /playlist/[playername]              | Delete playlist of [playername]                                         | - |
|      | GET         | /song/[id]                          | Deliver Song with id [id]                                               | Output = Song as file |
|      | GET         | /                                   | -                                                                       | - |
|      | POST        | /                                   | -                                                                       | - |
| X    | POST        | /search                             | Post search and get matching result                                     | Input = JSON{"search":searchword}; Output = JSON{"songs":[{"album":album, "artist":artist, "date":date, "genre":genre, "id":id, "title":title, "played_time":played_time, "tracknumber":tracknumber}], ...} |
|      | GET         | /playlist/[playername]/[place]/up   | Move playlistentry of player [playername] on place [place] to [place]-1 | - |
|      | GET         | /playlist/[playername]/[place]/down | Move playlistentry of player [playername] on place [place] to [place]-1 | - |
|      | POST        | /playlist/[playername]/[place]      | Post new playlistentry on place [place] of player [playername]          | - |
|      | DELETE      | /playlist/[playername]/[place]      | Delete playlistentry on place [place] of player [playername]            | - |
