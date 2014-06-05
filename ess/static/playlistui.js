/** @jsx React.DOM */

var Entry = React.createClass({
	render: function() {
		return (
			<tr>
				<td>{this.props.artist}</td>
				<td>{this.props.album}</td>
				<td>{this.props.title}</td>
			</tr>
			);
	}
});

var Playlist = React.createClass({
	render: function() {
		var resultNodes = this.props.media.map(function (media, index) {
			return <Entry key={index} artist={media.artist.name}
			album={media.album.name} title={media.title} />
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
				<form className="searchForm" onSubmit={this.handlePlaylist}>
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
			url: '/playlist/' + playername + '?expand=1',
			success: function( result ) {
				playlist = result[playername];
				this.setState(playlist);
			}.bind(this)
		});
	 },
	 getInitialState: function() {
		 handlePlaylist('player01');
		 return [];
	 },
	 render: function() {
		 return (
			 <div>
				 <PlaylistHeader onSearch={this.handleSearch} />
				 <Playlist playlist={this.state} />
			 </div>
		 );
	 }
});


React.renderComponent(
	<PlaylistUI url="/playlist/" />,
	document.getElementById('playlistui')
);
