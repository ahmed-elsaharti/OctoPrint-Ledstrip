# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import RPi.GPIO as GPIO
import sys
from subprocess import Popen
import time
import octoprint.plugin
import octoprint.events
import pigpio
from octoprint.util import RepeatedTimer
pi = pigpio.pi()
R_pwm=20
G_pwm=16
B_pwm=19
pi.set_PWM_dutycycle(R_pwm, 0)
pi.set_PWM_dutycycle(G_pwm, 0)
pi.set_PWM_dutycycle(B_pwm, 0)

class OctoLEDPlugin(octoprint.plugin.StartupPlugin,
                       octoprint.plugin.ShutdownPlugin,
                       octoprint.plugin.SettingsPlugin,
                       octoprint.plugin.AssetPlugin,
                       octoprint.plugin.TemplatePlugin,
                       octoprint.plugin.SimpleApiPlugin,
                       octoprint.plugin.WizardPlugin,
                       octoprint.plugin.ProgressPlugin,
                       octoprint.plugin.EventHandlerPlugin,
                       octoprint.plugin.RestartNeedingPlugin):

    RVal=GVal=BVal=0
    blinkR=blinkG=blinkB=100
    blinker=0
    current_state="None"
    BlinkTimer=0
    printprogress=0

    supported_events = {
        'Connected': 'idle',
        'Disconnected': 'disconnected',
        'PrintFailed': 'failed',
        'PrintDone': 'success',
        'PrintPaused': 'paused',
        'PrintResumed': 'resumed'
    }

    def blinkRGB(self):       
        if self.blinker == 1:
           self._logger.info("BLINK OFF!!")
           self.setRGB(0,0,0)
           self.RVal=self.GVal=self.BVal=0
           self.blinker = 0                                                                                                     
        else:
           self._logger.info("BLINK ON!!")
           self.setRGB(self.blinkR,self.blinkG,self.blinkB)
           self.RVal=self.blinkR
           self.GVal=self.blinkG
           self.BVal=self.blinkB
           self.blinker = 1

    def setRGB(self,RFinal,GFinal,BFinal):  
        self._logger.info("R "+str(RFinal)+" G "+str(GFinal)+" B "+str(BFinal))
        pi.set_PWM_dutycycle(R_pwm, RFinal)
        pi.set_PWM_dutycycle(G_pwm, GFinal)
        pi.set_PWM_dutycycle(B_pwm, BFinal)
        self.RVal=RFinal
        self.GVal=GFinal
        self.BVal=BFinal

    def fadeRGB(self,RFinal,GFinal,BFinal):      

        while self.RVal != RFinal or self.GVal != GFinal or self.BVal != BFinal:
            if self.RVal < RFinal:
                self.RVal += 1
                pi.set_PWM_dutycycle(R_pwm, self.RVal)
            elif self.RVal > RFinal:
                self.RVal -= 1
                pi.set_PWM_dutycycle(R_pwm, self.RVal)
            if self.GVal < GFinal:
                self.GVal += 1
                pi.set_PWM_dutycycle(G_pwm, self.GVal)
            elif self.GVal > GFinal:
                self.GVal -= 1
                pi.set_PWM_dutycycle(G_pwm, self.GVal)
            if self.BVal < BFinal:
                self.BVal += 1
                pi.set_PWM_dutycycle(B_pwm, self.BVal)
            elif self.BVal > BFinal:
                self.BVal -= 1
                pi.set_PWM_dutycycle(B_pwm, self.BVal)
            time.sleep(0.03)
            self._logger.info("R "+str(self.RVal)+" G "+str(self.GVal)+" B "+str(self.BVal))


    def on_after_startup(self):
        self._logger.info("----------Starting LED strip plugin----------")
        self.BlinkTimer = RepeatedTimer(0.5,self.blinkRGB)

    def on_shutdown(self):
        self._logger.info("----------Shutting LED strip plugin down----------")
        self.BlinkTimer.cancel()
        self.fadeRGB(0,0,0)


    def on_print_progress(self, storage, path, progress):
        self._logger.info(progress)
        self._logger.info("LOGGING IT NAAW")
        self.fadeRGB(100-int(progress),int(progress),0)
        self.printprogress=progress


    def on_event(self, event, payload):
        try:
					  self.BlinkTimer = RepeatedTimer(0.5,self.blinkRGB)
            self.current_state=self.supported_events[event]
            self._logger.info(self.current_state)
            if self.current_state == "resumed":
                self.BlinkTimer.cancel()
                self.fadeRGB(100-int(self.printprogress),int(self.printprogress),0)
            if self.current_state == "idle":
                self.BlinkTimer.cancel()
                self.fadeRGB(100,100,100)
            if self.current_state == "disconnected":
                self.BlinkTimer.cancel()
                self.fadeRGB(0,0,0)
            if self.current_state == "success":
                self.BlinkTimer.cancel()
                self.blinkR=0
                self.blinkG=100
                self.blinkB=0
                self.BlinkTimer = RepeatedTimer(0.5,self.blinkRGB)
                self.BlinkTimer.start()
            if self.current_state == "failed":
                self.BlinkTimer.cancel()
                self.blinkR=100
                self.blinkG=0
                self.blinkB=0
                self.BlinkTimer = RepeatedTimer(0.5,self.blinkRGB)
                self.BlinkTimer.start()
            if self.current_state == "paused":
                self.BlinkTimer.cancel()
                self.blinkR=0
                self.blinkG=0
                self.blinkB=100
                self.BlinkTimer = RepeatedTimer(0.5,self.blinkRGB)
                self.BlinkTimer.start()
        except KeyError:  # The event isn't supported
            pass

__plugin_name__ = "OctoLED"
__plugin_version__ = "1.0.0"
__plugin_description__ = "Plugin to control 4 pin RGB LED strips"
__plugin_pythoncompat__ = ">=2.7,<4"
__plugin_implementation__ = OctoLEDPlugin()
