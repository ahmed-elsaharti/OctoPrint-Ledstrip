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
#    global_counter=0
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

    event_effects = {
        'idle': "staticfade",
        'disconnected': "staticfade",
        'failed': "blink",
        'success': "blink",
        'paused': "blink"
    }

    event_colors = {
        'idle': dict(R=100,G=100,B=100),
        'disconnected': dict(R=0,G=0,B=0),
        'failed': dict(R=100,G=0,B=0),
        'success': dict(R=0,G=100,B=0),
        'paused': dict(R=0,G=0,B=100)
    }



################## Shortening stuff

#EFFECTS:

    def staticfadefnc(self):
        self.fadeRGB(self.event_colors[self.current_state]["R"],self.event_colors[self.current_state]["G"],self.event_colors[self.current_state]["B"])
    def blinkfnc(self):
        self.blinkR=self.event_colors[self.current_state]["R"]
        self.blinkG=self.event_colors[self.current_state]["G"]
        self.blinkB=self.event_colors[self.current_state]["B"]
        self.BlinkTimer = RepeatedTimer(0.5,self.blinkRGB)
        self.BlinkTimer.start()  


#Effects function (for all supported states):

    def effectfnc(self):
        try:
            if self.BlinkTimer != 0:
                self.BlinkTimer.cancel()
            self.effects_dict[self.event_effects[self.current_state]](self)
        except KeyError:  # effect is 'none'
            pass

#Function call dicts    

    effects_dict = {
        'staticfade': staticfadefnc,
        'blink': blinkfnc
    }

    event_dict = {
        'idle': effectfnc,
        'disconnected': effectfnc,
        'success': effectfnc,
        'failed': effectfnc,
        'paused': effectfnc        
    }

####################################



    def blinkRGB(self):       
        if self.blinker == 1:
           self._logger.info("********RGB BLINK OFF********")
           self.setRGB(0,0,0)
           self.RVal=self.GVal=self.BVal=0
           self.blinker = 0                                                                                                     
        else:
           self._logger.info("********RGB BLINK ON********")
           self.setRGB(self.blinkR,self.blinkG,self.blinkB)
           self.RVal=self.blinkR
           self.GVal=self.blinkG
           self.BVal=self.blinkB
           self.blinker = 1
#            self.global_counter += 1    todo: Implement global counter to be able to set timeout on blinks

    def setRGB(self,RFinal,GFinal,BFinal):  
        if self.R_pwm != "" and self.G_pwm != "" and self.B_pwm != "":
            #self._logger.info("R "+str(RFinal)+" G "+str(GFinal)+" B "+str(BFinal))
            self.pi.set_PWM_dutycycle(self.R_pwm, RFinal)
            self.pi.set_PWM_dutycycle(self.G_pwm, GFinal)
            self.pi.set_PWM_dutycycle(self.B_pwm, BFinal)
            self.RVal=RFinal
            self.GVal=GFinal
            self.BVal=BFinal
            self._logger.info("LEDstrip set to R "+str(self.RVal)+" G "+str(self.GVal)+" B "+str(self.BVal))
        else:
            self.RVal=RFinal
            self.GVal=GFinal
            self.BVal=BFinal
            self._logger.info("LEDstrip: No pins, setting to R "+str(self.RVal)+" G "+str(self.GVal)+" B "+str(self.BVal))

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
            self._logger.info("LEDstrip faded to R "+str(self.RVal)+" G "+str(self.GVal)+" B "+str(self.BVal))
        else:
            self.RVal=RFinal
            self.GVal=GFinal
            self.BVal=BFinal
            self._logger.info("LEDstrip: No pins, setting to R "+str(self.RVal)+" G "+str(self.GVal)+" B "+str(self.BVal))


    def on_after_startup(self):
        self._logger.info("*********************************************")
        self._logger.info("----------Starting LEDstrip plugin----------")
        self._logger.info("*********************************************")
        if self._settings.get(["Rpin"]) != "" and self._settings.get(["Gpin"]) != "" and self._settings.get(["Bpin"]) != "": 
            self.R_pwm=int(self._settings.get(["Rpin"]))
            self.G_pwm=int(self._settings.get(["Gpin"]))
            self.B_pwm=int(self._settings.get(["Bpin"]))
        self.BlinkTimer = RepeatedTimer(0.5,self.blinkRGB)
        if self.current_state != "idle":
            self.setRGB(0,0,0)
        for key in self.event_effects:
            self.event_effects[key]=self._settings.get([key+"_effect"])
        for key in self.event_colors:
            h=self._settings.get([key+"_color"])
            hex = h.lstrip('#')
            self.event_colors[key]["R"]=int(tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))[0]/2.55)
            self.event_colors[key]["G"]=int(tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))[1]/2.55)
            self.event_colors[key]["B"]=int(tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))[2]/2.55)

        

    def on_print_progress(self, storage, path, progress):
        #self._logger.info(progress)
        if self.BlinkTimer != 0:
            self.BlinkTimer.cancel()
        self._logger.info("LEDstrip logged progress change "+str(progress))
        self.fadeRGB(100-int(progress),int(progress),0)
        self.printprogress=progress



    def get_template_configs(self):
        return [
            dict(type="navbar", custom_bindings=False),
            dict(type="settings", custom_bindings=False)
        ]

    def on_shutdown(self):
        self._logger.info("**************************************************")
        self._logger.info("----------Shutting LEDstrip plugin down----------")
        self._logger.info("**************************************************")
        self.fadeRGB(0,0,0)                                                              
        self.pi.stop()                                                                   

    def get_settings_defaults(self):                                                
        return dict(Rpin="",Gpin="",Bpin="",
                    idle_effect="staticfade",idle_color="#FFFFFF",
                    disconnected_effect="staticfade",disconnected_color="#000000",
                    failed_effect="blink",failed_color="#FF0000",
                    success_effect="blink",success_color="#00FF00",
                    paused_effect="blink",paused_color="#0000FF")

    def get_template_vars(self):                    # Might not be needed...idr
        if self._settings.get(["Rpin"]) != "" and self._settings.get(["Gpin"]) != "" and self._settings.get(["Bpin"]) != "":                                                     # NEW
            self.R_pwm=int(self._settings.get(["Rpin"]))
            self.G_pwm=int(self._settings.get(["Gpin"]))
            self.B_pwm=int(self._settings.get(["Bpin"]))
            return dict(Rpin=50,Gpin=self._settings.get(["Gpin"]),Bpin=self._settings.get(["Bpin"]))
        
    def on_settings_initialized(self):
        temp_r_val=self.RVal
        temp_g_val=self.GVal
        temp_b_val=self.BVal
        self.fadeRGB(0,0,0)
        if self._settings.get(["Rpin"]) != "" and self._settings.get(["Gpin"]) != "" and self._settings.get(["Bpin"]) != "": 
            self.R_pwm=int(self._settings.get(["Rpin"]))
            self.G_pwm=int(self._settings.get(["Gpin"]))
            self.B_pwm=int(self._settings.get(["Bpin"]))
            self._logger.info("LEDstrip initialized RGB pins: "+str(self.R_pwm)+str(self.G_pwm)+str(self.B_pwm))
            self.RVal=self.GVal=self.BVal=0
            self.fadeRGB(temp_r_val,temp_g_val,temp_b_val)
        for key in self.event_effects:
            self.event_effects[key]=self._settings.get([key+"_effect"])
        for key in self.event_colors:
            h=self._settings.get([key+"_color"])
            hex = h.lstrip('#')
            self.event_colors[key]["R"]=int(tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))[0]/2.55)
            self.event_colors[key]["G"]=int(tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))[1]/2.55)
            self.event_colors[key]["B"]=int(tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))[2]/2.55)
     

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
            self.RVal=self.GVal=self.BVal=0
            self.fadeRGB(temp_r_val,temp_g_val,temp_b_val)
        for key in self.event_effects:
            self.event_effects[key]=self._settings.get([key+"_effect"])
        for key in self.event_colors:
            h=self._settings.get([key+"_color"])
            hex = h.lstrip('#')
            self.event_colors[key]["R"]=int(tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))[0]/2.55)
            self.event_colors[key]["G"]=int(tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))[1]/2.55)
            self.event_colors[key]["B"]=int(tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))[2]/2.55)

    def on_event(self, event, payload):
        try:
            self.current_state=self.supported_events[event]
            self._logger.info("LEDstrip recorded supported event: "+str(self.current_state))
            if self.current_state == "resumed":
                if self.BlinkTimer != 0:
                    self.BlinkTimer.cancel()
                self.fadeRGB(100-int(self.printprogress),int(self.printprogress),0)             # Needs to be dependent on progress effect

            self.event_dict[self.current_state](self)           #Much shorter
        except KeyError:  # The event isn't supported
            pass

__plugin_name__ = "LEDstrip"
__plugin_version__ = "0.1.4"
__plugin_description__ = "Plugin to control 4 pin RGB LED strips"
__plugin_pythoncompat__ = ">=2.7,<4"
__plugin_implementation__ = LEDstripPlugin()


# 8/22/2020
