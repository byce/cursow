#!/usr/bin/env python2
import curses
from curses import panel
from .widget import widget
from .common import *

class columnList(widget):
	"""
	Displays a list of data with columns
	List can be sorted and filtered arbitrarily

	Inherited methods:
	hide(self)
	show(self)
	getPanel(self)
	getWindow(self)
	"""

	class column(object):#{{{
		"""
		Column object for columnList

		The columnList class should provide the interface for
		this class. An external class should never have to 
		explicitly interface with this class
		"""
		def __init__(self, width, data, title):#{{{
			"""
			Column constructor

			arguments:
			width -- w > 1, then width in pixels, w<1 then percentage free space
			data -- function returning an items value, ie: data = lambda x: x.name
			title -- display title of the column
			"""
			self.width = width
			self.data = data
			self.title = title
			self.highlight = False#}}}
		
		def setHighlight( self, highlight ):#{{{
			"""
			Highlight column title when displayed

			arguments:
			highlight -- True if title should be in reverse mode, false otherwise
			"""
			self.highlight = highlight#}}}
		#}}}

	def __init__(self, window):#{{{
		"""
		Create item holders and fake filters

		arguments:
		window -- the curses window of the widget
		"""
		## Sort/filter function
		self.sortkey = lambda x: True
		self.filter = lambda x: True

		## Item holders
		self.columns = []
		self.items = []
		self.filteredItems = []

		## Position variables
		self.row = 0
		self.firstrow = 0

		## Display variables
		self.displayItems = {} # Dictionary is convenience to avoid some invalid-index checks
		self.spacers = 2

		super( columnList, self ).__init__( window )#}}}

	def resize(self, height, width, y0=None, x0=None):#{{{
		"""
		Resize and/or move the window

		arguments:
		height -- resized height
		width -- resized width
		y0 -- y coord of new top-left corner (default = self.y0)
		x0 -- x coord of new top-left corner (default = self.x0)
		"""
		self.scaleColumns()
		super( columnList, self ).resize( height, width, y0, x0 )#}}}

	def display(self):#{{{
		"""
		Draw column headers and items
		Attempts to refresh only what has been updated
		"""
		if not self.columns or not self.filteredItems:
			self.window.move(0, 0)
			self.window.clrtobot()
			self.window.nooutrefresh()
			return
	
		## Print column headers
		x = 1
		for column in self.columns:
			w = column.width if column.width >= 1 else int( column.width * ( self.width - self.spacers ) )
			mode = curses.A_REVERSE * column.highlight
			self.window.addstr( 0, x, column.title[:w].ljust( w ), mode )
			x += w+1

		for y in xrange( 1 , self.height ):
			## get item if it exists
			index = self.firstrow + y - 1

			if index >= len( self.filteredItems ):
				self.window.move( y , 0 )
				self.window.clrtobot()
				break
			item = self.filteredItems[ index ]

			if self.displayItems.get( y, False ) == item:
				continue
			else:
				self.displayItems[ y ] = item

			mode = curses.A_REVERSE * ( index == self.row )
			self.window.addstr( y, 1, ''.ljust(self.width-2), mode )
			x = 1
			for column in self.columns:
				w = column.width if column.width >= 1 else int( column.width * ( self.width - self.spacers ) )
				self.window.addstr( y, x, column.data(item)[:w].ljust( w ), mode )
				x += w+1

		self.window.nooutrefresh()#}}}

	def clear(self):#{{{
		"""
		Clear the display and mark all rows
		of the list for refresh
		"""
		self.displayItems = {}
		super( columnList , self ).clear()#}}}

	def focus( self ):
		"""
		TODO
		"""
		pass

	def handleInput( self, key ):#{{{
		"""
		Handles a given keypress

		arguments:
		key -- ord(ch) of character pressed
		"""
		if key in KEY_QUIT:
			return
		elif key in KEY_UP:
			self.move( -1 )
		elif key in KEY_UP5:
			self.move( -5 )
		elif key in KEY_PGUP:
			self.move( -self.height + 1 )
		elif key in KEY_DOWN:
			self.move( 1 )
		elif key in KEY_DOWN5:
			self.move( 5 )
		elif key in KEY_PGDOWN:
			self.move( self.height - 1 )#}}}

	def move( self, n ):#{{{
		"""
		Move selection down by amount n
		Negative n moves up, will scroll
		display if necessary

		arguments:
		n -- amount to move by
		"""
		if n == 0:
			return

		self.displayItems[ 1 + self.row - self.firstrow ] = False
		self.row += n
		self.displayItems[ 1 + self.row - self.firstrow ] = False

		## Do we even have items? Or is it top of list?
		if not self.filteredItems or self.row < 0:
			if self.firstrow != 0:
				self.displayItems = {}
				self.firstrow = 0
			else:
				self.displayItems[ 1 ] = False
			self.row = 0

		## End of list?
		if self.row >= len( self.filteredItems ):
			self.row = len( self.filteredItems ) - 1
			self.displayItems[ 1 + self.row ] = False

		## Scroll down?
		if self.row - self.firstrow > self.height - 2:
			self.firstrow = self.row - self.height + 2
			self.displayItems = {}

		## Scroll up?
		if self.row < self.firstrow:
			self.firstrow = self.row
			self.displayItems = {}

		self.display()#}}}
		
	def addItem(self, item):#{{{
		"""
		Add an item, and resort/display it
		if it matches current filter

		argument:
		item -- item to add
		"""
		self.items.append( item )
		if self.filter( item ):
			self.filteredItems.append( item )
			self.filteredItems = sorted( self.filteredItems, key=self.sortkey )
		self.display()#}}}

	def getItem(self, index):#{{{
		"""
		Return the item at a given index
		from self.items

		arguments:
		index -- index of wanted item
		"""
		return self.items[ index ]#}}}

	def getItems(self):#{{{
		"""
		Return item list
		"""
		return self.items#}}}

	def getFilteredItems(self):#{{{
		"""
		Return filtered item list
		"""
		return self.filteredItems#}}}

	def getSelectedItem(self):#{{{
		"""
		Return currently highlighted item
		"""
		return self.items[ self.row ]#}}}

	def setFilter( self, filt ):#{{{
		"""
		set the lists filtering function

		arguments:
		filt -- new filter function for list
		"""
		self.filter = filt
		self.filteredItems = sorted( filter( self.filter, self.items ), key=self.sortkey )#}}}
	
	def setSortKey( self, sortkey ):#{{{
		"""
		set the lists sorting function

		arguments
		sortkey -- new sort function for list
		"""
		self.sortkey = sortkey
		self.filteredItems = sorted( self.filteredItems, self.sortkey )#}}}

	def addColumn( self, width, data, title ):#{{{
		"""
		Wrapper to construct and add a column

		arguments:
		width -- w > 1, then width in pixels, w<1 then percentage free space
		data -- function returning an items value, ie: data = lambda x: x.name
		title -- display title of the column
		"""
		for column in self.columns:
			if column.title == title:
				raise cuiException('addColumn failed: Column with title %s already exists!' % title)
		col = self.column( width, data, title )
		self.columns.append( col )
		self.scaleColumns()#}}}
	
	def highlightColumn( self, title ): #{{{
		"""
		Highlight the column with given title
		All other columns are de-highlighted

		arguments:
		title -- tile of column to highlight
		"""
		for column in self.columns:
			if column.title == title:
				column.setHighlight( True )
			else:
				column.setHighlight( False )##}}}

	def scaleColumns(self):#{{{
		"""
		Calculate deadspace used
		as spacers between columns
		"""
		self.spacers = 1
		for column in self.columns:
			if column.width >= 1:
				self.spacers += column.width
			self.spacers += 1#}}}
