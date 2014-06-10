/** @jsx React.DOM */

var Result = React.createClass({
	render: function() {
		return (
			<tr>
				<td>{this.props.artist}</td>
				<td>{this.props.album}</td>
				<td>{this.props.title}</td>
				<td><a href="#" title="Add to playlist">⏩</a></td>
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
			album={media.album.name} title={media.title} />
		});
		return <table className="body">{resultNodes}</table>;
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
