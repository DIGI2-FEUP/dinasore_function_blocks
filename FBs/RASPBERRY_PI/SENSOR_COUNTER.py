# -*- coding: utf-8 -*-
"""
Created on Fri Mar 21 09:52:50 2025

@author: jaime
"""
import RPi.GPIO as GPIO
import time

class SENSOR_COUNTER:
  
    def __init__(self):

        pass
    
    def schedule(self, event_input_name, event_input_value, gpio_number, rate):
        global counter
        if event_input_name == 'INIT':
            if gpio_number == None:
                print("Invalid GPIO")
            else:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(gpio_number, GPIO.IN)
                counter=0
                print("Initializing sensor...")
                return [event_input_value, None, -1]
        
        elif event_input_name == 'READ':
            if rate == None:
                rate=0
            previous_state=GPIO.input(gpio_number)
            while GPIO.input(gpio_number) == GPIO.HIGH:
                pass
            if previous_state == GPIO.HIGH:
                counter=counter+1
                print("Vibration detected.")
                print(counter)
                time.sleep(rate)
            return [None, event_input_value, counter] 
