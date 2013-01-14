# -*- coding: utf-8 -*-

import os
from os import path
import csv
from datetime import date, time, timedelta
import json
from Tkinter import *
from jinja2 import Environment, FileSystemLoader

class BaseGraph(object):
	"""
	Base operations with time, date, data formatting
	"""
	def __init__(self, csv_table_name, delimiter, categories_list, date_delimiter, templates_path, reports_path):
		self.csv_table_name = csv_table_name
		self.delimiter = delimiter
		self.categories_list = categories_list
		self.date_delimiter = date_delimiter
		self.get_table_data()
		self.env = Environment(loader=FileSystemLoader(templates_path))
		self.reports_path = reports_path

	def rel(self, arg):
		return path.join(path.dirname(__file__), arg)

	def is_service(self, row):
		if int(row[0]) > 1000:
			return True
		else:
			return False

	def get_date_enter(self, row):
		return row[1]

	def get_time_enter(self, row):
		return row[2]

	def get_category_type(self, row):
		return row[7]

	def get_price(self, row):
		return int(row[8])

	def get_minutes_spanded(self, row):
		return row[6]
	
	def get_table_data(self):
		tablename = self.rel(self.csv_table_name)
		#print tablename
		table = open(tablename, 'rU')
		table_reader = csv.reader(table, delimiter=self.delimiter)
		#print table_reader
		table_list = [row for row in table_reader]
		#print table_list
		table.close()
		self.table_data = table_list[1:]

		#print self.table_data
		for line in self.table_data:
			print line
		print '*' * 30

	def string_to_date(self, d):
		d = [int(i) for i in d.split(self.date_delimiter)]
		d = date(d[2],d[0], d[1])
		return d

	def date_to_string(self, d):
		return d.strftime('%Y-%m-%d-%H-%M')

	def cmp_dates(self, date_1, date_2):  # return 2 (>), 1 (==) or 0 (<)
		# format year, month, day
	    date_1 = self.string_to_date(date_1)
	    date_2 = self.string_to_date(date_2)
	    return cmp(date_1, date_2) + 1

	def cmp_times(self, time_1, time_2): # return 2 (>), 1 (==) or 0 (<)
	    time_1 = [int(i) for i in time_1.split(':')]
	    time_2 = [int(i) for i in time_2.split(':')]
	    # format hour, minute
	    time_1 = time(time_1[0], time_1[1])
	    time_2 = time(time_2[0], time_2[1])
	    return cmp(time_1, time_2) + 1

	def date_time_enter_str(self, row):
		MM, DD, YYYY = row[1].split(self.date_delimiter)
		hh, mm = row[2].split(':')
		date_time_enter_str = '%s-%s-%s-%s-%s' % (YYYY, MM, DD, hh, mm)
		return date_time_enter_str

	def get_time_in_out_pair(self, row):
		time_enter = self.get_time_enter(row)
		h_in, min_in = map(int, time_enter.split(':'))
		h_in = h_in + min_in / 60.0
		min_spanded = int(self.get_minutes_spanded(row))
		h_out = h_in + min_spanded / 60.0
		
		if h_out > 24:
			h_out = 24
		return (h_in, h_out)

	def filter_rows(self, date_begin, date_end=None, time_begin=None, time_end=None):
	    # we always have the some start date
	    filtered_data = [row for row in self.table_data if \
	    	self.cmp_dates(self.get_date_enter(row), date_begin)] 
	    # but not always have end date
	    if date_end is not None:
	        filtered_data = [row for row in filtered_data if self.cmp_dates(date_end, self.get_date_enter(row))]
	    if time_begin is not None and time_end is not None:
	        filtered_data = [row for row in filtered_data if \
	            (cmp_times(self.get_time_enter(row), time_begin) and self.cmp_times(time_end, self.get_time_enter(row)))]

	    return filtered_data
	
	def replace_empty_lists(self, l):
		res = []
		for i in l:
			if i == []:
				res.append([0])
			else:
				res.append(i)
		return res

	def nice_float(self, f):
		f = float(f)	# if f is string
		if f.is_integer():
			return int(f)
		else:
			return float('%.2f' % f)

	def cat_value_pairs(self, values_list):
		return [(self.categories_list[ind], self.nice_float(value)) for ind, value in enumerate(values_list)]

	def render_template(self, template_name, context_dict):
		t = self.env.get_template(template_name)
		return t.render(context_dict).encode('utf-8')
	
	def write_report(self, report_name, data_dict):
		path_to_report = os.path.join(self.reports_path, report_name)
		f = open(path_to_report, 'w')
		f.write(self.render_template(report_name, data_dict))
		f.close()


class CTBAGraph(BaseGraph):
	def __init__(*args):
		BaseGraph.__init__(*args)

	def plot_graph_1(self, data_filename):
		# date_time format is YYYY-MM-DD-HH-MM-00
		table_data = [row for row in self.table_data if not self.is_service(row)]
		first_date = self.string_to_date(self.get_date_enter(self.table_data[0]))
		last_date = self.string_to_date(self.get_date_enter(self.table_data[-1]))
		one_day = timedelta(days=1)
		first_date_str = self.date_to_string(first_date - one_day)
		last_date_str = self.date_to_string(last_date + one_day)

		datasets = [
			[{'date_time': self.date_time_enter_str(row), 'price': self.get_price(row)} \
				for row in table_data if (self.get_category_type(row) == cat)] \
			for cat in self.categories_list
		]

		# assume that times is unique (minimum diff is 1 minute)
		all_dataset = [
			{'date_time': self.date_time_enter_str(row), 'price': self.get_price(row)} \
				for row in table_data
		]
		datasets.append(all_dataset)

		# it seems that amcharts needs sorted data array,
		# so insert first date to 0 position, while last date to last position
		for dataset in datasets:
			dataset.insert(0, {'date_time': first_date_str, 'price': 0});
			dataset.append({'date_time': last_date_str, 'price': 0});
		
		graph_1_data_file = open(data_filename, 'w')
		for ind, dataset in enumerate(datasets):
			graph_1_data_file.write('var chartData%d = ' % (ind))
			json.dump(dataset, graph_1_data_file)
			graph_1_data_file.write(';\n')
		graph_1_data_file.close()
		print 'graph 1 is successfully plotted' 

	def plot_graph_2(self, d1, d2):
		"""
		graph_2, average day data for period from d1 to d2
		simultaneous means one hour period
		"""
		
		if d1 == d2:
			from_to_string = d1
		else:
			from_to_string = '%s - %s' % (d1, d2)
		
		# period from monday to tuesday is 2 days
		number_of_days = (self.string_to_date(d2)-self.string_to_date(d1)).days + 1
		if number_of_days <= 0:
			print 'error occured on graph 2'
			return
		filtered_data = self.filter_rows(d1, d2)
		filtered_data = [row for row in filtered_data if not self.is_service(row)]
		if not filtered_data:
			print 'no data for graph_2'
			return
		hours_list = range(0, 24)
	    # 9.00 - from 9 to 10 interval, 8.00 - from 8 to 9 interval.
		# [(0, [1,0,0,0,1]), (1, [2,3,0,1,1]), ...]
		# data in pairs is already averaged for number_of_days
		pairs = [(h, [len([row for row in filtered_data if (self.cmp_times(self.get_time_enter(row), '%d:00' % h) \
	            and self.cmp_times('%d:00' % (h+1), self.get_time_enter(row)) == 2 and \
	            self.get_category_type(row) == category)]) / float(number_of_days) \
	            for category in self.categories_list] \
		) for h in hours_list]

		"""
		pairs_for_modal_period = [(h, len([row for row in filtered_data if (cmp_times(row[2], '%d:00' % h) \
				and cmp_times('%d:00' % (h+1), row[2]) == 2 \
				and ((h+1) > int(row[6])/60.0))]) / float(number_of_days)) \
		for h in hours_list]

		modal_periods = [(i,i+1) for i,m in pairs_for_modal_period if \
			m == max([p for k,p in pairs_for_modal_period])]
		print modal_periods 
		"""

		cat_numbers_list = [pair[1] for pair in pairs]	
		sum_people_for_each_cat = [sum(cat_numbers[i] for cat_numbers in cat_numbers_list) \
			for i in range(len(self.categories_list))]
		
		average_people_for_each_cat = ['%f' % (i / (24.0 )) for i in sum_people_for_each_cat]
		
		# sum of sum for all categories / 24 hours
		average_people_all = sum([sum(pair[1]) for pair in pairs]) / (24.0)

		# sum of people for each category
		sum_all_cat = [sum(pair[1]) for pair in pairs]
		max_people_period_all = [(i,i+1) for i,m in enumerate(sum_all_cat) if m == max(sum_all_cat)]
		min_people_period_all = [(i,i+1) for i,m in enumerate(sum_all_cat) if m == min(sum_all_cat)]
		
		# max people simultaneously for each cat
		max_people_simult_for_each_cat = \
			[max(cat_numbers[cat] for cat_numbers in cat_numbers_list) \
			for cat in range(len(self.categories_list))]

		# list of time spended
		times_list = [int(row[6]) for row in filtered_data]
		min_time_spended_all = min(times_list)
		max_time_spended_all = max(times_list)
		times_list_for_each_cat = [[(int(row[6])) for row in filtered_data \
			if self.get_category_type(row) == cat] \
			for cat in self.categories_list
		]

		# number of rows in filtered_data can be less than number of categories
		# so we filter out empty lists		
		times_list_for_each_cat = self.replace_empty_lists(times_list_for_each_cat)
		max_time_spended_for_each_cat = [max(t) for t in times_list_for_each_cat]
		min_time_spended_for_each_cat = [min(t) for t in times_list_for_each_cat]

		graph_2_data = []	# data for graph plotting
		for h, p in pairs:
			temp_d = {}
			temp_d['time'] = h
			temp_d['all'] = self.nice_float(sum(p))
			for cat in self.categories_list:
				temp_d[cat] = self.nice_float(p[self.categories_list.index(cat)])
			graph_2_data.append(temp_d)

		chartData = json.dumps(graph_2_data)

		# write graph_2 data and statistics
		
		context_dict = {
			'chartData': chartData,
			'from_to_string': from_to_string,
			'sum_people_for_each_cat': self.cat_value_pairs(sum_people_for_each_cat),
			'average_people_for_each_cat': self.cat_value_pairs(average_people_for_each_cat),
			'average_people_all': self.nice_float(average_people_all),
			'max_people_simult_for_each_cat': self.cat_value_pairs(max_people_simult_for_each_cat),
			'min_time_spended_for_each_cat': self.cat_value_pairs(min_time_spended_for_each_cat),
			'min_time_spended_all': self.nice_float(min_time_spended_all),
			'max_time_spended_for_each_cat': self.cat_value_pairs(max_time_spended_for_each_cat),
			'max_time_spended_all': self.nice_float(max_time_spended_all),
			'min_people_period_all': min_people_period_all,
			'max_people_period_all': max_people_period_all
		}
		
		self.write_report('graph_2.html', context_dict)
		print 'graph 2 is successfully plotted'

	def plot_graph_3(self, d, header_filename, picture_filename):
		import sys
		sys.path.append('/opt/local/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/site-packages')
		
		import cairo
		import cairoplot
		from random import random
		"""
		time in is row[2]
		time out is row[4]
		minutes_spanded is row[6]
		"""
		#f = open(header_filename, 'w')
		#f.write('var graph_3_header = "Учет рабочего времени сотрудников за %s"' % d)
		#f.close()
		
		self.write_report('graph_3.html', {'graph_3_date': d})
		
		v_legend = map(str, range(25))
		
		graph_3_data = [row for row in self.filter_rows(d, d) if self.is_service(row)]
		if not graph_3_data:
			cairoplot.gantt_chart(picture_filename, [[(5,19)]], 1000, 900, ['no_data',], v_legend, [(1,0,0),])
			print 'graph 3 successfully plotted. no data'
			return

		unique_ids = set([row[0] for row in graph_3_data])
		grouped_data = {}

		# bug or feature of cairoplot:
		# if there was one time_in_out for each id - we should
		# wrap each time_in_out pair in list, ex. [[(3, 6)], [(8, 12)]]
		# else: we should not 
		# that's why we use several_mode flag
		several_mode = False
		for client_id in unique_ids:
			client_id_rows = [row for row in graph_3_data if row[0] == client_id]
			if len(client_id_rows) > 1:
				several_mode = True
				time_in_out = [self.get_time_in_out_pair(row) for row in client_id_rows]
			else:
				time_in_out = self.get_time_in_out_pair(client_id_rows[0])
			
			grouped_data[client_id] = time_in_out
		
		if several_mode:
			pieces = grouped_data.values()
		else:
			pieces = map(lambda x: [x], grouped_data.values())
		h_legend = map(lambda x: 'id ' + x, grouped_data.keys())
		
		colors = [(random(), random(), random()) for piece in pieces]
		
		cairoplot.gantt_chart(picture_filename, pieces, 1000, 900, h_legend, v_legend, colors)
		print 'graph 3 successfully plotted'


class CTBAUI(Frame):
	def __init__(self, parent, ctba_graph_inst):
		Frame.__init__(self, parent, borderwidth=5)
	
		self.parent = parent
		self.ctba_graph_inst = ctba_graph_inst
		self.master_config()

		self.init_UI()

	def master_config(self):
		for row_number in range(8):
			self.rowconfigure(row_number, pad=8)
		for col_number in range(2):
			self.columnconfigure(col_number, pad=4)

		self.pack()
	
	def init_UI(self):

		self.init_graph_1()
		self.init_graph_2()
		self.init_graph_3()	

	def init_graph_1(self):
		self.graph_1_title = Label(self, text="График 1")
		self.graph_1_title.grid(row=0, column=0, columnspan=3, sticky=E+W)		
		
		self.graph_1_bt = Button(self, text="График 1: Обновить данные", \
		command = self.plot_graph_1)
		self.graph_1_bt.grid(row=1, column=0, columnspan=3, sticky=E+W)

	def init_graph_2(self):
		self.graph_2_title = Label(self, text="График 2")
		self.graph_2_title.grid(row=2, column=0, columnspan=3, sticky=E+W)		
		
		self.graph_2_lb1 = Label(self, text="Дата (от):")
		self.graph_2_lb1.grid(row=3, column=0)		

		self.graph_2_data1 = Entry(self)
		self.graph_2_data1.grid(row=3, column=1)
		#self.graph_2_data_1.bind("<Return>", self.plot_graph_2)

		self.graph_2_lb2 = Label(self, text="Дата (до):")
		self.graph_2_lb2.grid(row=4, column=0)		

		self.graph_2_data2 = Entry(self)
		self.graph_2_data2.grid(row=4, column=1)
		#self.graph_2_data2.bind("<Return>", self.plot_graph_2)

		self.graph_2_bt = Button(self, text="построить график 2", \
		command = self.plot_graph_2)
		self.graph_2_bt.grid(row=3, column=2, rowspan=2)

	def init_graph_3(self):
		self.graph_3_title = Label(self, text="График 3")
		self.graph_3_title.grid(row=5, column=0, columnspan=3, sticky=E+W)		
		
		self.graph_3_lb = Label(self, text="Дата:")
		self.graph_3_lb.grid(row=6, column=0)

		self.graph_3_data = Entry(self)
		self.graph_3_data.grid(row=6, column=1)

		self.graph_3_bt = Button(self, text="построить график 3", \
		command = self.plot_graph_3)
		self.graph_3_bt.grid(row=6, column=2)
		
		self.message = Message(self, bg="green")
		self.message.grid(row=7, column=0, columnspan=3, sticky=E+W)

	def plot_graph_1(self):
		self.ctba_graph_inst.plot_graph_1('js/graph_1_data.js')

	def plot_graph_2(self):
		user_data1 = self.graph_2_data1.get()
		user_data2 = self.graph_2_data2.get()
		v1 = self.validate_data(user_data1)
		v2 = self.validate_data(user_data2)
		if v1 and v2:
			self.message['text'] = 'ok'
			self.message['bg'] = 'green'
			self.ctba_graph_inst.plot_graph_2(user_data1, user_data2)
			#graph_2(user_data1, user_data2)	
		else:
			self.message['text'] = 'bad'
			self.message['bg'] = 'red'		
		#except Exception, m:
		#	self.message['text'] = m

	def plot_graph_3(self):
		user_data = self.graph_3_data.get()
		v = self.validate_data(user_data)
		if v:
			self.message['text'] = 'ok'
			self.message['bg'] = 'green'
			self.ctba_graph_inst.plot_graph_3(user_data, 'js/graph_3_header.js', 'js/graph_3.png')
		else:
			self.message['text'] = 'bad'
			self.message['bg'] = 'red'
	
	def validate_data(self, d):
		d = map(str.isdigit, d.split('.'))
		if False in d:
			return False
		else:
			return True


g = CTBAGraph('csv_test_table_1.csv', ';', ['A', 'B', 'C', 'D', 'E'], '.', 'templates/', 'reports/')

root = Tk()
root.title('CTBA')
app = CTBAUI(root, g)
root.mainloop()