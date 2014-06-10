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
		return <table className="body">{resultNodes}</table>;
	}
});

var PlaylistHeader = React.createClass({
	handlePlaylist: function() {
		var keyword = this.refs.keyword.getDOMNode().value.trim();
		this.props.onPlaylist(keyword);
		return false;
	},
	render: function() {
		return (
			<div className="header search">
				<form className="playerSelectForm" onSubmit={this.handlePlaylist}>
					<input type="text" placeholder="Playername…" ref="keyword" />
					<input type="image" src="/static/icons/iconmonstr-magnifier-icon-48.png" alt="Submit" />
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
				this.setState({playlist:playlist});
			}.bind(this)
		});
	 },
	 getInitialState: function() {
		 this.handlePlaylist('player01');
		 return {playlist:[]};
	 },
	 render: function() {
		 return (
			 <div>
				 <PlaylistHeader onPlaylist={this.handlePlaylist} />
				 <Playlist playlist={this.state.playlist} />
			 </div>
		 );
	 }
});


React.renderComponent(
	<PlaylistUI url="/playlist/" />,
	document.getElementById('playlistui')
);
