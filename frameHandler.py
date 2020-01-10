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
		#把40bit的数据转成64比特的帧数据
        return frameData[8:40]+'000000000000000000000000'+frameData[0:8]+'\n'

    def transformFrameFile(self,fileName):
        r'''
        先把40bit的TXT帧文件转成60bit的TXT帧文件，再转成bytes类型的.npy文件，用于传输；
        '''
        #读入40比特的帧数据
        mylog.info('正在将40bit帧文件转换为60bit的倒序帧文件...')
        with open('./files/%s.txt' % fileName,'r') as net40b:
            frames = net40b.readlines()
            framesTrans = [self.transfer(f) for f in frames]

        #写入64比特的帧数据,fileName64b_reverse.txt 
        with open('./files/%s64b_reverse.txt' % fileName,'w') as net64b:
            temp=[net64b.write(f) for f in framesTrans]
            mylog.info('正在将60bit的帧文件转换为.npy文件...')

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

    def writeToUSBWithGap(self,fileName,gap):
        r'''
        把处理好的帧数据逐帧写入USB设备，每帧间隔gap，单位为ms；
        '''
        #先定义启动帧和结束帧
        startFrame1 = 10    #1010
        startFrame2 = 9     #1001
        endFrame = 11       #1011
        testFrame = 4       #0100
        try:
            mylog.info('正在写入帧文件...')
            frameData = numpy.load('./files/%s.npy' % fileName)
            #某些情况下需要降低发送速度，下面将帧数据分块发送；
            frameData = bytes(frameData)
            dataLength = len(frameData)
            i = 0
            while i < dataLength:
                time.sleep(gap/1000)
                j = i
                while j < dataLength:
                    frameTitle = frameData[j+7] >> 4
                    if frameTitle == startFrame1 or frameTitle == startFrame2 or frameTitle == endFrame or frameTitle == testFrame:
                        break
                    j += 8
                if not self.usbHandler.writeToUSB(frameData[i:j+8]):
                    mylog.error('Error: 写入失败！')
                    return False
                i = j+8
        except BaseException as e:
            mylog.error("Error: 写入帧文件失败。")
            mylog.error(str(e))
            return False
        else:
            mylog.info('已成功写入帧文件。')
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