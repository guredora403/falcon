﻿# -*- coding: utf-8 -*-
#Falcon file operation handler copy
#Copyright (C) 2019 Yukio Nozawa <personal@nyanchangames.com>
#Note: All comments except these top lines will be written in Japanese. 
import logging
import os
import re
import win32file
from . import confirmElement, failedElement, helper
import misc
from clipboard import COPY, MOVE

VERB="past"
log=logging.getLogger("falcon.%s" % VERB)

class Element(object):
	"""コピー/移動する項目の情報を持っておく。"""
	def __init__(self,path,basepath,destpath):
		self.path=path
		self.isfile=os.path.isfile(path)
		self.size=os.path.getsize(path) if self.isfile else -1
		if basepath is None or destpath is None: return#どっちかがNoneだったら、移動するときのフォルダ削除用エントリとして取り扱うことにする
		self.destpath=path.replace(basepath,destpath)#これがコピー先
	#end __init__
#end Element

def Execute(op,resume=False):
	"""実行処理。リトライが必要になった項目数を返す。"""
	if resume: log.debug("Starting as resume mode...")
	retry=0
	try:
		f=op.instructions["target"]
	except KeyError:
		log.error("Required key is not specified.")
		return False
	#end 処理刷るものなし
	copy_move_flag=op.instructions["copy_move_flag"]
	if not resume:# resume modeではない=初期化
		op.output["all_OK"]=True
		op.output["retry"]["target"]=[]
		op.output["percentage"]=0
		op.output["copy_move_flag"]=copy_move_flag
		#ベースパスを決定
		op.output["basepath"]=os.path.dirname(f[0])
		op.output["destpath"]=op.instructions['to']
	#end 初期化
	basepath=op.output["basepath"]
	destpath=op.output["destpath"]
	log.debug("Base path: %s dest path: %s" % (basepath,destpath))
	log.debug("Retrieving file list...")
	lst=[]
	for elem in f:
		if not basepath in elem:
			debug.log("Ummatched base path, skipping %s" % elem)
			continue
		#end ベースパスが合わない
		if os.path.isfile(elem):
			lst.append(Element(elem,basepath,destpath))
		else:
			e=Element(elem,basepath,destpath)
			if os.path.isdir(e.destpath) and not resume:
				_processExistingFolder(op.output,elem)#フォルダがもうあれば、その時点で確認に入れる(中のフォルダを展開しない)
			else:#まだないか、確認済みなので追加
				_expandFolder(lst,elem,e,basepath,destpath)
			#end フォルダを展開するかしないか
		#end フォルダだった
	#end ファイルリスト作るループ
	#ファイルリスト作ったので、もともとの target に上書き
	f=lst
	log.debug("%d items found." % len(f))
	#コピーサイズの合計を計算
	total=0
	for elem in f:
		if elem.size!=-1: total+=elem.size
	#end サイズを足す
	op.output['total_bytes']=total
	op.output['current_bytes']=0
	log.debug("Size: %d bbytes" % total)
	log.debug("Start copying...")
	overwrite=0 if resume else win32file.COPY_FILE_FAIL_IF_EXISTS
	for elem in f:
		if elem.destpath is None:#フォルダ削除用
			try:
				win32.RemoveDirectory(elem.path,None)
			except win32file.error as err:
				log.debug("Error encountered when trying to delete moved folder: %s" % str(err))
			#end except
		#end フォルダ消す
		try:
			if elem.isfile:
				win32file.CopyFileEx(elem.path,elem.destpath,None,None,False,overwrite)
			else:
				if resume and os.path.isdir(elem.destpath): continue#再開している場合はエラーになる前に逃げる
				win32file.CreateDirectory(elem.destpath,None)
		except win32file.error as err:
			log.error("Cannot create %s (%s)" % (elem.destpath, str(err)))
			ProcessError(op.output,elem,str(err),resume)
			continue
		#end except
		if copy_move_flag==MOVE:
			try:
				if elem.isfile: win32file.DeleteFile(elem.path)
			except win32file.error as err:
				log.debug("Error encountered when deleting moved file: %s" % str(err))
			#end except
		#end 移動モード
		op.output["succeeded"]+=1
	#end 削除処理
	if len(op.output["retry"]["target"])>0:
		op.output["retry"]["operation"]=VERB
		retry=len(op.output["retry"]["target"])
	#end リトライあるか
	#終わった者はもう使わないので、ファイルリストは消してしまう
	op.instructions["target"]=[]
	return retry

def ProcessError(output,elem,msg,resume):
	"""アクセス拒否であれば、リトライするリストに追加する。昇格しても失敗するエラーであれば、 need_to_confirm に追加する。"""
	number=helper.GetErrorNumber(msg)
	if helper.IsAccessDenied(number):#アクセス拒否なので、リトライするリストに追加する
		output["retry"]["target"].append(elem)
		return
	#end リトライ
	#コピー/移動先ファイルがすでに存在する
	if number==80 or number==183:
		output["need_to_confirm"].Append(confirmElement.ConfirmElement(elem,number,msg))
		return
	#end 要確認
	output["all_OK"]=False
	output["failed"].append(failedElement.FailedElement(elem.destpath,(number,msg)))
#end ProcessError

def _processExistingFolder(output,elem):
	"""指定したフォルダを、すでに存在するフォルダとして、 need_to_confirm に入れる。"""
	output["need_to_confirm"].Append(confirmElement.ConfirmElement(elem,80,"このフォルダはすでに存在します。"))

def _expandFolder(lst,path,e,basepath,destpath):
	"""フォルダを展開して、指定されたリストに入れる。"""
	lst.append(e)#イテレーションの最初に親フォルダ追加
	for elem in misc.IteratePaths_dirFirst(path):
		lst.append(Element(elem,basepath,destpath))
	#end フォルダからファイルリスト
#end _expandFolder
