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

class LEDstripPlugin(octoprint.plugin.StartupPlugin,
                       octoprint.plugin.ShutdownPlugin,
                       octoprint.plugin.SettingsPlugin,
                       octoprint.plugin.AssetPlugin,
                       octoprint.plugin.TemplatePlugin,
                       octoprint.plugin.SimpleApiPlugin,
                       octoprint.plugin.WizardPlugin,
                       octoprint.plugin.ProgressPlugin,
                       octoprint.plugin.EventHandlerPlugin,
                       octoprint.plugin.RestartNeedingPlugin):

    pi = pigpio.pi()
    R_pwm=""
    G_pwm=""
    B_pwm=""
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
        if self.R_pwm != "" and self.G_pwm != "" and self.B_pwm != "":
            self._logger.info("R "+str(RFinal)+" G "+str(GFinal)+" B "+str(BFinal))
            self.pi.set_PWM_dutycycle(self.R_pwm, RFinal)
            self.pi.set_PWM_dutycycle(self.G_pwm, GFinal)
            self.pi.set_PWM_dutycycle(self.B_pwm, BFinal)
            self.RVal=RFinal
            self.GVal=GFinal
            self.BVal=BFinal
            self._logger.info("R "+str(self.RVal)+" G "+str(self.GVal)+" B "+str(self.BVal))
        else:
            self.RVal=RFinal
            self.GVal=GFinal
            self.BVal=BFinal
            self._logger.info("R "+str(self.RVal)+" G "+str(self.GVal)+" B "+str(self.BVal))

    def fadeRGB(self,RFinal,GFinal,BFinal):      
        if self.R_pwm != "" and self.G_pwm != "" and self.B_pwm != "":
            while self.RVal != RFinal or self.GVal != GFinal or self.BVal != BFinal:
                if self.RVal < RFinal:
                    self.RVal += 1
                    self.pi.set_PWM_dutycycle(self.R_pwm, self.RVal)
                elif self.RVal > RFinal:
                    self.RVal -= 1
                    self.pi.set_PWM_dutycycle(self.R_pwm, self.RVal)
                if self.GVal < GFinal:
                    self.GVal += 1
                    self.pi.set_PWM_dutycycle(self.G_pwm, self.GVal)
                elif self.GVal > GFinal:
                    self.GVal -= 1
                    self.pi.set_PWM_dutycycle(self.G_pwm, self.GVal)
                if self.BVal < BFinal:
                    self.BVal += 1
                    self.pi.set_PWM_dutycycle(self.B_pwm, self.BVal)
                elif self.BVal > BFinal:
                    self.BVal -= 1
                    self.pi.set_PWM_dutycycle(self.B_pwm, self.BVal)
                time.sleep(0.01)
                self._logger.info("R "+str(self.RVal)+" G "+str(self.GVal)+" B "+str(self.BVal))
        else:
            self.RVal=RFinal
            self.GVal=GFinal
            self.BVal=BFinal
            self._logger.info("R "+str(self.RVal)+" G "+str(self.GVal)+" B "+str(self.BVal))


    def on_after_startup(self):
        self._logger.info("----------Starting LED strip plugin----------")
        self._logger.info("----------TEST----------")
        if self._settings.get(["Rpin"]) != "" and self._settings.get(["Gpin"]) != "" and self._settings.get(["Bpin"]) != "": 
            self.R_pwm=int(self._settings.get(["Rpin"]))
            self.G_pwm=int(self._settings.get(["Gpin"]))
            self.B_pwm=int(self._settings.get(["Bpin"]))
        self.BlinkTimer = RepeatedTimer(0.5,self.blinkRGB)
        self.setRGB(0,0,0)

    def on_shutdown(self):
        self._logger.info("----------Shutting LED strip plugin down----------")

    def on_print_progress(self, storage, path, progress):
        self._logger.info(progress)
        self._logger.info("LOGGING IT NAAW")
        self.fadeRGB(100-int(progress),int(progress),0)
        self.printprogress=progress



    def get_template_configs(self):
        return [
            dict(type="navbar", custom_bindings=False),
            dict(type="settings", custom_bindings=False)
        ]

    def on_shutdown(self):
        self._logger.info("----------Shutting LED strip plugin down----------")
        self.fadeRGB(0,0,0)                                                               # NEW
        self.pi.stop()                                                                    # NEW

    def get_settings_defaults(self):                                                 # NEW
        return dict(Rpin="",Gpin="",Bpin="")

    def get_template_vars(self):
        if self._settings.get(["Rpin"]) != "" and self._settings.get(["Gpin"]) != "" and self._settings.get(["Bpin"]) != "":                                                     # NEW
            self.R_pwm=int(self._settings.get(["Rpin"]))
            self.G_pwm=int(self._settings.get(["Gpin"]))
            self.B_pwm=int(self._settings.get(["Bpin"]))
            return dict(Rpin=self._settings.get(["Rpin"]),Gpin=self._settings.get(["Gpin"]),Bpin=self._settings.get(["Bpin"]))
        
    def on_settings_initialized(self):
        temp_r_val=self.RVal
        temp_g_val=self.GVal
        temp_b_val=self.BVal
        self.fadeRGB(0,0,0)
        if self._settings.get(["Rpin"]) != "" and self._settings.get(["Gpin"]) != "" and self._settings.get(["Bpin"]) != "": 
            self.R_pwm=int(self._settings.get(["Rpin"]))
            self.G_pwm=int(self._settings.get(["Gpin"]))
            self.B_pwm=int(self._settings.get(["Bpin"]))
            self._logger.info("INIT RGB Pins: "+str(self.R_pwm)+str(self.G_pwm)+str(self.B_pwm))
            self.RVal=self.GVal=self.BVal=0
            self.fadeRGB(temp_r_val,temp_g_val,temp_b_val)

    def on_settings_save(self,data):
        temp_r_val=self.RVal
        temp_g_val=self.GVal
        temp_b_val=self.BVal
        self.fadeRGB(0,0,0)
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        if self._settings.get(["Rpin"]) != "" and self._settings.get(["Gpin"]) != "" and self._settings.get(["Bpin"]) != "": 
            self.R_pwm=int(self._settings.get(["Rpin"]))
            self.G_pwm=int(self._settings.get(["Gpin"]))
            self.B_pwm=int(self._settings.get(["Bpin"]))
            self._logger.info("SAVE RGB Pins: "+str(self.R_pwm)+str(self.G_pwm)+str(self.B_pwm))
            self.RVal=self.GVal=self.BVal=0
            self.fadeRGB(temp_r_val,temp_g_val,temp_b_val)

    def on_event(self, event, payload):
        try:
            self.current_state=self.supported_events[event]
            self._logger.info(self.current_state)
            if self.current_state == "resumed":
                if self.BlinkTimer != 0:
                    self.BlinkTimer.cancel()
                self.fadeRGB(100-int(self.printprogress),int(self.printprogress),0)
            if self.current_state == "idle":
                if self.BlinkTimer != 0:
                    self.BlinkTimer.cancel()
                self.fadeRGB(100,100,100)
            if self.current_state == "disconnected":
                if self.BlinkTimer != 0:
                    self.BlinkTimer.cancel()
                self.fadeRGB(0,0,0)
            if self.current_state == "success":
                if self.BlinkTimer != 0:
                    self.BlinkTimer.cancel()
                self.blinkR=0
                self.blinkG=100
                self.blinkB=0
                self.BlinkTimer = RepeatedTimer(0.5,self.blinkRGB)
                self.BlinkTimer.start()
            if self.current_state == "failed":
                if self.BlinkTimer != 0:
                    self.BlinkTimer.cancel()
                self.blinkR=100
                self.blinkG=0
                self.blinkB=0
                self.BlinkTimer = RepeatedTimer(0.5,self.blinkRGB)
                self.BlinkTimer.start()
            if self.current_state == "paused":
                if self.BlinkTimer != 0:
                    self.BlinkTimer.cancel()
                self.blinkR=0
                self.blinkG=0
                self.blinkB=100
                self.BlinkTimer = RepeatedTimer(0.5,self.blinkRGB)
                self.BlinkTimer.start()
        except KeyError:  # The event isn't supported
            pass

__plugin_name__ = "LEDstrip"
__plugin_version__ = "0.1.1"
__plugin_description__ = "Plugin to control 4 pin RGB LED strips"
__plugin_pythoncompat__ = ">=2.7,<4"
__plugin_implementation__ = LEDstripPlugin()
