import sys
import os
import logging
import frameHandler
import mylog
import threading

#设置log文件的格式
logging.basicConfig(level=logging.DEBUG,
                    filename='log.log',
                    format='[%(asctime)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filemode='a')

frameHandler = frameHandler.FrameHandler()      #处理帧文件的类

#先启动从USB设备读数据的线程，保证在程序结束前不停的读出。
readingThread = threading.Thread(target=frameHandler.readFromUSB, name='ReadingThread')
readingThread.start()

#下面执行写入过程
inputData = None
while True:
    #输入帧文件的信息，输入格式为'文件名(不含后缀),是否为新文件,帧间隔'
    inputData = input()

    if inputData == 'exit':     #退出程序
        frameHandler.stopReading()
        sys.exit(0)
    elif inputData == 'usb':    #重新查找、连接USB设备
        frameHandler.findUSB()
        continue
    else:
        fileName, transform, frameGap = inputData.split(',')

    #检查帧文件是否存在，如果不存在，跳出循环一次
    if not os.path.exists('./files/%s.txt' % fileName):
        mylog.error('Error: \'%s.txt\' does not exit.' % (fileName))
        continue

    if transform == '1':
        frameHandler.transformFrameFile(fileName)

    frameGap = int(frameGap)
    if frameGap <= 0:
        frameHandler.writeToUSB(fileName)
    else:
        frameHandler.writeToUSBWithGap(fileName,frameGap)