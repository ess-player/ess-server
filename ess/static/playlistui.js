/** @jsx React.DOM */

function tryGetProp(obj, prop) {
	var i = 0;
	while (obj && i < prop.length) {
		obj = obj[prop[i]];
		i++;
	}
	return obj;
}

var Entry = React.createClass({
	onPlay: function() {
		this.props.onPlay(this.props.entry);
	},
	render: function() {
		return (
			<tr className="playlistentry">
				<td className="playlistid">{this.props.entry.order}</td>
				<td className="playbtn ln" onClick={this.onPlay}>▶</td>
				<td>{this.props.entry.media.artist.name}</td>
				<td>{this.props.entry.media.album.name}</td>
				<td>{this.props.entry.media.title}</td>
			</tr>
			);
	}
});

var Playlist = React.createClass({
	render: function() {
		if (this.props.playlist == undefined) {
			return <span />;
		}
		var onPlay = this.props.onPlay;
		var resultNodes = this.props.playlist.map(function (entry, index) {
			return <Entry key={index} entry={entry} onPlay={onPlay} />
		});
		return (
			<table className="body">
				<thead>
					<tr>
						<td>#</td>
						<td>Artist</td>
						<td>Album</td>
						<td>Title</td>
					</tr>
				</thead>
				<tbody>
					{resultNodes}
				</tbody>
			</table>
			);
	}
});


selected_player = ''
update_playlist = function() {};


var PlaylistHeader = React.createClass({
	handlePlaylist: function() {
		selected_player = this.refs.keyword.getDOMNode().value.trim();
		this.props.onPlaylist(selected_player);
		return false;
	},
	render: function() {
		var playerOptions = this.props.player.map(function (player, index) {
			return <option value={player.playername}>{player.playername}</option>
		});
		update_playlist = this.handlePlaylist;
		return (
			<div className="header player">
				<form className="playerSelectForm" onSubmit={this.handlePlaylist}>
					<select onChange={this.handlePlaylist} ref="keyword">
						{playerOptions}
					</select>
				</form>
				<div> back | -10 | playpause | +10 | forward </div>
				<div>
					{tryGetProp(this.props.current, ['media', 'artist', 'name'])} --
					{tryGetProp(this.props.current, ['media', 'album', 'name'])} --
					{tryGetProp(this.props.current, ['media', 'title'])}
				</div>
			</div>
			);
	}
});

var PlaylistUI = React.createClass({
	playMedia: function(entry) {
		var request = JSON.stringify({ current : entry.order });
		$.ajax({
			type: "PUT",
			dataType: 'json',
			headers: { 'Content-Type' : 'application/json' },
			url: '/playlist/' + selected_player + '/current',
			data: request,
			statusCode: {
				201: function() {
					this.setState({
						playlist : this.state.playlist,
						player   : this.state.player,
						current  : entry });
				}.bind(this)
			}
		});
	},
	handlePlaylist: function(playername) {
		$.ajax({
			type: "GET",
			dataType: 'json',
			url: '/playlist/' + playername + '?expand=2',
			success: function( result ) {
				playlist = result[playername];
				this.setState({
					playlist : playlist,
					player   : this.state.player,
					current  : this.state.current });
			}.bind(this)
		});
	},
	getInitialState: function() {
		var player = [];
		$.ajax({
			type: "GET",
			dataType: 'json',
			url: '/player',
			async: false,
			success: function( result ) {
				player = result.player;
			}.bind(this)
		});
		if (player.length) {
			this.handlePlaylist(player[0].playername);
			selected_player = player[0].playername;
		}
		return {playlist:[], player:player, current:null};
	},
	render: function() {
		return (
				<div>
					<PlaylistHeader
						onPlaylist={this.handlePlaylist}
						player={this.state.player}
						current={this.state.current}
						/>
					<Playlist
						onPlay={this.playMedia}
						playlist={this.state.playlist}
						/>
				</div>
				);
	}
});


React.renderComponent(
		<PlaylistUI url="/playlist/" />,
		document.getElementById('playlistui')
		);
