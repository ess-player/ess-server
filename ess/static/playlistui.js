/** @jsx React.DOM */

var Entry = React.createClass({
	render: function() {
		return (
			<tr>
				<td>{this.props.entry.order}</td>
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
		var resultNodes = this.props.playlist.map(function (entry, index) {
			return <Entry key={index} entry={entry} />
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
		return (
			<div className="header player">
				<form className="playerSelectForm" onSubmit={this.handlePlaylist}>
					<select onChange={this.handlePlaylist} ref="keyword">
						{playerOptions}
					</select>
				</form>
			</div>
			);
	}
});

var PlaylistUI = React.createClass({
	handlePlaylist: function(playername) {
		$.ajax({
			type: "GET",
			dataType: 'json',
			url: '/playlist/' + playername + '?expand=2',
			success: function( result ) {
				playlist = result[playername];
				this.setState({playlist:playlist, player:this.state.player});
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
		return {playlist:[],player:player};
	},
	render: function() {
		return (
				<div>
					<PlaylistHeader onPlaylist={this.handlePlaylist} player={this.state.player} />
					<Playlist playlist={this.state.playlist} />
				</div>
				);
	}
});


React.renderComponent(
		<PlaylistUI url="/playlist/" />,
		document.getElementById('playlistui')
		);
