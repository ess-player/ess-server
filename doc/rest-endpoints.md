| HTTP method | URL                           | Description                                               |
|-------------|-------------------------------|-----------------------------------------------------------|
| GET         | /                             | Return UI                                                 |
| POST        | /search                       | Search and get matching result                            |
| GET         | /media/[id]                   | Deliver media with id [id]                                |
| POST        | /player                       | Register a player                                         |
| GET         | /player                       | Name and description of all players                       |
| GET         | /player/[name]                | Name and description of player [name]                     |
| DELETE      | /player/[name]                | Delete player [name]                                      |
| GET         | /playlist                     | All playlists                                             |
| DELETE      | /playlist                     | Delete all playlists                                      |
| GET         | /playlist/[name]              | Playlist of player [name]                                 |
| PUT         | /playlist/[name]              | Put playlist of player [name]                             |
| POST        | /playlist/[name]              | Add playlistentry at the end of playlist of player [name] |
| DELETE      | /playlist/[name]              | Delete playlist of player [name]                          |
| GET         | /playlist/[name]/[place]/up   | Move playlistentry of player [name] on [place] up         |
| GET         | /playlist/[name]/[place]/down | Move playlistentry of player [name] on [place] down       |
| DELETE      | /playlist/[name]/[place]      | Delete playlistentry on [place] of player [name]          |
| DELETE      | /playlist/[name]/current      | Delete current of player [name]                           |
| GET         | /playlist/[name]/current      | Get current of player [name]                              |
| PUT         | /playlist/[name]/current      | Put current of player [name]                              |
