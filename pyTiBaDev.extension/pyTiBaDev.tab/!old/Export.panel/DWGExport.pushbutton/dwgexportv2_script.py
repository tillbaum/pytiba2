"""PDFsOut: - Active Sheet Selection in ProjectBrowser
		   	  or, if nothing selected,
            - Selection in Sheet-Selection-Dialog
			- Printer Adobe PDF, """

# TODO, CHECK Imports, what do I need??
import clr
import sys
import os
import string #?
#from collections import OrderedDict 
#import threading
from functools import wraps 

from pyrevit import HOST_APP, EXEC_PARAMS
from pyrevit.compat import safe_strtype  # Func
#from pyrevit import coreutils
#from pyrevit.coreutils.logger import get_logger
from pyrevit import framework
from pyrevit.framework import System
#from pyrevit.framework import Threading 
from pyrevit.framework import Interop #What is this?? 
from pyrevit.framework import Controls, Media  # needed?

clr.AddReference('IronPython.Wpf')
import wpf

from pyrevit.api import AdWindows 
from pyrevit import revit, UI, DB 
import pyrevit.forms 

#logger = get_logger(__name__) 

DEFAULT_INPUTWINDOW_WIDTH = 500
DEFAULT_INPUTWINDOW_HEIGHT = 400

__title__ = "DWG\nExport"

__author__ = "TBaumeister"

# for timing ------------------------------------------------
from pyrevit.coreutils import Timer
timer = Timer()

import clr # import common language runtime .Net Laufzeitumgebung 
from System.Collections.Generic import List 
from System.Windows import Forms #
from Autodesk.Revit.DB import *
#( FilteredElementCollector, BuiltInCategory, Transaction, TransactionGroup, OfClass)
import pyrevit 
from pyrevit import forms 
import rpw.ui.forms as rpwforms # FlexForm, Label, ComboBox, TextBox, \
								# Separator, Button, CheckBox, Alert 

pyt_path = (r'C:\Program Files (x86)\IronPython 2.7\Lib') 
sys.path.append(pyt_path)
# tb_path 
tblib_path = (r'E:\pyRevit\tblib')
sys.path.append(tblib_path)
pyrevitpath = r"E:\pyRevitv4.5\pyRevit\pyrevitlib"
sys.path.append(pyrevitpath)
import math	 # math.ceil
from math import ceil  
#this way of importing takes much less momory, and is faster! python cookbook! 
import time # sleep() 
import traceback
import cPickle as pickle
from pyrevit import script

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

#when running in RPS
try:
	__file__
except NameError: 
	__file__ = "E:\\pyRevit\\tblib\\"

#*** Assign ListContent to multiple variables 
# Revit usage: Sheetlist of size 5: v0 = sheetlist[0], v1 = ....
def list2var(list, string = "a"):
    for i,j in enumerate(list):
        globals()['{}{}'.format(string, i)] = j
    print "len(list)= ",len(list)

# func to print items in list, 
def lprint(ls):
	for i in ls: print(i) 

def pick_folder():
    fb_dlg = Forms.FolderBrowserDialog()
    if fb_dlg.ShowDialog() == Forms.DialogResult.OK:
        return fb_dlg.SelectedPath

class SelectFromCheckBoxes(framework.Windows.Window): 
    """ tb_Modified Standard form to select from a list of check boxes.
    """
    xaml_source = 'tb_SelectFromCheckboxesDwg.xaml' 

# copied from TemplateUserInputWindow ---------------------------
    def __init__(self, context,
                 title='User Input',
                 width=DEFAULT_INPUTWINDOW_WIDTH,
                 height=DEFAULT_INPUTWINDOW_HEIGHT, **kwargs):
        """Initialize user input window."""
        wpf.LoadComponent(self, os.path.join(os.path.dirname(__file__), self.xaml_source))
        self.Title = title
        self.Width = width
        self.Height = height
        self.Left = System.Windows.SystemParameters.FullPrimaryScreenWidth / 2 - self.Width /2
        self.Top = 50

        self._context = context #private attr.
        self.response = None 	#see select button

        def handle_ESCinput_key( sender, args):
            """Handle Escape keyboard input"""
            if args.Key == framework.Windows.Input.Key.Escape:
                self.Close()
                sys.exit() #TODO! sysExit. READ
        self.PreviewKeyDown += handle_ESCinput_key # ESC closes the form

		# in def setup( **kwargs)
        self.hide_element(self.clrsearch_b) # func in WPFWindow
        self.search_tb.Focus()

        self.checked_only = kwargs.get('checked_only', False) # get() builtin

        button_name = kwargs.get('button_name', None)
        if button_name:
            self.select_b.Content = button_name
        self.list_lb.SelectionMode = Controls.SelectionMode.Extended
        self._verify_context()
        self._list_options()

		#tb_ADDED: Values from Checkbox and Textinput --------------------------
        self.dic_dlgval = {}
        with open(os.path.dirname(__file__) + "\\dlgval.pkl", "a+b") as f: # create and read
            f.seek(0)
            try:
                self.dic = pickle.load(f)
            except: print "run again"
        try: 
            self.dic # if dic not exists -> Except clause 
            #print self.dic # testing
            self.txtbox_paranames.Text = self.dic["paranames"]

            firstdwgsetting = FilteredElementCollector(doc).OfClass(ExportDWGSettings) \
													.FirstElement()
            currentactiveset= firstdwgsetting.GetActivePredefinedSettings(doc)
            self.txtbox_dwgsetting.Text = currentactiveset.Name
            self.txtblock_expander.Text =   "Filename:       " + self.dic["paranames"] \
										+ "\nExportSetup:  " + self.txtbox_dwgsetting.Text \
										#+ "\nExportPath:" + self.dic["filepath"]s
            self.lb_filepath.Content = self.dic["filepath"]
            self.chbox_output.IsChecked = self.dic["output"]
            self.chbox_dwgexport.IsChecked = self.dic["dwgexport"]
        except:
            import traceback
            errorReport = traceback.format_exc()
            print(errorReport) 
			#Standard Dialog Values
            self.txtbox_paranames.Text = "Sheet Number,-,Sheet Name"
            self.txtblock_expander.Text = "Sheet Number,_,Sheet Name"
            self.chbox_output.IsChecked = True
            
# copied from WMFWindow
    @staticmethod # e.g can be applied to the class and the instance, both
    def hide_element(*wpf_elements):
        """Collapse elements.

        Args:
            *wpf_elements (str): element names to be collapsed
        """
        for el in wpf_elements:
            el.Visibility = framework.Windows.Visibility.Collapsed

    @staticmethod
    def show_element(*wpf_elements):
        """Show collapsed elements.

        Args:
            *wpf_elements (str): element names to be set to visible.
        """
        for el in wpf_elements:
            el.Visibility = framework.Windows.Visibility.Visible

    @staticmethod
    def toggle_element(*wpf_elements):
        """Toggle visibility of elements.

        Args:
            *wpf_elements (str): element names to be toggled.
        """
        for el in wpf_elements:
            if el.Visibility == framework.Windows.Visibility.Visible:
                self.hide_element(el)
            elif el.Visibility == framework.Windows.Visibility.Collapsed:
                self.show_element(el)
# copied from TemplateUserInputWindow END ---------------------

    def _verify_context(self): 
        new_context = []
        for item in self._context:
            if not hasattr(item, 'state'):
                new_context.append(BaseCheckBoxItem(item))
            else:
                new_context.append(item)

        self._context = new_context

    def _list_options(self, checkbox_filter=None):
        if checkbox_filter:
            self.checkall_b.Content = 'Check'
            self.uncheckall_b.Content = 'Uncheck'
            self.toggleall_b.Content = 'Toggle'
            checkbox_filter = checkbox_filter.lower()
            self.list_lb.ItemsSource = \
                [checkbox for checkbox in self._context
                 if checkbox_filter in checkbox.name.lower()]
        else:
            self.checkall_b.Content = 'Check All'
            self.uncheckall_b.Content = 'Uncheck All'
            self.toggleall_b.Content = 'Toggle All'
            self.list_lb.ItemsSource = self._context

    def _set_states(self, state=True, flip=False, selected=False):
        all_items = self.list_lb.ItemsSource
        if selected:
            current_list = self.list_lb.SelectedItems
        else:
            current_list = self.list_lb.ItemsSource
        for checkbox in current_list:
            if flip:
                checkbox.state = not checkbox.state
            else:
                checkbox.state = state

        # push list view to redraw
        self.list_lb.ItemsSource = None
        self.list_lb.ItemsSource = all_items

    def toggle_all(self, sender, args):
        """Handle toggle all button to toggle state of all check boxes."""
        self._set_states(flip=True)

    def check_all(self, sender, args):
        """Handle check all button to mark all check boxes as checked."""
        self._set_states(state=True)

    def uncheck_all(self, sender, args):
        """Handle uncheck all button to mark all check boxes as un-checked."""
        self._set_states(state=False)

    def check_selected(self, sender, args):
        """Mark selected checkboxes as checked."""
        self._set_states(state=True, selected=True)

    def uncheck_selected(self, sender, args):
        """Mark selected checkboxes as unchecked."""
        self._set_states(state=False, selected=True)

    def button_select(self, sender, args):
        """Handle select button click."""
        if self.checked_only:
            self.response = [x.item for x in self._context if x.state]
        else:
            self.response = self._context
        #tb folowing lines added!
        self.dic_dlgval["paranames"] = self.txtbox_paranames.Text
        self.dic_dlgval["output"] =    self.chbox_output.IsChecked
        self.dic_dlgval["dwgexport"] = self.chbox_dwgexport.IsChecked
        self.dic_dlgval["filepath"] =  self.lb_filepath.Content
        self.Close()

    # tb previewbutton: breview_b
    def preview_click(self, sender, event):
        ''' Handle Preview Button click '''
        str2list = self.txtbox_paranames.Text.split(',')
        #stripwhitespacefrlistelem = list(map(str.strip, str2list))
        paranameseval = namefromparalist(FilteredElementCollector(doc)
									.OfClass(ViewSheet).FirstElement(),str2list)
        self.lb_txtbox_preview.Text = paranameseval

    def pickfolder(self, sender, event):
        self.lb_filepath.Content = pick_folder()

    def search_txt_changed(self, sender, args):
        """Handle text change in search box."""
        if self.search_tb.Text == '':
            self.hide_element(self.clrsearch_b)
        else:
            self.show_element(self.clrsearch_b)

        self._list_options(checkbox_filter=self.search_tb.Text)

    def clear_search(self, sender, args):
        """Clear search box."""
        self.search_tb.Text = ' '
        self.search_tb.Clear()
        self.search_tb.Focus()

class BaseCheckBoxItem(object):
    """Base class for checkbox option wrapping another object."""

    def __init__(self, orig_item):
        """Initialize the checkbox option and wrap given obj.

        Args:
            orig_item (any): object to wrap (must have name property
                             or be convertable to string with str()
        """
        self.item = orig_item
        self.state = False

    def __nonzero__(self):
        return self.state

    def __str__(self):
        return self.name or str(self.item)

    @property
    def name(self):
        """Name property."""
        return getattr(self.item, 'name', '') #getattr() python built in func 

    def unwrap(self):
        """Unwrap and return wrapped object."""
        return self.item

class SheetOption(BaseCheckBoxItem):
    def __init__(self, sheet_element):
        super(SheetOption, self).__init__(sheet_element)

    @property
    def name(self):
        return '{} - {}{}' \
            .format(self.item.SheetNumber,
                    self.item.Name,
                    ' (placeholder)' if self.item.IsPlaceholder else '')

    @property
    def number(self):
        return self.item.SheetNumber

#func lookuppara; paraname as string: ex: "Sheet Number"
#TODO: maybe replace with orderedParameters, or ParameterSet, 
def lookupparaval(element, paraname): 
	try: newp = element.LookupParameter(paraname)
	except: newp = None; pass 
	if newp:
		if newp.StorageType == StorageType.String:    value = newp.AsString()
		elif newp.StorageType == StorageType.Integer: value = newp.AsInteger()
		elif newp.StorageType == StorageType.Double:  value = newp.AsDouble()
		return value
	else: return False

def namefromparalist(view, paralist):
	import datetime
	m = datetime.datetime.now()
	date = m.strftime("%d-%m-%y") #stringformattime fun
	time = m.strftime("%H.%M")
	tmp_filenamelist = []
	for i in paralist: 
		if i in ['_', ' ', '.', '-', ';']:
			tmp_filenamelist.append(i)
		elif i in ["date", "time"]:
			datetime = m.strftime(eval(i))
			tmp_filenamelist.append(datetime)
		#elif i in ["%d","%m","%y","%Y","%H","%M"]:
		elif i.startswith("%"):
			try:
				datetime = m.strftime(i)
				tmp_filenamelist.append(datetime)
			except: pass
		elif lookupparaval(view, i):
			lookupval = lookupparaval(view, i)
			# str(lookupval) if lookupval else '' 
			tmp_filenamelist.append(str(lookupval) if lookupval else '')
		else: 
			tmp_filenamelist.append(i)
	filename = ''.join(tmp_filenamelist)
	return filename

def filenamelist(viewlist, paralist, dirpath):
	filepathlist = []
	filenamelist = []
	for v in viewlist: 
		tmpname = namefromparalist(v, paralist)
		tmpname += ".pdf" 
		filenamelist.append(tmpname)
		filepathlist.append(dirpath + "\\" + tmpname )
	return (filepathlist, filenamelist)

def open_dic(fn="dlgval.pkl"):
	dic1 = {"ouput": True, "paranames": 'Sheet Number,_,Sheet Name'}
	with open(os.path.dirname(__file__) + "\\" + fn, "a+b") as f: # create and read
		f.seek(0)
		try:
			dic = pickle.load(f)
			return dic
		except: return dic1

# write dialogData from input boxes as dictionary.
def write_dic(newdic, olddic=open_dic(), fn= "dlgval.pkl"):
	if newdic and not newdic == olddic:
		with open(os.path.dirname(__file__) + "\\" + fn, "wb") as f:
			pickle.dump(newdic, f)


def selectsheets2print():
	all_sheets = DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet) \
                   .WhereElementIsNotElementType().ToElements()
	sortlist = sorted([SheetOption(x) for x in all_sheets], key=lambda x: x.number)
	selsheet = SelectFromCheckBoxes(sortlist, title = "Select Sheets",
						width = 500, height = 400, 
						button_name = "Select / PRINT")
	selsheet.ShowDialog() #.Net Method, Modal Window, no other window is active
	write_dic(selsheet.dic_dlgval)
	if selsheet.response:
		return ([i.item for i in selsheet.response if i.state], selsheet.dic_dlgval)
	else: 
		sys.exit() #selsheet.response does not exist 

#--- ELEMENT SELECTION ----------------------------------------
selec_el = [doc.GetElement( elId ) for elId in uidoc.Selection.GetElementIds() \
				if doc.GetElement(elId).GetType() == ViewSheet ] 
#---END ELEMENT SELECTION -------------------------------------

output = True 
if selec_el: #exist: 1 or 2, or 3 or ... , not 0
	viewlist = selec_el
	dlgdic = open_dic()
	ouput = dlgdic["output"]
	pdfexport = dlgdic["pdfexport"]
else: 
	viewlist, dlgdic = selectsheets2print()
	output = dlgdic["output"] # True or False 
	dwgexport = dlgdic["dwgexport"]
if not viewlist: 
	sys.exit() #pyrevit.script.exit() 


### FUNCTIONS ############################################################

# Filepath-----------------------------------------------

# scriptpath = script.get_script_path()
# if not scriptpath: 
	# scriptpath = "C:\\Users\\Till\\Desktop"

# if __shiftclick__: 
	# with open(scriptpath + "\\path.txt", "w+") as f: 
		# pass	
	# forms.alert("filepath deleted!")

# fun Export DWG ---------------------------------------------
def ExportDwg(filename, view, folderpath): 
	# DWGExport Options, get Current Active
	firstdwgsetting = FilteredElementCollector(doc).OfClass(ExportDWGSettings) \
													.FirstElement()
	currentactiveset= firstdwgsetting.GetActivePredefinedSettings(doc)
	dwgopt= currentactiveset.GetDWGExportOptions()
	views = List[ElementId]()
	views.Add(view.Id)
	result = doc.Export(folderpath, filename, views, dwgopt) #Revit API func
	return result 

# Create fnlist FUN
#def filenamelist(viewlist, paralist, dirpath = ''):
dirpath = "C:\\"
str2list = dlgdic["paranames"].split(",")

fnlist = filenamelist(viewlist, str2list, dirpath)

# Printing Lists
if output:
	print "---Dialog Values--------------------------------"
	for i in dlgdic.items(): print i

	print("\n--- Viewlist----------------------------------")
	for i in viewlist: 
		print( '{} - {}'.format(i.SheetNumber, i.ViewName))

	print("\n--- FileNamelist------------------------------")
	for i in fnlist[1]: print(i)
	print("\n--- DWG Export -------------------------------")


# Export DWG --- existing files with same name will be overwritten, No Error
if not dlgdic["filepath"]:
	print "--- ExportPath not set! ---"
	sys.exit()

if dlgdic["dwgexport"]:
	try:
		errorReport = None

		for fn, v in zip(fnlist[1], viewlist):
			ExportDwg(fn, v, dlgdic["filepath"])
			if output: 
				print("Success")
	except:
		##when error accurs anywhere in the process catch it
		import traceback
		errorReport = traceback.format_exc()
		print(errorReport)



# TODO Test if the ProcessList is faster than for loop! 
# from Konrad
# def ProcessList(_func, _list):
    # return map( lambda x: ProcessList(_func, x) if type(x)==list else _func(x), _list )

# def ProcessParallelLists(_func, *lists):
	# return map( lambda *xs: ProcessParallelLists(_func, *xs) if all(type(x) is list for x in xs) else _func(*xs), *lists )

# try:
	# errorReport = None
	# run export
	# ProcessParallelLists(ExportDwg, fnlist, viewlist)
# except:
	# if error accurs anywhere in the process catch it
	# import traceback
	# errorReport = traceback.format_exc()

endtime = timer.get_time()
if output:
	print(endtime)
