#!/usr/bin/python
# -*- coding : utf-8 -*-

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QTableWidgetItem, QHBoxLayout, QStyleFactory, QApplication

import sys
from time import ctime, sleep
import subprocess
import locale
import codecs
import threading
import os
import time
import inspect
import datetime

from Ui_apkuptest import Ui_MainWindow
from Logger import FinalLogger

oldapkspath = {}
newapkpath = ""
dict_device = {}
dict_testresult = []
timefomate = "%Y%m%d"

class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        super(MyWindow, self).__init__()

        self.setupUi(self)
        nowtime = datetime.datetime.now().strftime(timefomate)
        self.systemlogpath =  os.path.abspath('.') + os.sep + "Systemlog" + nowtime + ".log" 
        command = 'adb.exe logcat -v time *:i | find "." >> ' + self.systemlogpath
        self.ps = subprocess.Popen(command,stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        self.logger = FinalLogger.getLogger()
        self.logger.info("start test")

        self.text_systemlogpath.setText(FinalLogger.log_file)
        self.text_loggerpath.setText(self.systemlogpath)

        self.SetDevices()
        self.tt()

        self.btn_getdevices.clicked.connect(self.SetDevices)
        self.btn_chooseold.clicked.connect(self.ChooseOldApks)
        self.btn_choosenew.clicked.connect(self.ChooseNewApk)
        self.btn_start.clicked.connect(self.StartTest)
        #self.btn_detailinfo.clicked.connect(self.OpenLogcat)

        self.tableWidget.setHorizontalHeaderLabels(['', '', '', '', ''])

    def SetDevices(self):
        self.getdeviceslist()
        self.combo_devices.clear()
        self.combo_devices.addItems(dict_device.keys())

    def OpenLogcat(self):
        
        
        os.system(self.systemlogpath)


    def StartTest(self):
        """卸载apk后，安newapk并启动"""
        self.logger.info("FUNC: %s" % sys._getframe().f_code.co_name)

        global dict_testresult
        num = 1

        packagename=self.text_packagename.text()   
        installpath = self.lineEdit.text()
        version = self.text_version.text()
        startactivity = self.text_startactivity.text()

        result_unitstall = self.unitstallapp(packagename)
        result_install = self.installapp(installpath, 1)
        result_startactivity = self.StartActivity(startactivity)

        dict_testresult.append(
                "Step%d. New_Release_install %s" % (num, version))
        dict_testresult.append(["result_unitstall:", result_unitstall, "result_install:",
                                    result_install, "result_startactivity:", result_startactivity])
        print(dict_testresult)

        """循环oldapk进行如下操作：卸载newapk，安装老版本apk并启动；覆盖安装newapk并启动。"""
        for (oldapk,info) in oldapkspath.items():
            num = num + 1
            result_unitstall = self.unitstallapp(packagename)
            result_install = self.installapp(oldapk, 1)
            result_startactivity = self.StartActivity(info[1])
            dict_testresult.append("Step%d. Lower_version_install %s" % (num, info[2]))
            dict_testresult.append(["result_unitstall", result_unitstall, "result_install",result_install, "result_startactivity", result_startactivity])
            result_install = self.installapp(installpath, 1)
            result_startactivity = self.StartActivity(startactivity)
            dict_testresult.append("Step%d. New_Release_install %s" % (num, version))
            dict_testresult.append(["result_install", result_install, "result_startactivity", result_startactivity])

        self.tabWidget.setCurrentIndex(1)
        print(dict_testresult)
        self.showTableWidget(dict_testresult)
        print("end.")

    def ChooseNewApk(self):
        self.logger.info("FUNC: %s" % sys._getframe().f_code.co_name)
        global newapkpath
        self.lineEdit.clear()

        filedialog = QFileDialog()
        filedialog.setNameFilter("Get Files(*.apk)")

        path = filedialog.getOpenFileName(
            self, "选取文件", "C:/", "APK Files (*.apk);;Text Files (*.txt)")

        if path != "":
            self.lineEdit.setText(str(path[0]))
            newapkpath = path[0]
            pids = self.GetApkInfo(newapkpath)
          
            if pids != []:
                
                self.text_versioncode.setText(pids[2])
                self.text_packagename.setText(pids[1][6:-1])
                self.text_version.setText(pids[3])
                self.text_startactivity.setText(
                    pids[pids.index('launchable-activity:') + 1][6:-1])

    def ChooseOldApks(self):
        self.logger.info("FUNC: %s" % sys._getframe().f_code.co_name)
        global oldapkspath
        self.textEdit.clear()
        packagename=self.text_packagename.text()   #新版本的packagename
        filedialog = QFileDialog()
        filedialog.setNameFilter("Get Files(*.apk)")
        path = filedialog.getOpenFileNames(
            self, "选取文件", "C:/", "APK Files (*.apk);;Text Files (*.txt)")

        if path != "":
            
            apkspath = path[0]

            if apkspath != []:
                self.textEdit.clear()
                for x in apkspath:
                    pids = self.GetApkInfo(x)
                    if pids[1][6:-1] != packagename:
                        
                        
                         QMessageBox.warning(self, "警告", "packageName新老版本不一致，请重新选择！", QMessageBox.Yes)
                         return 0
                    else:

                        oldapkspath[x] = [pids[1][6:-1], pids[pids.index('launchable-activity:') + 1][6:-1], pids[2],pids[3]]
                for (k,v) in oldapkspath.items():
                    #s = str(k)+ "\\r" +str(v)
                    self.textEdit.append(str(k))
                    self.textEdit.append(str(v))     
                    self.textEdit.append("")                 

    def GetApkInfo(self, apkpath):
        self.logger.info("FUNC: %s" % sys._getframe().f_code.co_name)
        command="aapt dump badging " + apkpath
        pids=self.exctcmd(command).split()
        print(pids)
        return pids

    def installapp(self, installpath, installtype):
        self.logger.info("FUNC: %s" % sys._getframe().f_code.co_name)
        """installtype:1 覆盖安装；0：卸载安装"""

        # self.text_result.clear()

        if installpath != "":
            text_devicesname=self.combo_devices.currentText()

            if text_devicesname != "":

                # 获取设备的-s
                text_sname=dict_device[text_devicesname]

                if installtype == 0:
                    self.unitstallapp()

                command="adb -s " + text_sname + " install -r " + installpath

                pids=self.exctcmd(command).replace(
                    '\r\r', '\r').replace('\n', "").split('\r')[-2]

                # self.text_result.append(pids[-50:])
            else:
                QMessageBox.warning(
                    self, "警告", "请先选择设备", QMessageBox.Yes)
                pids="Devices Error"

        else:
            QMessageBox.warning(self, "警告", "请先选择apk！", QMessageBox.Yes)
            pids="ApkPath Error"

        self.logger.info("Execute Install %s" % pids)
        return pids

    def unitstallapp(self,packagename):
        self.logger.info("FUNC: %s" % sys._getframe().f_code.co_name)
        # self.text_result.clear()
        
        text_devicesname=self.combo_devices.currentText()

        if text_devicesname != "":
            if packagename != "":

                text_sname=dict_device[text_devicesname]

                command="adb -s " + text_sname + " uninstall " + packagename
                pids=self.exctcmd(command).replace('\r', '').replace('\n', '')
                # self.text_result.append(pids)

            else:
                QMessageBox.warning(
                    self, "警告", "PackageName不正确", QMessageBox.Yes)
                pids="PackageName Error"

        else:
            QMessageBox.warning(
                self, "警告", "请先选择设备", QMessageBox.Yes)
            pids = "Devices Error"
        self.logger.info("Execute UnitstallApp %s" % pids)
        return pids

    def StartActivity(self,startactivity):
        self.logger.info("FUNC: %s" % sys._getframe().f_code.co_name)
        text_packagename = self.text_packagename.text()
        text_devicesname = self.combo_devices.currentText()

        if text_devicesname != "":
            if text_packagename != "":
                if startactivity != "":

                    text_sname = dict_device[text_devicesname]

                    command = "adb -s " + text_sname + " shell am start -W -n " + \
                        text_packagename + "/" + startactivity
                    pids = self.exctcmd(command).split('\r\r\n')[-2]

                else:
                    QMessageBox.warning(
                        self, "警告", "StartActivity不正确", QMessageBox.Yes)
                    pids = "StartActivity Error"

            else:
                QMessageBox.warning(
                    self, "警告", "PackageName不正确", QMessageBox.Yes)
                pids = "PackageName Error"
        else:
            QMessageBox.warning(
                self, "警告", "请先选择设备", QMessageBox.Yes)
            pids = "Devices Error"
        self.logger.info("Execute StartActivity %s" % pids)
        return pids

    def getdeviceslist(self):
        self.logger.info("FUNC: %s" % sys._getframe().f_code.co_name)
        global dict_device
        dict_device = {}

        pids = self.exctcmd('adb devices').split()[4:]

        if pids.count('*') > 0 and pids.count('successfully') > 0:
            pids = pids[16:]
        elif pids.count('*') > 0 and pids.count('successfully') == 0:
            dict_device["Failed to get devices！"] = "Failed to get devices！"
            return 0

        pid_s = pids[::2]
        pid_tag = pids[1::2]
        # print(pids)
        # print(pid_tag)
        count = len(pid_s)

        # 根据device -s 信息获取 设备型号,将设备信息放入device dict中
        if count != 0:
            for x in range(count):
                if pid_tag[x] == 'device':
                    command = "adb -s " + \
                        pid_s[x] + " shell getprop | grep \"ro.product.model]\""
                    #'shell getprop | grep "ro.product.model"'cat /system/build.prop

                    modelinfo = self.exctcmd(command).replace(
                        "\r", "").replace(" [", "[").strip('\n')[19:]
                    # print(modeinfo)
                    pid_tag[x] = modelinfo

                    dict_device[pid_tag[x]] = pid_s[x]  # 仅考虑连接成功的设备

        return dict_device.keys()

    def exctcmd(self, command):
        self.logger.info("FUNC: %s" % sys._getframe().f_code.co_name)

        obj = subprocess.Popen(command, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # out_error_list = obj.communicate('print "hello"')
        s = obj.stdout.read()
        # result = s.decode('ascii')
        result = str(s, encoding='utf-8')

        # obj.terminate()
        obj.kill()
        print(result)
        return result

    def showTableWidget(self,resultdict):
        """set test result in tableWidget"""
        self.logger.info("FUNC: %s" % sys._getframe().f_code.co_name)

        failcount = 0
        roucount = int((((len(resultdict) / 2 - 1) / 2)) * 5 + 5)
        self.tableWidget.setRowCount(roucount)
        
        row = 2
        column = 3
        for x in resultdict[1::2]:
            myrow = row
            for y in x[::2]:
                newItem = QTableWidgetItem(y)
                self.tableWidget.setItem(myrow, column, newItem)
                myrow = myrow + 1

            myrow = row
            for y in x[1::2]:
                newItem = QTableWidgetItem(y)

                if "Failure" in y or "Error" in y:
                    failcount = failcount + 1

                    brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
                    brush.setStyle(QtCore.Qt.NoBrush)
                    newItem.setForeground(brush)  
                
                self.tableWidget.setItem(myrow, column +1 , newItem)               
                myrow = myrow + 1
            row = myrow

        row = 2
        for x in resultdict[::2]:
            column = 0
            l = x.split(" ")
            for y in l:
                newItem = QTableWidgetItem(y)
                self.tableWidget.setItem(row, column, newItem)
                column = column + 1
            row = int(row + len(resultdict[resultdict.index(x) + 1]) / 2)
        
        
        # self.tableWidget.setSpan(0, 1, 1, 2) 合并单元格，从01，开始横向合并1，纵向合并2

        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        

        newItem = QTableWidgetItem("Summary: ")
        newItem.setFont(font)
        self.tableWidget.setItem(0,0,newItem)

        if failcount == 0:
            result = "Complete all execution"
            newItem = QTableWidgetItem(result)
        else:
            result = "%d execution error occurred" % failcount
            newItem = QTableWidgetItem(result)
            brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
            brush.setStyle(QtCore.Qt.NoBrush)
            newItem.setForeground(brush)
        newItem.setFont(font)
        self.tableWidget.setItem(0, 1 , newItem)        

        self.tableWidget.resizeColumnsToContents()  # 将列调整到跟内容大小相匹配
        self.tableWidget.resizeRowsToContents()  # 将行大小调整到跟内容的大学相匹配


    def tt(self):
        self.logger.info("FUNC: %s" % sys._getframe().f_code.co_name)
        
        resultdict = ["Step1. New_Release_install versionName='5.6.0'", ['result_unitstall:', 'Failure', 'result_install:', 'Success', 'result_startactivity:', 'Complete'], "Step2. Lower_version_install versionCode='5591'", ['result_unitstall', 'Success', 'result_install', 'Success', 'result_startactivity', 'Complete'], "Step2. New_Release_install versionName='5.6.0'", ['result_install', 'Success', 'result_startactivity', 'Complete']]

        self.tabWidget.setCurrentIndex(1)

        # table title
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)

        newItem = QTableWidgetItem("No.")
        newItem.setFont(font)
        self.tableWidget.setItem(2,0,newItem)

        newItem = QTableWidgetItem("Case")
        newItem.setFont(font)
        self.tableWidget.setItem(2,1,newItem)

        newItem = QTableWidgetItem("Step")
        newItem.setFont(font)
        self.tableWidget.setItem(2,2,newItem)

        newItem = QTableWidgetItem("Detail")
        newItem.setFont(font)
        self.tableWidget.setItem(2,3,newItem)

        newItem = QTableWidgetItem("Result")
        newItem.setFont(font)
        self.tableWidget.setItem(2,4,newItem)


        failcount = 0
        roucount = int((((len(resultdict) / 2 - 1) / 2)) * 5 + 7)
        self.tableWidget.setRowCount(roucount)
        
        row = 4
        column = 3
        for x in resultdict[1::2]:
            myrow = row
            for y in x[::2]:
                newItem = QTableWidgetItem(y)
                self.tableWidget.setItem(myrow, column, newItem)
                myrow = myrow + 1

            myrow = row
            for y in x[1::2]:
                newItem = QTableWidgetItem(y)

                if "Failure" in y or "Error" in y:
                    failcount = failcount + 1

                    brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
                    brush.setStyle(QtCore.Qt.NoBrush)
                    newItem.setForeground(brush)  
                
                self.tableWidget.setItem(myrow, column +1 , newItem)               
                myrow = myrow + 1
            row = myrow

        row = 4
        for x in resultdict[::2]:
            column = 0
            l = x.split(" ")
            for y in l:
                newItem = QTableWidgetItem(y)
                self.tableWidget.setItem(row, column, newItem)
                column = column + 1
            row = int(row + len(resultdict[resultdict.index(x) + 1]) / 2)

        self.tableWidget.resizeColumnsToContents()  # 将列调整到跟内容大小相匹配
        self.tableWidget.resizeRowsToContents()  # 将行大小调整到跟内容的大学相匹配       
        
        
        # 设置汇总结果
        self.tableWidget.setSpan(0, 0, 1, 5) #合并单元格，从01，开始横向合并1，纵向合并2

        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)

        newItem = QTableWidgetItem()
        newItem.setFont(font)

        result = "Summary: "

        if failcount == 0:
            result = result + "Complete all execution"
            
        else:
            result = result +"%d execution error occurred" % failcount            
            brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
            brush.setStyle(QtCore.Qt.NoBrush)
            newItem.setForeground(brush)
        
        newItem.setText(result)

        self.tableWidget.setItem(0,0,newItem)
        
       

        #self.tableWidget.resizeColumnsToContents()  # 将列调整到跟内容大小相匹配
        #self.tableWidget.resizeRowsToContents()  # 将行大小调整到跟内容的大学相匹配



if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setPalette(QApplication.style().standardPalette())
    
    myshow = MyWindow()
    myshow.show()
    sys.exit(app.exec_())
