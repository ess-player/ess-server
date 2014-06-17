/** @jsx React.DOM */

var Result = React.createClass({
	addEntry: function() {
		var request = JSON.stringify({ media : this.props.id });
		$.ajax({
			type: "POST",
			dataType: 'json',
			headers: { 'Content-Type' : 'application/json' },
			url: '/playlist/' + selected_player,
			data: request
		});
	},
	render: function() {
		return (
			<tr>
				<td>{this.props.artist}</td>
				<td>{this.props.album}</td>
				<td>{this.props.title}</td>
				<td><a title="Add to playlist" onClick={this.addEntry}>⏩</a></td>
			</tr>
			);
	}
});

var SearchResult = React.createClass({
	render: function() {
		if (this.props.media == undefined) {
			return <span />;
		}
		var resultNodes = this.props.media.map(function (media, index) {
			return <Result key={index} artist={media.artist.name}
			album={media.album.name} title={media.title} id={media.id} />
		});
		return (
			<table className="body">
				<thead>
					<tr>
						<td>Artist</td>
						<td>Album</td>
						<td>Title</td>
						<td></td>
					</tr>
				</thead>
				<tbody>
					{resultNodes}
				</tbody>
			</table>);
	}
});

var SearchHeader = React.createClass({
	handleSearch: function() {
		var keyword = this.refs.keyword.getDOMNode().value.trim();
		this.props.onSearch(keyword);
		return false;
	},
	render: function() {
		return (
			<div className="header search">
				<form className="searchForm" onSubmit={this.handleSearch}>
					<input type="text" placeholder="Search…" ref="keyword" />
					<input type="image" src="/static/icons/iconmonstr-magnifier-icon-48.png" alt="Submit" />
				</form>
			</div>
		);
	}
});

var SearchUI = React.createClass({
	handleSearch: function(keyword) {
		var request = JSON.stringify({ search : keyword });
		$.ajax({
			type: "POST",
			dataType: 'json',
			headers: { 'Content-Type' : 'application/json' },
			url: this.props.url,
			data: request,
			success: function( result ) {
				this.setState(result);
			}.bind(this)
		});
	 },
	 getInitialState: function() {
		 return {media: []};
	 },
	 render: function() {
		 return (
			 <div>
				 <SearchHeader onSearch={this.handleSearch} />
				 <SearchResult media={this.state.media} />
			 </div>
		 );
	 }
});


React.renderComponent(
	<SearchUI url="/search" />,
	document.getElementById('searchui')
);
