# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Library with various helper functions for Qt widgets
"""

import logging
logger = logging.getLogger(__name__)

from .pyfda_lib import qstr

from .compat import QFrame, QMessageBox, Qt
from .pyfda_dirs import OS

#------------------------------------------------------------------------------
def qwindow_stay_on_top(win, top):
    """
    Set flags for a window such that it stays on top (True) or not

    On Windows (7) the new window stays on top anyway (check for Win10),
    Additionally setting WindowStaysOnTopHint blocks the message window when
    trying to close pyfda.
    """

    win_flags = (Qt.CustomizeWindowHint | Qt.Window |# always needed
                Qt.WindowTitleHint | # show title bar, make window movable
                Qt.WindowCloseButtonHint | # show close button
                Qt.WindowContextHelpButtonHint | # right Mousebutton context menu
                Qt.WindowMinMaxButtonsHint) # show min/max buttons

    if OS == "Windows" or not top:
        win.setWindowFlags(win_flags)
    else:
        win.setWindowFlags(win_flags | Qt.WindowStaysOnTopHint)

#------------------------------------------------------------------------------
def qcmb_box_populate(cmb_box, items_list, item_init):
    """
    Clear and populate combo box `cmb_box` with text, data and tooltip from the list 
    `items_list` with initial selection of `init_item` (data).
    
    Text and tooltip are prepared for translation via `self.tr()`
    
    Parameters
    ----------
    
    cmb_box: instance of QComboBox
        Combobox to be populated
        
    items_list: list
        List of combobox entries, in the format
        [ "Tooltip for Combobox",
         ("data 1st item", "text 1st item", "tooltip for 1st item"),
         ("data 2nd item", "text 2nd item", "tooltip for 2nd item")]
        
    item_init: str
        data for initial positition of combobox. When data is not found,
        set combobox to first item.

    Returns
    -------
    None
    """
    cmb_box.clear()
    cmb_box.setToolTip(cmb_box.tr(items_list[0]))
    for i in range(1, len(items_list)):
        cmb_box.addItem(cmb_box.tr(items_list[i][1]), items_list[i][0])
        cmb_box.setItemData(i-1, cmb_box.tr(items_list[i][2]), Qt.ToolTipRole)
    qset_cmb_box(cmb_box, item_init, data=True)

    """ icon = QIcon('logo.png') 
    # adding icon to the given index 
    self.combo_box.setItemIcon(i, icon) 
    size = QSize(10, 10) 
    self.combo_box.setIconSize(size)  """

#------------------------------------------------------------------------------
def qget_cmb_box(cmb_box, data=True):
    """
    Get current itemData or Text of comboBox and convert it to string.

    In Python 3, python Qt objects are automatically converted to QVariant
    when stored as "data" e.g. in a QComboBox and converted back when
    retrieving. In Python 2, QVariant is returned when itemData is retrieved.
    This is first converted from the QVariant container format to a
    QString, next to a "normal" non-unicode string.

    Returns:

    The current text or data of combobox as a string
    """
    if data:
        idx = cmb_box.currentIndex()
        cmb_data = cmb_box.itemData(idx)
        cmb_str = qstr(cmb_data) # convert QVariant, QString, string to plain string
    else:
        cmb_str = cmb_box.currentText()

    cmb_str = str(cmb_str)

    return cmb_str

#------------------------------------------------------------------------------
def qset_cmb_box(cmb_box, string, data=False, fireSignals=False, caseSensitive=False):
    """
    Set combobox to the index corresponding to `string` in a text field (`data = False`)
    or in a data field (`data=True`). When `string` is not found in the combobox entries,
    select the first entry. Signals are blocked during the update of the combobox unless
    `fireSignals` is set `True`. By default, the search is case insensitive, this
    can be changed by passing `caseSensitive=False`.

    Parameters
    ----------

    string: str
        The label in the text or data field to be selected. When the string is
        not found, select the first entry of the combo box.

    data: bool (default: False)
        Whether the string refers to the data or text fields of the combo box

    fireSignals: bool (default: False)
        When True, fire a signal if the index is changed (useful for GUI testing)

    caseInsensitive: bool (default: False)
        When true, perform case sensitive search.

    Returns
    -------
        The index of the string. When the string was not found in the combo box,
        return index -1.
    """
    if caseSensitive:
        flag = Qt.MatchFixedString | Qt.MatchCaseSensitive
    else:
        flag = Qt.MatchFixedString # string based matching (case insensitive)

    # Other more or less self explanatory flags:
    # MatchExactly (default), MatchContains, MatchStartsWith, MatchEndsWith,
    # MatchRegExp, MatchWildcard, MatchRecursive

    if data:
        idx = cmb_box.findData(str(string), flags=flag) # find index for data = string
    else:
        idx = cmb_box.findText(str(string), flags=flag) # find index for text = string

    ret = idx

    if idx == -1: # data does not exist, use first entry instead
        idx = 0

    cmb_box.blockSignals(not fireSignals)
    cmb_box.setCurrentIndex(idx) # set index
    cmb_box.blockSignals(False)

    return ret

#------------------------------------------------------------------------------
def qcmb_box_del_item(cmb_box, string, data=False, fireSignals=False, caseSensitive=False):
    """
    Try to find the entry in combobox corresponding to `string` in a text field (`data = False`)
    or in a data field (`data=True`) and delete the item. When `string` is not found,
    do nothing. Signals are blocked during the update of the combobox unless
    `fireSignals` is set `True`. By default, the search is case insensitive, this
    can be changed by passing `caseSensitive=False`.

    Parameters
    ----------

    string: str
        The label in the text or data field to be deleted.

    data: bool (default: False)
        Whether the string refers to the data or text fields of the combo box

    fireSignals: bool (default: False)
        When True, fire a signal if the index is changed (useful for GUI testing)

    caseInsensitive: bool (default: False)
        When true, perform case sensitive search.

    Returns
    -------
        The index of the item with string / data. When not found in the combo box,
        return index -1.
    """
    if caseSensitive:
        flag = Qt.MatchFixedString | Qt.MatchCaseSensitive
    else:
        flag = Qt.MatchFixedString # string based matching (case insensitive)

    # Other more or less self explanatory flags:
    # MatchExactly (default), MatchContains, MatchStartsWith, MatchEndsWith,
    # MatchRegExp, MatchWildcard, MatchRecursive

    if data:
        idx = cmb_box.findData(str(string), flags=flag) # find index for data = string
    else:
        idx = cmb_box.findText(str(string), flags=flag) # find index for text = string

    if idx > -1: # data  / text exists in combo box, delete it.
        cmb_box.blockSignals(not fireSignals)
        cmb_box.removeItem(idx) # set index
        cmb_box.blockSignals(False)

    return idx

#------------------------------------------------------------------------------
def qcmb_box_add_item(cmb_box, item_list, data=True, fireSignals=False, 
                      caseSensitive=False):
    """
    Add an entry in combobox with text / data / tooltipp from `item_list`. 
    When the item is already in combobox (searching for data or text item, depending
    `data`), do nothing. Signals are blocked during the update of the combobox unless
    `fireSignals` is set `True`. By default, the search is case insensitive, this
    can be changed by passing `caseSensitive=False`.

    Parameters
    ----------

    item_list: list
        List with `["new_data", "new_text", "new_tooltip"]` to be added.

    data: bool (default: False)
        Whether the string refers to the data or text fields of the combo box

    fireSignals: bool (default: False)
        When True, fire a signal if the index is changed (useful for GUI testing)

    caseInsensitive: bool (default: False)
        When true, perform case sensitive search.

    Returns
    -------
        The index of the found item with string / data. When not found in the
        combo box, return index -1.
    """
    if caseSensitive:
        flag = Qt.MatchFixedString | Qt.MatchCaseSensitive
    else:
        flag = Qt.MatchFixedString # string based matching (case insensitive)

    # Other more or less self explanatory flags:
    # MatchExactly (default), MatchContains, MatchStartsWith, MatchEndsWith,
    # MatchRegExp, MatchWildcard, MatchRecursive

    if data:
        idx = cmb_box.findData(item_list[0], flags=flag) # find index for data 
    else:
        idx = cmb_box.findText(item_list[1], flags=flag) # find index for text

    if idx == -1: # data  / text doesn't exist in combo box, add it.
        cmb_box.blockSignals(not fireSignals)
        cmb_box.addItem(cmb_box.tr(item_list[1]), item_list[0]) # set index
        idx = cmb_box.findData(item_list[0])
        cmb_box.setItemData(idx, cmb_box.tr(item_list[2]), Qt.ToolTipRole)
        cmb_box.blockSignals(False)
        
    return idx

#------------------------------------------------------------------------------
def qstyle_widget(widget, state):
    """
    Apply the "state" defined in pyfda_rc.py to the widget, e.g.:
    Color the >> DESIGN FILTER << button according to the filter design state.

    - "normal": default, no color styling
    - "ok":  green, filter has been designed, everything ok
    - "changed": yellow, filter specs have been changed
    - "error" : red, an error has occurred during filter design
    - "failed" : orange, filter fails to meet target specs
    - "u" or "unused": grey text color
    - "d" or "disabled": background color darkgrey
    - "a" or "active": no special style defined
    """
    state = str(state)
    if state == 'u':
        state = "unused"
        # *[state="unused"], *[state="u"]{background-color:white; color:darkgrey}
    elif state == 'a':
        state = "active"
    elif state == 'd':
        state = "disabled"
        # QLineEdit:disabled{background-color:darkgrey;}
    widget.setProperty("state", state)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


#------------------------------------------------------------------------------
def qget_selected(table, select_all=False, reverse=True):
    """
    Get selected cells in ``table`` and return a dictionary with the following keys:

    'idx': indices of selected cells as an unsorted list of tuples

    'sel': list of lists of selected cells per column, by default sorted in reverse

    'cur':  current cell selection as a tuple

    Parameters
    ----------

    select_all : bool
        select all table items and create a list when True

    reverse : bool
        return selected fields upside down when True
    """
    if select_all:
        table.selectAll()

    idx = []
    for _ in table.selectedItems():
        idx.append([_.column(), _.row(), ])

    sel = [[], []]
    sel[0] = sorted([i[1] for i in idx if i[0] == 0], reverse = reverse)
    sel[1] = sorted([i[1] for i in idx if i[0] == 1], reverse = reverse)

    if select_all:
        table.clearSelection()

    # use set comprehension to eliminate multiple identical entries
    # cols = sorted(list({i[0] for i in idx}))
    # rows = sorted(list({i[1] for i in idx}))
    cur = (table.currentColumn(), table.currentRow())
    # cur_idx_row = table.currentIndex().row()
    return {'idx':idx, 'sel':sel, 'cur':cur}# 'rows':rows 'cols':cols, }

#------------------------------------------------------------------------------
def qfilter_warning(self, N, fil_class):
    """
    Pop-up a warning box for very large filter orders
    """
    reply = QMessageBox.warning(self, 'Warning',
        ("<span><i><b>N = {0}</b></i> &nbsp; is a rather high order for<br />"
         "an {1} filter and may cause large <br />"
         "numerical errors and compute times.<br />"
         "Continue?</span>".format(N, fil_class)),
         QMessageBox.Yes, QMessageBox.No)
    if reply == QMessageBox.Yes:
        return True
    else:
        return False

#------------------------------------------------------------------------------
class QHLine(QFrame):
    """
    Create a thin horizontal line utilizing the HLine property of QFrames
    Usage:
        myline = QHLine()
        mylayout.addWidget(myline)
    """
    def __init__(self, width=1):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Plain)       
        self.setLineWidth(width)


class QVLine(QFrame):
    def __init__(self, width=1):
        super(QVLine, self).__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Plain)
        #self.setStyleSheet('border-color: rgb(50,50,50)')  
        #self.setFrameShadow(QFrame.Sunken)
        #self.setLineWidth(width)
        #self.setFrameShape(QFrame.StyledPanel);
        self.setStyleSheet( "border-width: 2px; border-top-style: none; border-right-style: solid; border-bottom-style: none; border-left-style: solid; border-color: grey; ");
        
#==============================================================================

if __name__=='__main__':
    pass
