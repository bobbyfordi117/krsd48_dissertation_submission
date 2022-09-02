# -*- coding: utf-8 -*-
"""
Created on Wed Apr  1 10:04:22 2020

Communications using National Instruments (compatible) GPIB interface [32 or 64 bit] and rs232/serial interface

Requires:
    PySerial (3.4 tested)
    NI GPIB drivers (or compatible?) requires Windows at present

@author: Aidan Hindmarch
"""

import serial
import threading
import ctypes  
from time import sleep
from platform import system

#RQS = (1<<11)  
#SRQ = (1<<12)  
#TIMO = (1<<14)  
  





class _GPIB_instrument(object):
    '''Base GPIB communications class
        This is a rudimentary wrapper around the NI 488.2 dll.
        TODO: Check type coercion is appropriate!
    '''
    _gpib = None 
    
    def __init__(self, address=0, board=0, pause=0.1, library='ni4882.dll'): # NI-compatible dll (64 or 32 bit)
        
        assert system() == 'Windows'  
        if type(self)._gpib is None:
            #GPIB._gpib=getattr(ctypes.windll,"gpib488")  # Keithley-specific dll  
            type(self)._gpib = getattr(ctypes.windll, library)  
        self._gpib = type(self)._gpib
        
        self.pause = pause
        self.address = address
        self.board = board
        self._lock = threading.RLock()
        
        with self._lock:
            self.hwaddress = self._gpib.ibdev(self.board, self.address, 0, 13, 1, 0) 
            sleep(self.pause) 
            self._gpib.ibclr(self.hwaddress)
            sleep(self.pause)            
    
    def __del__(self):
        try:
            self._gpib.ibonl(self.hwaddress, 0)
        except AttributeError:
            pass
        
    def close(self):
        with self._lock:
            self._gpib.ibonl(self.hwaddress, 0)  
  
    def _write(self, s):
        lst = ctypes.c_short * 2
        addrlist = lst(self.address, 0)
        self._gpib.SendSetup(self.board, addrlist)            
        self._gpib.ibwrt(self.hwaddress, s, len(s)) 
        sleep(self.pause)
        self._gpib.SendIFC(self.board)
    
    def _read(self, length):
        result = ctypes.create_string_buffer(length) 
        self._gpib.ReceiveSetup(self.board, self.address)
        self._gpib.ibrd(self.hwaddress, result, length) 
        self._gpib.SendIFC(self.board)
        return result
    
    def write(self, s):
        with self._lock:
            self._write(s.encode())
  
    def read(self, length=4096):
        with self._lock:
            return self._read(length=length).value.decode()
    
    def readb(self, length):
        with self._lock:
            return self._read(length=length).raw
    
    def query(self, s, length=4096):
        with self._lock:
            self._write(s.encode())
            return self._read(length=length).value.decode()
    
    def queryb(self, s, length):
        with self._lock:
            self._write(s.encode())
            return self._read(length=length).raw 
 
    def clear(self):
        with self._lock:
            self._gpib.ibclr(self.hwaddress)  
  
    def rsp(self):  
        with self._lock:
            result = ctypes.c_char_p('\000')  
            self.spb = self._gpib.ibrsp(self.hwaddress, result)     
            if len(result.value) > 0:  
                return ord(result.value)  
            else:  
                return -256  
    
    


class _rs232_instrument(object):
    '''Base serial instrument class.
        handles coercion between strings and bytearrays where required
        comand strings should have appropriate termination characters
    '''
    def __init__(self, port='COM1', baud=9600, bytesize=8, parity='N', stopbits=1, dtsdtr=False, xonxoff=False, timeout=0.1, write_timeout=0.1):
                
        self.port = port
        self._lock = threading.RLock()
        self._serial = serial.Serial()
        self._serial.port = port
        self._serial.baudrate = baud
        self._serial.parity = parity
        self._serial.bytesize = bytesize
        self._serial.stopbits = stopbits
        self._serial.timeout = timeout
        self._serial.write_timeout=write_timeout
        self._serial.xonxoff = xonxoff
        self._serial.dsrdtr = dtsdtr
        try:
            with self._lock:
                self._serial.open()
        except serial.SerialException as e:
            raise serial.SerialException('Unable to connect to serial device on {}. Check power, cabling, and device address.'.format(port)) from e
            
    def __del__(self):
        try:
            self._serial.close()
            del self._serial
            del self._lock
        except AttributeError:
            pass

    def close(self):
        with self._lock:
            self._serial.close()
        
    def write(self, cmd): 
        with self._lock:
            self._serial.write(cmd.encode())     
    
    def read(self, bufferlength=None): 
        with self._lock:
            return self._serial.read_until(self._term_chr.encode(), size=bufferlength).decode()
     
    def readb(self, bufferlength):
        with self._lock:
            return self._serial.read(bufferlength)
            
    def query(self, cmd, bufferlength=None):
        with self._lock:
            self._serial.write(cmd.encode()) 
            return self._serial.read_until(self._term_chr.encode(), size=bufferlength).decode()
        
    def queryb(self, cmd, bufferlength):
        with self._lock:
            self._serial.write(cmd.encode()) 
            return self._serial.read(bufferlength)
       
    def clear(self):
        pass
    
    def rsp(self):
        pass
    
    
    
class _instrument(object):    
    '''
    Handles appending/stripping termination characters to/from STRINGS
    Delegates the actual communications and type coercion to the appropriate _xxxx_instrument class
    '''
    def __init__(self, terminator='\n', **kwds):
        self._term_chr = terminator 
        super().__init__(**kwds)
        
    def write(self, cmd):
        super().write('{command}{terminator}'.format(command=cmd, terminator=self._term_chr))
        
    def read(self, bufferlength=None):
        return super().read(bufferlength=bufferlength).rstrip(self._term_chr).lstrip()
    
    def query(self, cmd, bufferlength=None):
        return super().query('{command}{terminator}'.format(command=cmd, terminator=self._term_chr), bufferlength=bufferlength).rstrip(self._term_chr).lstrip()
        
    def queryb(self, cmd, bufferlength=4096):
        return super().queryb('{command}{terminator}'.format(command=cmd, terminator=self._term_chr), bufferlength=bufferlength)
        
    def get_identity(self):
        return self.query('*IDN?')
    
class serial_instrument(_instrument, _rs232_instrument):
    pass

class gpib_instrument(_instrument, _GPIB_instrument):
    pass



if __name__ == '__main__':
    inst = serial_instrument(port='COM20', timeout=2)
    print(inst.query('*IDN?'))