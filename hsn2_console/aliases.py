#!/usr/bin/python -tt

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


class Aliases():

    def __init__(self):
        self.commandAliases = {
            'job': 'j',
            'workflow': 'w',
            'config': 'c',
            'ping': 'p',
        }

        self.subCommandAliases = {
            'job': {
                'list': 'l',
                'details': 'd',
                'submit': 's'
            },
            'workflow': {
                'list': 'l',
                'get': 'g',
                'enable': 'e',
                'disable': 'd',
                'upload': 'u',
                'history': 'h',
                'status': 's'
            },
            'config': {
                'set': 's',
                'get': 'g'
            }
        }

        self.commandFullNames = dict(zip(self.commandAliases.values(), self.commandAliases.keys()))
        self.subCommandFullNames = dict()
        for name in self.subCommandAliases.keys():
            self.subCommandFullNames[name] = dict(zip(self.subCommandAliases[name].values(), self.subCommandAliases[name].keys()))

    def getAliases(self, key, context=None):
        if (context is None):
            src = self.commandAliases
        else:
            src = self.subCommandAliases.get(context, {})
        val = src.get(key, None)
        if (val is not None):
            val = [val]
        else:
            val = []
        return val

    def getFullName(self, key, context=None):
        if (context is None):
            src = self.commandFullNames
        else:
            src = self.subCommandFullNames.get(context, {})
        val = src.get(key, None)
        if (val is None):
            val = key
        return val
