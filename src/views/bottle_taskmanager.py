# taskmanager.py
#
# Copyright 2022 brombinmirko <send@mirko.pm>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, in version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gettext import gettext as _
from gi.repository import Gtk

from bottles.utils.threading import RunAsync  # pyright: reportMissingImports=false
from bottles.backend.runner import Runner
from bottles.backend.wine.winedbg import WineDbg
from bottles.backend.wine.winebridge import WineBridge


@Gtk.Template(resource_path='/com/usebottles/bottles/details-taskmanager.ui')
class TaskManagerView(Gtk.ScrolledWindow):
    __gtype_name__ = 'TaskManagerView'

    # region Widgets
    treeview_processes = Gtk.Template.Child()
    actions = Gtk.Template.Child()
    btn_update = Gtk.Template.Child()
    btn_kill = Gtk.Template.Child()

    # endregion

    def __init__(self, details, config, **kwargs):
        super().__init__(**kwargs)

        # common variables and references
        self.window = details.window
        self.manager = details.window.manager
        self.config = config

        self.btn_update.connect("clicked", self.sensitive_update)
        self.btn_kill.connect("clicked", self.kill_process)
        self.treeview_processes.connect("cursor-changed", self.show_kill_btn)

        # apply model to treeview_processes
        self.liststore_processes = Gtk.ListStore(str, str, str)
        self.treeview_processes.set_model(self.liststore_processes)

        cell_renderer = Gtk.CellRendererText()
        i = 0

        for column in [
            "PID",
            "Name",
            "Threads",
            # "Parent"
        ]:
            '''
            For each column, add it to the treeview_processes
            '''
            column = Gtk.TreeViewColumn(column, cell_renderer, text=i)
            self.treeview_processes.append_column(column)
            i += 1

        self.update()

    def set_config(self, config):
        self.config = config

    def show_kill_btn(self, widget):
        selected = self.treeview_processes.get_selection()
        model, treeiter = selected.get_selected()
        if model is None or len(model) == 0:
            self.btn_kill.set_sensitive(False)
            return
        self.btn_kill.set_sensitive(True)

    def update(self, widget=False, config=None):
        """
        This function scan for new processed and update the
        liststore_processes with the new data
        """
        if config is None:
            config = {}
        self.config = config
        if not config.get("Runner"):
            return

        self.liststore_processes.clear()
        winebridge = WineBridge(config)

        if winebridge.is_available():
            processes = winebridge.get_procs()
        else:
            winedbg = WineDbg(config)
            processes = winedbg.get_processes()

        if len(processes) > 0:
            for process in processes:
                self.liststore_processes.append([
                    process.get("pid"),
                    process.get("name", "n/a"),
                    process.get("threads", "0"),
                    # process.get("parent", "0")
                ])

    def sensitive_update(self, widget):
        def reset(result, error):
            self.btn_update.set_sensitive(True)

        self.btn_update.set_sensitive(False)
        RunAsync(
            task_func=self.update,
            callback=reset,
            widget=False,
            config=self.config
        )

    def kill_process(self, widget):
        winebridge = WineBridge(self.config)
        selected = self.treeview_processes.get_selection()
        model, treeiter = selected.get_selected()

        if model is None:
            self.btn_kill.set_sensitive(False)
            return

        pid = model[treeiter][0]
        self.btn_kill.set_sensitive(False)

        def reset(result, error):
            self.liststore_processes.remove(treeiter)

        if winebridge.is_available():
            RunAsync(
                task_func=winebridge.kill_proc,
                callback=reset,
                pid=pid
            )
        else:
            winedbg = WineDbg(self.config)
            RunAsync(
                task_func=winedbg.kill_process,
                callback=reset,
                pid=pid
            )
