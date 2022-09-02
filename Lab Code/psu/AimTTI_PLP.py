# -*- coding: utf-8 -*-
"""
Created on Mon Jul 23 06:48:45 2018
Python3 compatible

@author: lcfl72

Interface code to run Aim/TTI PL-P series benchtop power supply
"""
#from .Comms import CommsConnection, COMMS_RS232
from instrument import serial_instrument

from time import sleep

class dev_TTI_PLP(serial_instrument):  
    '''
    Class to control TTI PSU over USB-serial interface. Exposes the following properties:
    
    OutputOn, OutputOff - to set the output state; write only
    Vout, Iout          - the present output voltage/current; read only
    SetCurrent          - Current setpoint; read/write, subject to preset voltage limit
    SetVoltage          - Voltage setpoint; read/write, subject to preset current limit   
    '''
    def __init__(self, portstr='COM1', baud=9600):  
        #self.dev=CommsConnection(COMMS_RS232, portstr=portstr, baud=baud, commspause=0.5)        
        #self.TermChr='\n'  
        super().__init__(terminator='\n', port=portstr, baud=baud)
        
        
        self._Isetval=0.0
        self._Vsetval=0.0
        self._Vlimit=30.00   #Software voltage and current limits
        self._Ilimit=1.0
        self._LowIrangelimit=0.5    #Maximum corrent in low range
        self._Iranges=[1,2] #low or high current output range
        self._OCPtripcurrent=1.0    #Hardware current limit
        self._OVPtripvoltage=30.0
        self._EnableIRangeChange=False #Behaviour on reaching low current range limit if set to low current range: increase range or not.
        self.write('OCP1 {}'.format(self._OCPtripcurrent))
        self.write('OVP1 {}'.format(self._OVPtripvoltage))
        self._outputFlag=False
        self.Setup()
        
    def Setup(self):
        #commands to initialise device here
        self.write('*CLS')
        self.OutputOff
        self._Irange1val=0
        self._Irange1=2
        self._Iset=0.0
        self._Vset=0.0   
        
    
    @property
    def _Vset(self):
        if (not self._outputFlag):
            retstr=''
            tries=0
            while (len(retstr)<9 and tries<100):
                retstr = self.query('V1?')    
                tries+=1
            self._Vsetval=float(retstr[2:-1])    
        return self._Vsetval
    
    @_Vset.setter
    def _Vset(self, Vval):
        if Vval > self._Vlimit:
            Vval=self._Vlimit                
        self._Vsetval=Vval
        self.write('V1 {}'.format(self._Vsetval))
        #sleep(0.1)
       
    @property
    def _Irange1(self):
        return int(self.query('IRANGE1?')[:-1])
        
    @_Irange1.setter
    def _Irange1(self, Irange1):
        if Irange1 in self._Iranges:
            if not Irange1 == self._Irange1val:
                self._Irange1val=Irange1
                self.OutputOff
                self.write('IRANGE1 {}'.format(self._Irange1val))
                

    @property
    def _Iset(self):
        if (not self._outputFlag):
            retstr=''
            tries=0
            while (len(retstr)<9 and tries<100):
                retstr = self.query('I1?')
                tries+=1
            self._Isetval=float(retstr[2:-1])
        return self._Isetval
    
    @_Iset.setter
    def _Iset(self, Ival):
        if Ival > self._Ilimit:
            Ival=self._Ilimit        
        if self._Irange1==1 and Ival > self._LowIrangelimit:
            if self._EnableIRangeChange:
                self._Irange1 = 2
            else:
                Ival = self._LowIrangelimit             
        self._Isetval=Ival
        self.write('I1 {}'.format(self._Isetval))
        #sleep(0.1)
        
    @property 
    def Vout(self):
        return float(self.query('V1O?')[:-2])
    
    @property    
    def Iout(self):
        return float(self.query('I1O?')[:-2])
     
    def _Status(self):
        return int(self.query('*ESR?'))
    
    @property
    def OutputOn(self):
        self.write('OP1 1')
        self._outputFlag=True
        #sleep(0.5)
    
    @property    
    def OutputOff(self):
        self.write('OP1 0')
        self._outputFlag=False
    
    @property
    def SetCurrent(self):
        return self._Iset
    
    @SetCurrent.setter    
    def SetCurrent(self, Ival):
        self._Vset=self._Vlimit
        self._Iset=Ival
        self.OutputOn
        
    @property
    def SetVoltage(self):
        return self._Vset

    @SetVoltage.setter        
    def SetVoltage(self, Vval):
        self._Iset=self._Ilimit
        self._Vset=Vval
        self.OutputOn
        
        

if (__name__ == '__main__'):  
    
    
    TTI = dev_TTI_PLP(portstr='COM12')    
    
    idn=TTI.get_identity()
    print('GetIdentity (*IDN?) in AimTTI_PLP.py returns: {}'.format(idn))
    
    TTI._Vlimit = 12.0
    
    TTI.SetVoltage = 12.0
    TTI.SetCurrent = 0.18
    
    sleep(2)
    TTI.OutputOff
        
    for _ in range(10):
        
        sleep(0.2)
        TTI.OutputOn
        sleep(0.2)
        TTI.OutputOff
    
    
#    TTI.OutputOn
#    sleep(2)
#    for i in range(100):
#        TTI.SetCurrent=((i+1)/1000)        
#        #T72._Vset=(i+1)/10
#        st=TTI._Iset
#        print('I1? returns {}'.format(st)) 
#        st=TTI.Iout
#        print('I1O? returns {}'.format(st))
#    TTI.OutputOff

    TTI.close() 
         
