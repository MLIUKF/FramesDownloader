# encoding: utf-8
import numpy
import time
import array
import usbHandler
import logging
import mylog

class FrameHandler():

    def __init__(self):
        self.usbHandler = usbHandler.USBHandler()
        self.allowRead = True

    def transfer(self,frameData):
		#把64bit的数据转成64比特的倒序帧数据
        return frameData[32:64]+frameData[0:32]+'\n'

    def transformFrameFile(self,fileName):
        r'''
        把64bit的TXT帧文件转成bytes类型的.npy文件，用于传输；
        '''
        #读入40比特的帧数据
        mylog.info('正在将64bit帧文件转换为64bit的倒序帧文件...')
        with open('./files/%s.txt' % fileName,'r') as net64bInit:
            frames = net64bInit.readlines()
            framesTrans = [self.transfer(f) for f in frames]

        #写入64比特的帧数据,fileName64b_reverse.txt
        with open('./files/%s64b_reverse.txt' % fileName,'w') as net64b:
            temp=[net64b.write(f) for f in framesTrans]
            mylog.info('正在将64bit的帧文件转换为.npy文件...')

        #读入按字节倒序的64比特的帧数据，并转成bytes类型数据，存入.npy文件中
        frames = framesTrans
        framesNum = len(frames)
        tempData = numpy.zeros(framesNum).astype('uint64')
        for i,f in enumerate(frames):
            tempData[i] = int(f,2)

        tempData.dtype = 'uint8'
        frameBytes = bytes(tempData)
        numpy.save('./files/%s.npy' % fileName,numpy.array(frameBytes))
        mylog.info('帧文件转换完成。')

    def writeToUSB(self,fileName):
        r'''
        把处理好的帧数据连续写入USB设备；
        '''
        try:
            mylog.info('正在写入帧文件...')
            frameData = numpy.load('./files/%s.npy' % fileName)
            #某些情况下需要降低发送速度，下面将帧数据分块发送；
            frameData = bytes(frameData)
            dataLength = len(frameData)
            bytesValidOneTime = int(0.5*1024)  #每次发送的数据中，有效帧的字节数
            i = 0
            while (i+bytesValidOneTime) < dataLength:
                #time.sleep(0.001)
                if not self.usbHandler.writeToUSB(frameData[i:(i+bytesValidOneTime)]):
                    mylog.error('Error: 写入失败！')
                    return False
                i += bytesValidOneTime
            if i < dataLength:
                if not self.usbHandler.writeToUSB(frameData[i:]):
                    mylog.error('Error: 写入失败！')
                    return False
        except BaseException as e:
            mylog.error("Error: 写入帧文件失败。")
            mylog.error(str(e))
            return False
        else:
            mylog.info('已成功写入帧文件。')
            return True

    def writeToUSBWithFrameNum(self,fileName):
        r'''
        把固定数量的帧数据写入USB设备，起始帧编号为currentFrameNo，写入帧的数量为frameNum；
        '''
        currentFrameNo = 0
        try:
            frameData = numpy.load('./files/%s.npy' % fileName)
            frameData = bytes(frameData)
            dataLength = len(frameData)
            frameLength = dataLength//8
        except BaseException as e:
            mylog.error("Error: 读取帧文件失败。")
            mylog.error(str(e))
            return False
        else:
            mylog.info('已成功读取帧文件。')
        while True:
            inputData = input()
            if inputData == 'stop':
                return True
            else:
                try:
                    frameNum = int(inputData)
                except BaseException as e:
                    mylog.error("Error: 指令不符合要求，请输入数字或stop：")
                    mylog.error(str(e))
                    continue
                if currentFrameNo+frameNum > frameLength:
                    mylog.error('Error: 超出帧文件范围。起始帧为%d，写入帧数量为%d...' % (currentFrameNo,frameNum))
                    return False
                mylog.info('正在写入帧，起始帧为%d，帧数量为%d...' % (currentFrameNo,frameNum))
                if not self.usbHandler.writeToUSB(frameData[(8*currentFrameNo):(8*(currentFrameNo+frameNum))]):
                    mylog.error('Error: 写入失败！')
                    return False
                print('已写入，请输入数字或stop：')
                currentFrameNo += frameNum
        return True

    def findUSB(self):
        self.usbHandler.findUSB()

    def readFromUSB(self):
        while self.allowRead:
            readOutBytes = self.usbHandler.readFromUSB()
            if readOutBytes == 1:
                mylog.error('读出过程发生错误。')
                return False
            elif readOutBytes == None:
                mylog.error('未读到数据。')
                time.sleep(5)
            else:
                with open('./files/out.txt','a') as outFile:
                    readOutBytesNum = len(readOutBytes)
                    for i in range(0,readOutBytesNum,8):
                        #frameTitle = readOutBytes[i+3] >> 4
                        #if frameTitle != 3:     #0011
                        for j in range(3,-1,-1):
                            outFile.write('{:0>2x}'.format(readOutBytes[i+j]))
                        for j in range(7,3,-1):
                            outFile.write('{:0>2x}'.format(readOutBytes[i+j]))
                        outFile.write('\n')
            break

    def stopReading(self):
        self.allowRead = False

    def startReading(self):
        self.allowRead = True