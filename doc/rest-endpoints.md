| Done | HTTP method | URL                                | Description                               | Input/Output |
|------|-------------|------------------------------------|-------------------------------------------|--------------|
| X    | POST        | /player                            | Register a player                         | Input = JSON{"name":name, "description":description} |
| X    | GET         | /player                            | Name and description of all players       | Output = JSON {"player":[{"current":current, "name":name, "description":description}, ...]} |
| X    | DELETE      | /player                            | Delete all players                        | - |
| X    | GET         | /player/&ltplayername&gt           | Name and description of &ltplayername&gt      | Output = JSON{"current":current, "name":name, "description":description}               |
| X    | GET         | /playlist                          | songlist and current of all playlists     | Output = JSON{playername:{"current":current, "list":[song_id, ..., song_id]},...} |
| X    | DELETE      | /playlist                          | Delete all playlists                      | - |
| X    | GET         | /playlist/&ltplayername&gt/current | Get current of player &ltplayername&gt        | Output = JSON{"id":song_id} |
| X    | POST        | /playlist/&ltplayername&gt/current | Post current of player &ltplayername&gt       | Input = JSON{"id":song_id} |
| X    | GET         | /playlist/&ltplayername&gt         | Get songlist and current of &ltplayername&gt  | Input = {"current":current, "list":[song_id, ..., song_id]} |
| X    | POST        | /playlist/&ltplayername&gt         | Post songlist and current of &ltplayername&gt | Output = {"current":current,"list":[song_id, ..., song_id]} |
| X    | DELETE      | /playlist/&ltplayername&gt         | Delete playlist of &ltplayername&gt           | - |
|      | GET         | /song/%ltid&gt                     | Deliver Song with id &ltid&gt                 | Output = Song as file |
|      | GET         | /                                  | -                                         | - |
|      | POST        | /                                  | -                                         | - |
| X    | POST        | /search                            | Post search and get matching result       | Input = JSON{"search":searchword}; Output = JSON{"songs":[{"album":album, "artist":artist, "date":date, "genre":genre, "song":song, "played_time":played_time, "tracknumber":tracknumber}], ...} |
