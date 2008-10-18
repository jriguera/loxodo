#
# Loxodo -- Password Safe V3 compatible Password Vault
# Copyright (C) 2008 Christoph Sommer <mail@christoph-sommer.de>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

import os
import wx

from vault import Vault
from recordframe import RecordFrame

class VaultFrame(wx.Frame):

    """
    Displays (and lets the user edit) the Vault.
    """

    class VaultListCtrl(wx.ListCtrl):

        """
        wx.ListCtrl that contains the contents of a Vault.
        """

        def __init__(self, *args, **kwds):
            wx.ListCtrl.__init__(self, *args, **kwds)
            self.vault = None
            self._filterstring = ""
            self.displayed_entries = []
            self.InsertColumn(0, "Title")
            self.InsertColumn(1, "User")
            self.InsertColumn(2, "Group")
            self.SetColumnWidth(0, 256)
            self.SetColumnWidth(1, 128)
            self.SetColumnWidth(2, 256)
            self.sort_function = lambda e1, e2: cmp(e1.group, e2.group)
            self.Refresh()

        def OnGetItemText(self, item, col):
            """
            Return display text for entries of a virtual list

            Overrides the base classes' method.
            """
            if (col == 0):
                return self.displayed_entries[item].title
            if (col == 1):
                return self.displayed_entries[item].user
            if (col == 2):
                return self.displayed_entries[item].group
            return "--"

        def Refresh(self):
            """
            Update the visual representation of list.

            Extends the base classes' method.
            """
            if not self.vault:
                self.displayed_entries = []
                return
            self.displayed_entries = [record for record in self.vault.records if ((record.title.lower().find(self._filterstring.lower()) >= 0) or (record.group.lower().find(self._filterstring.lower()) >= 0))]

            self.displayed_entries.sort(self.sort_function)
            self.SetItemCount(len(self.displayed_entries))
            wx.ListCtrl.Refresh(self)

        def set_vault(self, vault):
            """
            Set the Vault this control should display.
            """
            self.vault = vault
            self.Refresh()

        def set_filter(self, filterstring):
            """
            Sets a filter string to limit the displayed entries
            """
            self._filterstring = filterstring
            self.Refresh()

    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        wx.EVT_CLOSE(self, self._on_frame_close)

        self.panel = wx.Panel(self, -1)

        self.list = self.VaultListCtrl(self.panel, -1, size=(640, 240), style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_VIRTUAL|wx.LC_EDIT_LABELS)
        self.statusbar = self.CreateStatusBar(1, wx.ST_SIZEGRIP)

        # Set up menus
        filemenu = wx.Menu()
        filemenu.Append(wx.ID_ABOUT, "&About", "Information about this program")
        wx.EVT_MENU(self, wx.ID_ABOUT, self._on_about)
        filemenu.AppendSeparator()
        filemenu.Append(wx.ID_EXIT, " E&xit", "Terminate the program")
        wx.EVT_MENU(self, wx.ID_EXIT, self._on_exit)
        entrymenu = wx.Menu()
        entrymenu.Append(wx.ID_ADD, "&Add\tCtrl+A", "Add a new record, ...")
        wx.EVT_MENU(self, wx.ID_ADD, self._on_add)
        entrymenu.Append(wx.ID_DELETE, "&Delete\tCtrl+Back", "Delete this record")
        wx.EVT_MENU(self, wx.ID_DELETE, self._on_delete)
        entrymenu.AppendSeparator()
        entrymenu.Append(wx.ID_EDIT, "&Edit\tCtrl+E", "Change this record's username, password, ...")
        wx.EVT_MENU(self, wx.ID_EDIT, self._on_edit)
        entrymenu.AppendSeparator()
        entrymenu.Append(wx.ID_VIEW_DETAILS, "Copy &Username\tCtrl+U", "Copy this record's username to the clipboard")
        wx.EVT_MENU(self, wx.ID_VIEW_DETAILS, self._on_copy_username)
        entrymenu.Append(wx.ID_COPY, "Copy &Password\tCtrl+P", "Copy this record's password to the clipboard")
        wx.EVT_MENU(self, wx.ID_COPY, self._on_copy_password)
        menu_bar = wx.MenuBar()
        menu_bar.Append(filemenu,"&Vault")
        menu_bar.Append(entrymenu,"&Record")
        self.SetMenuBar(menu_bar)

        self.SetTitle("Vault Contents")
        self.list.SetFocus()
        self.statusbar.SetStatusWidths([-1])
        statusbar_fields = [""]
        for i in range(len(statusbar_fields)):
            self.statusbar.SetStatusText(statusbar_fields[i], i)

        sizer = wx.BoxSizer(wx.VERTICAL)
        _rowsizer = wx.BoxSizer(wx.HORIZONTAL)
        self._searchbox = wx.SearchCtrl(self.panel, size=(200, -1))
        self._searchbox.ShowCancelButton(True)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self._on_search_cancel, self._searchbox)
        self.Bind(wx.EVT_TEXT, self._on_search_do, self._searchbox)

        _rowsizer.Add(self._searchbox, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, 5)
        sizer.Add(_rowsizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        sizer.Add(self.list, 1, wx.EXPAND, 0)
        self.panel.SetSizer(sizer)
        _sz_frame = wx.BoxSizer()
        _sz_frame.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(_sz_frame)

        sizer.Fit(self)
        self.Layout()

        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_list_item_activated, self.list)
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self._on_list_item_label_edit, self.list)
        self.Bind(wx.EVT_LIST_COL_CLICK, self._on_list_column_click, self.list)

        self.vault_file_name = None
        self.vault_password = None
        self.vault = Vault()
        self._recordframe = RecordFrame(self, -1, "")
        self._recordframe.refresh_subscriber = self
        self._is_modified = False

    def on_modified(self):
        self.mark_modified()

    def mark_modified(self):
        self._is_modified = True
        if ((self.vault_file_name is not None) and (self.vault_password is not None)):
            self.save_vault(self.vault_file_name, self.vault_password)
        self.list.Refresh()

    def open_vault(self, filename, password):
        """
        Set the Vault that this frame should display.
        """
        self.vault_file_name = None
        self.vault_password = None
        self._is_modified = False
        self.vault = Vault()
        self.vault.read_from_file(filename, password)
        self.list.set_vault(self.vault)
        self.vault_file_name = filename
        self.vault_password = password
        self.statusbar.SetStatusText("Read Vault contents from disk", 0)

    def save_vault(self, filename, password):
        """
        Set the Vault that this frame should display.
        """
        self._is_modified = False
        self.vault_file_name = filename
        self.vault_password = password
        self.vault.write_to_file(filename, password)
        self.statusbar.SetStatusText("Wrote Vault contents to disk", 0)

    def _copy_to_clipboard(self, text):
        if not wx.TheClipboard.Open():
            raise RuntimeError("Could not open clipboard")
        try:
            clip_object = wx.TextDataObject(text)
            wx.TheClipboard.SetData(clip_object)
            clip_object.clear_after_get = True
        finally:
            wx.TheClipboard.Close()

    def _on_list_item_activated(self, event):
        """
        Event handler: Fires when user double-clicks a list entry.
        """
        index = event.GetIndex()
        entry = self.list.displayed_entries[index]
        try:
            self._copy_to_clipboard(entry.passwd)
            self.statusbar.SetStatusText('Copied password of "'+entry.title+'" to clipboard', 0)
        except RuntimeError:
            self.statusbar.SetStatusText('Error copying password of "'+entry.title+'" to clipboard', 0)

    def _on_list_item_label_edit(self, event):
        """
        Event handler: Fires when user edits an entry's label.
        """
        index = event.GetIndex()
        entry = self.list.displayed_entries[index]
        label_str = event.GetLabel()
        old_title = entry.title
        entry.title = label_str
        self.list.Refresh()
        if ((not self._recordframe is None) and (self._recordframe.IsShown())):
            self._recordframe.Refresh()
        self.statusbar.SetStatusText('Changed title of "'+old_title+'"', 0)
        self.mark_modified()

    def _on_list_column_click(self, event):
        """
        Event handler: Fires when user clicks on the list header.
        """
        col = event.GetColumn()
        if (col == 0):
            self.list.sort_function = lambda e1, e2: cmp(e1.title, e2.title)
        if (col == 1):
            self.list.sort_function = lambda e1, e2: cmp(e1.user, e2.user)
        if (col == 2):
            self.list.sort_function = lambda e1, e2: cmp(e1.group, e2.group)
        self.list.Refresh()

    def _on_about(self, dummy):
        """
        Event handler: Fires when user chooses this menu item.
        """

        gpl_v2 = "\n\n".join((
                              "This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.",
                              "This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.",
                              "You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.",
                              ))

        developers = (
                      "Christoph Sommer",
                      "Bjorn Edstrom (Python Twofish)",
                      "Brian Gladman (C Twofish)",
                      )

        about = wx.AboutDialogInfo()
        about.SetIcon(wx.Icon(os.path.join(os.path.dirname(__file__), "..", "resources", "loxodo-icon.png"), wx.BITMAP_TYPE_PNG, 128, 128))
        about.SetName("Loxodo")
        about.SetVersion("0.0-git")
        about.SetCopyright("Copyright (C) 2008 Christoph Sommer <mail@christoph-sommer.de>")
        about.SetWebSite("http://www.christoph-sommer.de/loxodo")
        about.SetLicense(gpl_v2)
        about.SetDevelopers(developers)
        wx.AboutBox(about)

    def _on_exit(self, dummy):
        """
        Event handler: Fires when user chooses this menu item.
        """
        self.Close(True)  # Close the frame.

    def _on_edit(self, dummy):
        """
        Event handler: Fires when user chooses this menu item.
        """
        index = self.list.GetFirstSelected()
        if (index is None):
            return
        entry = self.list.displayed_entries[index]
        self._recordframe.vault_record = entry
        self._recordframe.Show()
        self._recordframe.Raise()

    def _on_add(self, dummy):
        """
        Event handler: Fires when user chooses this menu item.
        """
        entry = self.vault.Record()
        self.vault.records.append(entry)
        self.mark_modified()
        self._recordframe.vault_record = entry
        self._recordframe.Show()
        self._recordframe.Raise()

    def _on_delete(self, dummy):
        """
        Event handler: Fires when user chooses this menu item.
        """
        index = self.list.GetFirstSelected()
        if (index == -1):
            return
        entry = self.list.displayed_entries[index]

        if ((entry.user != "") or (entry.passwd != "")):
            dial = wx.MessageDialog(self,
                                    'Are you sure you want to delete this record? It contains a username or password and there is no way to undo this action.',
                                    'Really delete record?',
                                    wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION
                                    )
            retval = dial.ShowModal()
            dial.Destroy()
            if retval != wx.ID_YES:
                return

        if (entry == self._recordframe.vault_record):
            self._recordframe.Hide()
            self._recordframe.vault_record = None
        self.vault.records.remove(entry)
        self.mark_modified()

    def _on_copy_username(self, dummy):
        """
        Event handler: Fires when user chooses this menu item.
        """
        index = self.list.GetFirstSelected()
        if (index == -1):
            return
        entry = self.list.displayed_entries[index]
        try:
            self._copy_to_clipboard(entry.user)
            self.statusbar.SetStatusText('Copied username of "'+entry.title+'" to clipboard', 0)
        except RuntimeError:
            self.statusbar.SetStatusText('Error copying username of "'+entry.title+'" to clipboard', 0)

    def _on_copy_password(self, dummy):
        """
        Event handler: Fires when user chooses this menu item.
        """
        index = self.list.GetFirstSelected()
        if (index == -1):
            return
        entry = self.list.displayed_entries[index]
        try:
            self._copy_to_clipboard(entry.user)
            self.statusbar.SetStatusText('Copied password of "'+entry.title+'" to clipboard', 0)
        except RuntimeError:
            self.statusbar.SetStatusText('Error copying password of "'+entry.title+'" to clipboard', 0)

    def _on_search_do(self, dummy):
        """
        Event handler: Fires when user interacts with search field
        """
        self.list.set_filter(self._searchbox.GetValue())

    def _on_search_cancel(self, dummy):
        """
        Event handler: Fires when user interacts with search field
        """
        self._searchbox.SetValue("")

    def _on_frame_close(self, dummy):
        """
        Event handler: Fires when user closes the frame
        """
        self.Destroy()