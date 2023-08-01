#!/usr/bin/python
# -*- coding: UTF-8 -*-
import sys
import os
import io
from shutil import copyfile


def deleteGarbage(filePath):
    print("开始处理路径为[%s]的文件", filePath)
    # 获取脚本当前路径
    f = io.open(filePath, "r", encoding="utf-8")  # 打开文件
    # 获取脚本所在的位置
    currentDir = os.getcwd()
    f_split = os.path.split(f.name)
    name = f_split[1]
    # 备份文件夹
    backDirPath = currentDir + os.sep + "bak"
    if not os.path.exists(backDirPath):
        os.makedirs(backDirPath)
    # 备份文件
    backupPath = backDirPath + os.sep + name + ".bak"
    # backupPath = currentDir+os.sep+'bak.test.bak'
    print("正在将文件备份到[%s]" + backupPath)
    copyfile(filePath, backupPath)
    # 将文件内容保存起来
    buffer = ""
    flag = True
    for line in f:
        # 不保存Garbage
        if line.startswith("[Aegisub Project Garbage]"):
            flag = False
        if not flag and line.startswith("[V4+ Styles]"):
            flag = True
        if flag:
            buffer += line
    f.close
    # 覆盖源文件
    print("开始删除Garbage" + f.name)
    f = io.open(filePath, "w", encoding="utf-8")  # 打开文件
    f.write(buffer)
    f.close


def main():
    print("main--------------")
    print("参数个数为:", len(sys.argv), "个参数。")
    print("参数列表:", str(sys.argv))
    print("脚本名为：", sys.argv[0])
    for i in range(1, len(sys.argv)):
        filePath = sys.argv[i]
        deleteGarbage(filePath)


# python的main方法（不是）
if __name__ == "__main__":
    main()
