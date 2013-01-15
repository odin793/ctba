var nice_table = function() {
	rows = document.getElementsByTagName('tr');
	$each(rows, function(el, ind) {
		if (ind % 2 == 0) el.setStyle('background', '#DEB887');
	});
};
