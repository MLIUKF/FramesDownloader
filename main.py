import sys
import os
import logging
import frameHandler
import mylog
import threading
import time

#设置log文件的格式
logging.basicConfig(level=logging.DEBUG,
                    filename='log.log',
                    format='[%(asctime)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filemode='a')

frameHandler = frameHandler.FrameHandler()      #处理帧文件的类

#先启动从USB设备读数据的线程，保证在程序结束前不停的读出。
readingThread = threading.Thread(target=frameHandler.readFromUSB, name='ReadingThread')
#readingThread.start()

#下面执行写入过程
inputData = None
fileName = 'None'
transform = None
while True:
    #输入帧文件的信息，输入格式为'文件名(不含后缀),是否为新文件,帧间隔'
    inputData = input()

    if inputData == 'exit':     #退出程序
        frameHandler.stopReading()
        sys.exit(0)
    elif inputData == 'usb':    #重新查找、连接USB设备
        frameHandler.findUSB()
        continue
    elif inputData == 'read':
        frameHandler.stopReading()
        time.sleep(0.005)
        frameHandler.startReading()
        readingThread = threading.Thread(target=frameHandler.readFromUSB, name='ReadingThread')
        readingThread.start()
        print('读出线程已重启。')
        continue
    elif inputData == 'file':
        print('当前帧文件：%s，请输入新的帧文件名称：' % fileName)
        inputDataB = input()
        try:
            fileName, transform = inputDataB.split(',')
            #检查帧文件是否存在，如果不存在，跳出循环一次
            if not os.path.exists('./files/%s.txt' % fileName):
                mylog.error('Error: \'%s.txt\' does not exit.' % (fileName))
                continue
            if transform == '1':
                frameHandler.transformFrameFile(fileName)
        except BaseException as e:
            mylog.error("Error: 指令不符合要求。")
            mylog.error(str(e))
            continue
    elif inputData == 'autowrite':
        print('开始自动写入帧文件：%s...' % fileName)
        if frameHandler.writeToUSB(fileName):
            print('自动写入结束。')
        else:
            print('自动写入失败。')
    elif inputData == 'handwrite':
        print('开始手动写入帧文件：%s，请输入数字或stop：' % fileName)
        if frameHandler.writeToUSBWithFrameNum(fileName):
            print('已退出手动写入。')
        else:
            print('手动写入失败。')
    else:
        print('指令未识别，请重新输入：')
        continue