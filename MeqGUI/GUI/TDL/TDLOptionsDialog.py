# -*- coding: utf-8 -*-
import Timba
from MeqGUI import Grid, GUI, Plugins
from Timba.dmi import *
from Timba.utils import *
from MeqGUI.GUI.pixmaps import pixmaps
from Timba.TDL import TDLOptions

from qtpy.QtCore import QObject, Signal
from qtpy.QtWidgets import (QWidget, QDialog, QVBoxLayout, QHBoxLayout,
       QSizePolicy, QLabel, QPushButton)


import configparser

import os.path

_dbg = verbosity(0,name='tdloptgui');
dprint = _dbg.dprint;
dprintf = _dbg.dprintf;

PROFILE_FILE = "tdlconf.profiles";

ColumnName = 0;
ColumnToolTip =1;
ColumnValue = 2;

class TDLOptionsDialog (QDialog,PersistentCurrier):
  """implements a floating window for TDL options""";
  refreshProfiles = Signal()
  accepted = Signal()

  def __init__ (self,parent,ok_label=None,ok_icon=None):
    QDialog.__init__(self,parent);
    self.setSizeGripEnabled(True);

    lo_main = QVBoxLayout(self);
    # add option treeWidget
    self._tw = QTreeWidget(self);
    self._tw.setColumnCount(3);
    self._tw.setRootIsDecorated(True);
    self._tw.setSortingEnabled(False);
    self._tw.setSelectionMode(QAbstractItemView.NoSelection);

    self._tw.header().setResizeMode(ColumnName,QHeaderView.ResizeToContents);
    self._tw.header().setResizeMode(ColumnToolTip,QHeaderView.ResizeToContents);
    self._tw.header().setResizeMode(ColumnValue,QHeaderView.Stretch);
    self._tw.header().resizeSection(ColumnValue,300);
    self._tw.header().hide();
    self._tw.header().sectionResized[int, int, int].connect(self._resize_dialog)
    self._allow_resize_dialog = True;
    # self._tw.setSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.MinimumExpanding);
    # add signals
    self._tw.itemClicked[QTreeWidgetItem, int].connect(self._process_treewidget_click)
    self._tw.itemActivated[QTreeWidgetItem, int].connect(self._process_treewidget_press)
    # this is emitted when a job button is puhysed in the treewidget -- hide ourselves when this happens
    self._tw.closeWindow.connect(self.hide)
    # self._tw.setMinimumSize(QSize(200,100));
    lo_main.addWidget(self._tw);
    # set geometry
    # self.setMinimumSize(QSize(200,100));
    # self.setGeometry(0,0,200,60);

    # add buttons on bottom
    lo_btn  = QHBoxLayout(None);
    if ok_label:
      if ok_icon:
        self.wok = QPushButton(ok_icon.icon(),ok_label,self);
      else:
        self.wok = QPushButton(ok_label,self);
      lo_btn.addWidget(self.wok);
      self.wok.clicked.connect(self.accept)
    else:
      self.wok = None;
    # addspacer
    spacer = QSpacerItem(40,20,QSizePolicy.Expanding,QSizePolicy.Minimum);
    lo_btn.addItem(spacer)
    # add load button
    self.wload = QToolButton(self);
    self.wload.setText("Load");
    self.wload.setIcon(pixmaps.fileopen.icon());
    self.wload.setToolTip("""<P>Loads current option settings from a named <i>profile</I>.
          Profiles are kept in a file called %s in your current directory.</P>"""%PROFILE_FILE);
    self.wload.setPopupMode(QToolButton.InstantPopup);
    self.wload.setToolButtonStyle(Qt.ToolButtonTextBesideIcon);
    self.load_menu = QMenu(self);
    self.wload.setMenu(self.load_menu);
    lo_btn.addWidget(self.wload);
    # add save button
    self.wsave = QToolButton(self);
    self.wsave.setText("Save");
    self.wsave.setIcon(pixmaps.filesave.icon());
    self.wsave.setToolTip("""<P>Saves current option settings to a named <i>profile</I>.
          Profiles are stored in a file called %s in your current directory.</P>"""%PROFILE_FILE);
    self.wsave.setPopupMode(QToolButton.InstantPopup);
    self.wsave.setToolButtonStyle(Qt.ToolButtonTextBesideIcon);
    self.save_menu = QMenu(self);
    self.wsave.setMenu(self.save_menu);
    lo_btn.addWidget(self.wsave);
    # create the New profile action for the save menu
    self._qa_newprof = QAction("New profile...",self);
    self._qa_newprof.triggered.connect(self._save_new_profile)
    # load profile configuration
    self.refresh_profiles();
    self.refreshProfiles.connect(self.refresh_profiles)
    # add cancel button
    tb = QPushButton(pixmaps.red_round_cross.icon(),"Cancel",self);
    tb.clicked.connect(self.hide)
    spacer = QSpacerItem(40,20,QSizePolicy.Expanding,QSizePolicy.Minimum);
    lo_btn.addItem(spacer)
    lo_btn.addWidget(tb);
    lo_main.addLayout(lo_btn);
    self.resize(QSize(600,480).expandedTo(self.minimumSizeHint()))

  def enableOkButton (self,enable):
    if self.wok:
      self.wok.setEnabled(enable);

  def adjustSizes (self):
    width = 300;  # minimal size of content section
    # add width of other sections
    for col in [0,1]:
      width += self._tw.header().sectionSize(col);
    # print width;
    self.resize(max(width,self.width()),self.height());

  def refresh_profiles (self):
    """Reloads the profiles file and repopulates load and save menus accordingly""";
    self.load_menu.clear();
    self.save_menu.clear();
    self.save_menu.addAction(self._qa_newprof);
    self.save_menu.addSeparator();
    self.profiles = configparser.RawConfigParser();
    try:
      self.profiles.read([PROFILE_FILE]);
    except:
      pass;
    self.wload.setEnabled(bool(self.profiles.sections()));
    for name in sorted(self.profiles.sections()):
      self.load_menu.addAction(name,self.curry(self._load_profile,name));
      self.save_menu.addAction(name,self.curry(self._save_profile,name));

  def _load_profile (self,name):
    if not self.profiles.has_section(name):
      QMessageBox.warning(self,"Error loading profile","""<P>Profile '%s' not found,
              check your %s file.</P>"""%(name,PROFILE_FILE));
      return;
    for name,value in self.profiles.items(name):
      try:
        TDLOptions.set_option(name,value,save=False,from_str=True);
      except ValueError:
        dprintf(0,"can't set '%s' to %s, ignoring",name,value);
    TDLOptions.save_config();

  def _save_profile (self,name):
    if self.profiles.has_section(name):
      if QMessageBox.warning(self,"Overwriting profile","""<P>Do you really want to
                          overwrite the existing profile '%s'?</P>"""%name,
                          QMessageBox.Ok|QMessageBox.Cancel,QMessageBox.Ok) != QMessageBox.Ok:
        return;
      newprof = False;
    else:
      self.profiles.add_section(name);
      newprof = True;
    TDLOptions.save_to_config(self.profiles,name);
    try:
      ff = open(PROFILE_FILE,"wt");
      for section in sorted(self.profiles.sections()):
        ff.write("[%s]\n"%section);
        for opt,value in sorted(self.profiles.items(section)):
          ff.write("%s = %s\n"%(opt.lower(),value));
        ff.write("\n");
      ff.close();
    except:
      dprintf(0,"error writing %s"%PROFILE_FILE);
      traceback.print_exc();
      QMessageBox.warning(self,"Error saving profile","""<P>There was an error writing to the %s file,
                           profile was not saved.</P>"""%PROFILE_FILE);
    if newprof:
      self.refreshProfiles.emit()

  def _save_new_profile (self):
    default_name = os.path.splitext(os.path.basename(TDLOptions.current_scriptname))[0] + ":";
    name,ok = QInputDialog.getText(self,"Saving profile","Enter profile name",QLineEdit.Normal,default_name);
    if ok:
      self._save_profile(str(name));

  def _resize_dialog (self,section,*dum):
    if self._allow_resize_dialog and section<ColumnValue:
      self.adjustSizes();

  def accept (self):
    self.accepted.emit()
    self.hide();

#  def show (self):
    #self._tw.adjustColumn(0);
    #self._tw.adjustColumn(1);
#    return QDialog.show(self);

#  def exec_ (self):_load_prof
#    #self._tw.adjustColumn(0);
#    #self._tw.adjustColumn(1);
#    return QDialog.exec_(self);

  def treeWidget (self):
    return self._tw;

  def clear (self):
    self._tw.clear();

  def addAction (self,label,callback,icon=None):
    # find last item
    last = self._tw.topLevelItem(self._tw.topLevelItemCount()-1);
    item = QTreeWidgetItem(self._tw,last);
    button = QPushButton(self._tw);
    button.setText(label);
    if icon:
      button.setIcon(icon.icon());
    self._tw.setItemWidget(item,0,button);
    button._on_click = callback;
    button.clicked.connect(button._on_click)
    button.clicked.connect(self.hide)

  def _process_treewidget_click (self,item,col,*dum):
    """helper function to process a click on a treeWidget item. Meant to be connected
    to the clicked() signal of a QListView""";
    if col == ColumnToolTip:
      tip = str(item.toolTip(ColumnToolTip));
      if tip:
        pos = self._tw.viewport().mapToGlobal(QPoint(self._tw.columnViewportPosition(ColumnToolTip),self._tw.visualItemRect(item).top()));
        QToolTip.showText(pos,tip,self._tw);
    else:
      getattr(item,'_on_click',lambda:None)();
      if getattr(item,'_close_on_click',False):
        self.hide();

  def _process_treewidget_press (self,item,col,*dum):
    """helper function to process a press on a treeWidget item. Meant to be connected
    to the pressed() signal of a QListView""";
    if col == ColumnToolTip:
      tip = str(item.toolTip(ColumnToolTip));
      if tip:
        pos = self._tw.viewport().mapToGlobal(QPoint(self._tw.columnViewportPosition(ColumnToolTip),self._tw.visualItemRect(item).top()));
        QToolTip.showText(pos,tip,self._tw);
    else:
      getattr(item,'_on_press',lambda:None)();

