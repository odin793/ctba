Array.implement({
	sum: function(field) {
		var sum = 0;
		var list_obj = listobj_to_list(this, field);
		$each(list_obj, function(el, ind) {
			sum = sum + el;				
		});
		return sum;
	},

	max: function(no_field) {
		var max = 0;
		if (no_field != true) var list_obj = listobj_to_list(this, "price");
		else var list_obj = this;
		$each(list_obj, function(el, ind) {
			if (el > max) max = el;
		});
		return max;
	},
	
	min: function() {
		var list_obj = listobj_to_list(this, "price");
		if (list_obj.length == 0) return 0;
		var min = list_obj[0];
		$each(list_obj, function(el, ind) {
			if (el < min) min = el;
		});
		return min;
	},
		
	to_nice_str: function(no_commas) {
		var s = "";
		var no_commas = (typeof no_commas === 'undefined') ? false: true;
		if (no_commas) {
			$each(this, function(el, ind) {	
				s += el;
			});			
		}
		else {
			$each(this, function(el, ind) {	
				s += el;
				if (this.length != ind+1) s += ", ";
			}, this);						
		}
		return s;
	},
});


var listobj_to_list = function(obj, field) {
	var obj_mode = (typeof field === 'undefined') ? false: true;
	var result = [];
	if (!obj_mode) return obj;
	else {
		$each(obj, function(el, ind) {
			result.append([el[field]]);
		}); 
	};
	return result;
};


var GraphStat = new Class({
	initialize: function(holder, datasets) {
		this.stat_holder = $(holder);
		this.stat_header_holder = $("graph_1_stat_header");
		this.datasets = datasets;
		this.filtered_datasets = [];
		this.stat_obj = {};
		this.string_stat_obj = {};
		this.day_in_ms = 1000 * 60 * 60 * 24;
		this.categories_list = ["A", "B", "C", "D", "E", "All"];
	},
	
	filter_datasets: function(d1, d2) {
		this.filtered_datasets.empty();
		$each(this.datasets, function(el, ind) {
			//console.log(el.dataProvider.slice(1,-1));
			this.filtered_datasets[ind] = el.dataProvider.slice(1,-1).filter(function(point_obj) {
				return ((point_obj.date_time-d1) > 0) && ((point_obj.date_time-d2) < 0);
			});		
		}, this);
	},

	to_cats_pairs: function(l) {
		var result = [];
		$each(l, function(el, ind) {
			result.append(["<b>" + this.categories_list[ind] + "</b>: " + el]);
		}, this);
		return result.to_nice_str();
	},
	
	get_sum_each_cat: function() {
		var sum_each_cat = [];
		$each(this.filtered_datasets, function(el, ind) {
			sum_each_cat[ind] = el.sum("price");
		}, this);
		this.stat_obj["sum_each_cat"] = sum_each_cat;
		this.string_stat_obj["sum_each_cat"] = this.to_cats_pairs(sum_each_cat);
	},

	get_max_all: function() {
		var max_all = this.filtered_datasets.getLast().max(); // max from category All
		this.stat_obj["max_all"] = max_all;
		this.string_stat_obj["max_all"] = max_all;		
	},

	get_max_each_cat: function() {
		var max_each_cat = [];
		$each(this.filtered_datasets, function(el, ind) {
			max_each_cat[ind] = el.max();
		}, this);
		this.stat_obj["max_each_cat"] = max_each_cat;
		this.string_stat_obj["max_each_cat"] = this.to_cats_pairs(max_each_cat.slice(0, -1));	
	},

	get_min_each_cat: function() {
		var min_each_cat = [];
		$each(this.filtered_datasets.slice(0, -1), function(el, ind) {
			min_each_cat[ind] = el.min();
		}, this);
		this.stat_obj["min_each_cat"] = min_each_cat;
		this.string_stat_obj["min_each_cat"] = this.to_cats_pairs(min_each_cat);	
	},

	get_min_all: function() {
		var min_all = this.filtered_datasets.getLast().min(); // max from category All
		this.stat_obj["min_all"] = min_all;
		this.string_stat_obj["min_all"] = min_all;			
	},

	get_average_sum_all: function(d1, d2) {
		// average sum for one day.
		var average_sum_all = 0;
		var sum_all = this.stat_obj["sum_each_cat"].getLast(); // sum for category All
		var period_in_days = (d2 - d1) / this.day_in_ms;
		average_sum_all = sum_all / period_in_days; 
		this.stat_obj["average_sum_all"] = average_sum_all.round(1);
		this.string_stat_obj["average_sum_all"] = average_sum_all.round(1);
	},

	get_average_sum_each_cat: function(d1, d2) {
		var average_sum_each_cat = [];
		var sum_each_cat = this.stat_obj["sum_each_cat"].slice(0, -1); // list of sum for each cat
		var period_in_days = (d2 - d1) / this.day_in_ms;	
		$each(sum_each_cat, function(el, ind) {
			var average_sum = el / period_in_days;
			average_sum_each_cat.append([average_sum.round(1)]);
		}, this);
		this.stat_obj["average_sum_each_cat"] = average_sum_each_cat;	
		this.string_stat_obj["average_sum_each_cat"] = this.to_cats_pairs(average_sum_each_cat);
	},

	get_modal: function(l, ind) {
		var modal_prices = [];
		var modal_interval = 25;
		var i = 0;
		var run = true;
		while (run) {
			modal_prices.append([l.filter(function(el) {
				return (el >= i * modal_interval) && (el < (i+1) * modal_interval);
			}).length]);
			i += 1;
			if ((i * modal_interval) > this.stat_obj["max_each_cat"][ind]) run = false;
		}
		console.log(modal_prices);
		max_val = modal_prices.max(true);
		if ((modal_prices.length - modal_prices.slice().erase(max_val).length) > 1 || modal_prices.length == 1) {
			return "Нет моды";
		}
		max_modal_ind = modal_prices.indexOf(max_val);
		modal_price = max_modal_ind * modal_interval + ' - ' + (max_modal_ind + 1) * modal_interval;
		return modal_price;
	},

	get_modal_each_cat: function() {
		var modals_list = [];
		$each(this.filtered_datasets, function(el, ind) {
			modals_list[ind] = this.get_modal(listobj_to_list(el, "price"), ind);
		}, this);
		this.stat_obj["modal_all"] = modals_list.getLast();
		this.string_stat_obj["modal_all"] = modals_list.getLast();
		this.stat_obj["modal_each_cat"] = modals_list.slice(0, -1);
		this.string_stat_obj["modal_each_cat"] = this.to_cats_pairs(modals_list.slice(0, -1));		
	},

	update_stat: function(d1, d2) { 
		this.filter_datasets(d1, d2);
		this.get_sum_each_cat();
		this.get_max_all();
		this.get_min_all();
		this.get_max_each_cat();
		this.get_min_each_cat();
		this.get_average_sum_all(d1, d2);
		this.get_average_sum_each_cat(d1, d2);
		this.get_modal_each_cat();
		var stat_list = [];
		//var from_date = d1.toLocaleString();
		//var to_date = d2.toLocaleString();
		var from_date = d1.toDateString() + ' ' + d1.toTimeString().slice(0,8);
		var to_date = d2.toDateString() + ' ' + d2.toTimeString().slice(0,8);
		var statistics_header = '<p>Статистика за период: <b>' + from_date + '</b> по <b>' + to_date + '</b></p>';
		statistics_header = statistics_header.substitute(this.stat_obj);
		this.stat_header_holder.set('html', statistics_header);
		stat_list.append(['<table>']);
		stat_list.append(['<tr><td>Сумма по каждому виду карт, руб:</td> <td>{sum_each_cat}</td></tr>']);
		stat_list.append(['<tr><td>Максимальный платеж в целом, руб:</td> <td> {max_all}</td></tr>']);
		stat_list.append(['<tr><td>Минимальный платеж в целом, руб:</td> <td> {min_all}</td></tr>']);
		stat_list.append(['<tr><td>Максимальный платеж по каждому виду карт, руб:</td> <td> {max_each_cat}</td></tr>']);
		stat_list.append(['<tr><td>Минимальный платеж по каждому виду карт, руб:</td> <td> {min_each_cat}</td></tr>']);
		stat_list.append(['<tr><td>Средняя общая сумма за день, руб:</td> <td> {average_sum_all}</td></tr>']);
		stat_list.append(['<tr><td>Средняя сумма за день по каждому виду карт, руб:</td> <td> {average_sum_each_cat}</td></tr>']);
		stat_list.append(['<tr><td>Модальный платеж в целом, руб:</td> <td> {modal_all}</td></tr>']);
		stat_list.append(['<tr><td>Модальный платеж по каждому виду карт, руб:</td> <td> {modal_each_cat}</td></tr>']);
		stat_list.append(['</table>']);
		var stat_string = stat_list.to_nice_str(true);
		stat_string = stat_string.substitute(this.string_stat_obj);
		this.stat_holder.set('html', stat_string);
		nice_table();
	},

});