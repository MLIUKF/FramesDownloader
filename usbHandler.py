import usb
import logging
import mylog
import array

r'''
USBHandler用于处理与USB接口有关的任务
'''

class USBHandler():

    def __init__(self):
        r'''
        连接USB设备。
        '''
        self.device = []
        self.deviceW = None
        self.deviceR = None
        self.inPoint = None
        self.outPoint = None
        self.usbReady = False
        self.deviceOrder = [1,0]
        self.findUSB()

    def findUSB(self):
        self.device = list(usb.core.find(find_all=True))
        self.deviceOrder[1], self.deviceOrder[0] = self.deviceOrder

        usbDeviceNum = len(self.device)
        if usbDeviceNum == 1:
            self.deviceR = self.device[0]
    
            self.deviceR.set_configuration()
            cfgR = self.deviceR.get_active_configuration()
            intfR = cfgR[(0,0)]
        
            self.inPoint = usb.util.find_descriptor(intfR,
                # match the first IN endpoint
                custom_match = lambda e: \
                    usb.util.endpoint_direction(e.bEndpointAddress) == \
                    usb.util.ENDPOINT_IN)

            self.usbReady = True
            mylog.info("1个USB设备已连接。")
        elif usbDeviceNum == 2:
            self.deviceW = self.device[self.deviceOrder[0]]
            self.deviceR = self.device[self.deviceOrder[1]]

            self.deviceW.set_configuration()
            cfgW = self.deviceW.get_active_configuration()
            intfW = cfgW[(0,0)]
    
            self.deviceR.set_configuration()
            cfgR = self.deviceR.get_active_configuration()
            intfR = cfgR[(0,0)]

            self.outPoint = usb.util.find_descriptor(intfW,
                # match the first OUT endpoint
                custom_match = lambda e: \
                    usb.util.endpoint_direction(e.bEndpointAddress) == \
                    usb.util.ENDPOINT_OUT)
        
            self.inPoint = usb.util.find_descriptor(intfR,
                # match the first IN endpoint
                custom_match = lambda e: \
                    usb.util.endpoint_direction(e.bEndpointAddress) == \
                    usb.util.ENDPOINT_IN)

            self.usbReady = True
            mylog.info("2个USB设备已连接。")
        else:
            self.usbReady = False
            mylog.error("Error: 可用USB设备数量不是2。")

    def writeToUSB(self,data):
        r"""Write data to usbDevice.
        The data parameter should be a sequence like type convertible to
        the array type (see array module).
        """
        if self.usbReady:
            try:
                self.deviceW.write(self.outPoint.bEndpointAddress,data)
            except BaseException as e:
                mylog.error("Error: Failed to write to USB.")
                mylog.error(str(e))
                return False
            else:
                return True
        else:
            mylog.error("Error: USB device is not ready.")
            return False

    def readFromUSB(self):
        r"""Read data from usbDevice.
        The bulksNum parameter should be the amount of bulks to be readed.
        One bulk is wMaxPacketSize(512) bytes.
        The method returns the data readed as an array. If read nothing, return None.
        """
        if self.usbReady:
            try:
                #readOutData = array.array('B')
                readOutBytes = self.deviceR.read(self.inPoint.bEndpointAddress,self.inPoint.wMaxPacketSize)
                return readOutBytes
            except BaseException as e:
                mylog.error("Error: Failed to read from USB.")
                mylog.error(str(e))
                return 1
        else:
            mylog.error("Error: USB device is not ready.")
            return None