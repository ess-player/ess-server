$(document).ready(function() {

	$('.search img').click(function() {
		$.ajax({
			type: "POST",
			dataType: 'json',
			headers: { 'Content-Type' : 'application/json' },
			url: "/search",
			data: '{ "search" : "'+$('.search input').val()+'" }',
			success: function( result ) {
				songs = result.songs;
				var list = '';
				for (var i=0; i < songs.length; i++) {
					s = songs[i];
					list += '<tr class=song >';
					list += '<td class=artist>' + (s.artist ? s.artist : '') + '</td>';
					list += '<td class=album>'  + (s.album  ? s.album  : '') + '</td>';
					list += '<td class=title>'  + (s.title  ? s.title  : '') + '</td>';
					list += '</tr>';
				}
				$('#searchresult').html('<table>'+list+'</table>');
			}
		})
	});

})
