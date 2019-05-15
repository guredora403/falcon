﻿# -*- coding: utf-8 -*-
#Falcon app main view
#Copyright (C) 2019 Yukio Nozawa <personal@nyanchangames.com>
#Note: All comments except these top lines will be written in Japanese. 

import gettext
import logging
import os
import sys
import wx
from logging import getLogger, FileHandler, Formatter

from .base import *
import misc
import views.test
import constants
import errorCodes
import globalVars
import tabObjects
from simpleDialog import *

class View(BaseView):
	def Initialize(self):
		t=misc.Timer()
		self.identifier="mainView"#このビューを表す文字列
		self.log=getLogger("falcon.%s" % self.identifier)
		self.log.debug("created")
		self.app=globalVars.app
		super().Initialize(constants.APP_NAME,self.app.config.getint(self.identifier,"sizeX"),self.app.config.getint(self.identifier,"sizeY"))
		self.menu=Menu()
		self.events=Events(self)
		self.InstallMenuEvent(self.menu,self.events)
		self.InstallShortcutEvent(self.identifier,self.events)
		self.InstallListPanel()
		self.tabs=[]
		self.MakeFirstTab()
		self.hFrame.Show()
		self.app.SetTopWindow(self.hFrame)
		self.log.debug("Finished creating main view (%f seconds)" % t.elapsed)
		return True

	def InstallListPanel(self):
		"""リストコントロールが表示されるパネルを設定する。"""
		self.hListPanel=wx.Panel(self.hFrame, wx.ID_ANY, pos=(0,0),size=(800,300))
		self.hListPanel.SetBackgroundColour("#0000ff")		#項目のない部分の背景色
		self.hListPanel.SetAutoLayout(True)
		self.sizer=wx.BoxSizer(wx.HORIZONTAL)
		self.hListPanel.SetSizer(self.sizer)

	def MakeFirstTab(self):
		"""最初のタブを作成する。"""
		self.activeTab=None#最初なのでなにもなし
		tab=tabObjects.FileListTab()
		tab.Initialize(self.hListPanel, os.path.expandvars(self.app.config["browse"]["startPath"]))
		self.AppendTab(tab,active=True)

	def AppendTab(self,tab,active=False):
		"""タブを追加する。active=True で、追加したタブをその場でアクティブにする。"""
		self.tabs.append(tab)
		self.sizer.Add(tab.GetListCtrl(),1,wx.EXPAND)
		self.log.debug("A new tab has been added (now %d)" % len(self.tabs))
		if active is True: self.ActivateTab(tab)

	def ActivateTab(self,tab):
		"""指定されたタブをアクティブにする。内部で管理しているタブリストに入っていない他部でも表示できる。"""
		if self.activeTab: self.activeTab.getListCtrl().Hide()
		self.activeTab=tab
		l=self.activeTab.GetListCtrl()
		l.Show(True)

class Menu():
	def Apply(self,target,event):
		"""指定されたウィンドウに、メニューを適用する。"""
		#メニューの大項目を作る
		self.hFileMenu=wx.Menu()
		self.hEditMenu=wx.Menu()
		self.hMoveMenu=wx.Menu()
		self.hReadMenu=wx.Menu()
		self.hToolMenu=wx.Menu()
		self.hViewMenu=wx.Menu()
		self.hEnvMenu=wx.Menu()
		self.hHelpMenu=wx.Menu()
		#ファイルメニューの中身
		self.hFileMenu.Append(constants.MENU_ITEMS["FILE_EXIT"].GetValue(),_("終了"))
		#移動メニューの中身
		self.hMoveMenu.Append(constants.MENU_ITEMS["MOVE_FORWARD"].GetValue(),_("開く"))
		self.hMoveMenu.Append(constants.MENU_ITEMS["MOVE_BACKWARD"].GetValue(),_("閉じる"))
		#環境メニューの中身
		self.hEnvMenu.Append(constants.MENU_ITEMS["ENV_TESTDIALOG"].GetValue(),_("テストダイアログを表示"))
		#ヘルプメニューの中身
		self.hHelpMenu.Append(constants.MENU_ITEMS["HELP_VERINFO"].GetValue(),_("バージョン情報"))
		#メニューバー
		self.hMenuBar=wx.MenuBar()
		self.hMenuBar.Append(self.hFileMenu,_("ファイル"))
		self.hMenuBar.Append(self.hEditMenu,_("編集"))
		self.hMenuBar.Append(self.hMoveMenu,_("移動"))
		self.hMenuBar.Append(self.hReadMenu,_("読み"))
		self.hMenuBar.Append(self.hToolMenu,_("ツール"))
		self.hMenuBar.Append(self.hViewMenu,_("表示"))
		self.hMenuBar.Append(self.hEnvMenu,_("環境"))
		self.hMenuBar.Append(self.hHelpMenu,_("ヘルプ"))
		target.SetMenuBar(self.hMenuBar)
		target.Bind(wx.EVT_MENU,event.OnMenuSelect)

class Events(BaseEvents):
	def OnMenuSelect(self,event):
		"""メニュー項目が選択されたときのイベントハンドら。"""
		selected=event.GetId()#メニュー識別しの数値が出る
		if selected==constants.MENU_ITEMS["MOVE_BACKWARD"].GetValue():
			self.GoBackward()
			return
		if selected==constants.MENU_ITEMS["MOVE_FORWARD"].GetValue():
			self.GoForward()
			return
		if selected==constants.MENU_ITEMS["ENV_TESTDIALOG"].GetValue():
			self.testdialog=views.test.View()
			self.testdialog.Initialize()
			return
		if selected==constants.MENU_ITEMS["FILE_EXIT"].GetValue():
			self.Exit(event)
			return
		if selected==constants.MENU_ITEMS["HELP_VERINFO"].GetValue():
			self.ShowVersionInfo()
			return
		dialog(_("エラー"),_("操作が定義されていないメニューです。"))
		return

	def ShowVersionInfo(self):
		"""バージョン情報を表示する。"""
		dialog(_("バージョン情報"),_("%(app)s Version %(ver)s.\nCopyright (C) %(year)s %(names)s") % {"app":constants.APP_NAME, "ver":constants.APP_VERSION, "year":constants.APP_COPYRIGHT_YEAR, "names":constants.APP_DEVELOPERS})

	def GoBackward(self):
		"""back アクションを実行"""
		p=self.parent
		ret=p.activeTab.TriggerAction(tabObjects.ACTION_BACKWARD)
		if ret==errorCodes.NOT_SUPPORTED:
			dialog(_("エラー"),_("このオペレーションはサポートされていません。"))
		elif ret==errorCodes.BOUNDARY:
			dialog("test","mada")

	def GoForward(self):
		"""forward アクションを実行"""
		p=self.parent
		ret=p.activeTab.TriggerAction(tabObjects.ACTION_FORWARD)
		if ret==errorCodes.NOT_SUPPORTED:
			dialog(_("エラー"),_("このオペレーションはサポートされていません。"))
		elif ret==errorCodes.BOUNDARY:
			dialog("test","mada")