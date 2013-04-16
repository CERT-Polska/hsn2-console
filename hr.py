#!/usr/bin/python

# Copyright (c) NASK, NCSC
# 
# This file is part of HoneySpider Network 2.0.
# 
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys, os
import logging
import ConfigParser

sys.path.append("/opt/hsn2/python/commlib")

from aliases import Aliases
import argparsealiases as argparse

import couchdb
import itertools
from collections import defaultdict

class DocumentWithChildren:
	def __init__(self, document):
		self.document = document
		self.children = []
		self.value = document.value

	def addChild(self, child):
		self.children.append(child)

	def __repr__(self):
		return self.document.id

class Printer:
	def __init__(self, formatting_class, **init_args):
		self.formatting_class = formatting_class
		self.args = init_args

	def get(self, documents, sorting_key = None, filtering = lambda x: True):
		for document in sorted(documents, key = lambda d: d.value.get(sorting_key)):
			if filtering(document):
				yield self.formatting_class(document, **self.args)

class ListPrinter(Printer):
	def display(self, documents, sorting_key = None, filtering = lambda x: True):
		for line in self.get(documents, sorting_key, filtering):
			print unicode(line)

class TreePrinter(Printer):
	def display(self, documents, sorting_key = None, level = 0, filtering = lambda x: True):
		for line in self.get(documents, sorting_key, filtering):
			if level == 0:
				print
			print '  '* level + unicode(line)
			self.display(line.document.children, sorting_key, level = level + 1)
			

class DocumentFormatter:
	def __init__(self, document, format):
		self.document = document
		self.format = format

	def __str__(self):
		return self.format.format(**self.document.value)

class ColorDocumentFormatter(DocumentFormatter):
	COLORS = {
		'red':'\033[0;31m', 
		'yellow':'\033[0;33m', 
		'green': '\033[0;32m',
		'normal': '',
		}

	def __init__(self, document, format, color_name, color_dict):
		DocumentFormatter.__init__(self, document, format)
		self.format = '{color_start}' + self.format + '{color_end}'
		self.color_name = color_name
		self.color_dict = color_dict

	def __str__(self):
		formatting = self.document.value
		formatting['color_end'] = '\033[0m'
		formatting['color_start'] = ColorDocumentFormatter.COLORS[self.color_dict.get(formatting[self.color_name], 'normal')]
		return self.format.format(**formatting)


def createParser():
	parser = argparse.ArgumentParser()
	parser.add_argument("--config", "-c", default="/etc/hsn2/console.conf", dest="configuration")
	subparsers = parser.add_subparsers()

	parser_list = subparsers.add_parser("list", aliases = ["l"])
	parser_list.add_argument("job_id")
	parser_list.add_argument("--sort", "-s", dest="sort", choices=["object_id", "classification", "origin"])
	parser_list.add_argument("--color", dest="color", choices=["auto", "always", "never"], default="auto")
	parser_list.add_argument("--tree", "-t", dest="tree", action='store_true', default=False)
	parser_list.add_argument("--classification", "-c", dest="classification")
	parser_list.set_defaults(func = listJobs)

	parser_deploy = subparsers.add_parser("deploy", aliases = ["d"])
	parser_deploy.add_argument("--directory", "-d", default = "/etc/hsn2/views/")
	parser_deploy.set_defaults(func = deployViews)

	parser_summary = subparsers.add_parser("summary", aliases = ["u"])
	parser_summary.add_argument("job_id")
	parser_summary.set_defaults(func = summary)
	return parser

def summary(db, args):
	documents = db.view('hr/classification_by_job_id',  startkey = [args.job_id], endkey=[args.job_id, {}], group = True)
	for document in documents:
		print document.key[1] + ':'
		total = 0
		for element, value in document.value.iteritems():
			total += value
			print u' {:<10}: {:<5}'.format(element, value)
		print ' TOTAL     : {}'.format(total)
		print

def configparse(args):
	config = ConfigParser.ConfigParser()
	try:
		ret = config.read(args.configuration)
	except IOError:
		sys.stderr.write('Cannot read configuration file')
		sys.exit(1)
	return config

def listJobs(db, args):
	documents = db.view('hr/list_by_job_id',  key = args.job_id)
	format = u'{object_id:>6}  {classification:<.1}  {origin:<.1}  {display}'

	if args.color == 'always' or (args.color == 'auto' and sys.stdout.isatty()):
		colors = {'malicious': 'red'} #, 'benign': 'green'}
		if args.tree:
			printer = TreePrinter(ColorDocumentFormatter, format = format, color_name = 'classification', color_dict = colors)
		else:
			printer = ListPrinter(ColorDocumentFormatter, format = format, color_name = 'classification', color_dict = colors)
	else:
		if args.tree:
			printer = TreePrinter(DocumentFormatter, format = format)
		else:
			printer = ListPrinter(DocumentFormatter, format = format)

	if args.tree:
		documents = [DocumentWithChildren(document) for document in documents]
		roots = []
		nodes = {}
		for doc in documents:
			nodes[int(doc.value['object_id'])] = doc
		for doc in documents:
			if 'parent' in doc.value:
				nodes[doc.value['parent']].addChild(doc)
			else:
				roots.append(doc)
		documents = roots
	filters = [lambda x: True]
	if args.classification:
		filters.append(lambda x: x.value['classification'] == args.classification)
	printer.display(documents, sorting_key = args.sort, filtering = lambda x: False not in [f(x) for f in filters])

def deployViews(db, args):
        viewDoc = {     "_id" : "_design/hr",
                        "language" : "javascript",
                        "views" : {},
                        }

        for filename in os.listdir(args.directory):
                viewFile = os.path.join(args.directory, filename)
                view = {}
                viewDoc["views"][filename] = view
                for suffix in ["map", "reduce"]:
                        filename = os.path.join(viewFile, suffix + ".js")
                        if os.path.exists(filename):
                                with open(filename) as f:
                                        view[suffix] = f.read()
        try:
                db.save(viewDoc)
        except couchdb.http.ResourceConflict:
                rev = db.revisions(viewDoc["_id"]).next().rev
                viewDoc['_rev'] = rev
                db.save(viewDoc)


def getCouchDb(args):
	config = configparse(args)
	server = couchdb.Server('http://%s:%s/' % (config.get('couchdb', 'server'), config.get('couchdb', 'port')))
        return server[config.get('couchdb', 'db')]

def main():
	args = createParser().parse_args()
	db = getCouchDb(args)
	args.func(db, args)

if __name__ == '__main__':
	main()
