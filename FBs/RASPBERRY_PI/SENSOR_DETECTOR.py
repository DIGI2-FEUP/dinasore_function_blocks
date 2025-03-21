import RPi.GPIO as GPIO
import time

class SENSOR_DETECTOR:
  
    def __init__(self):

        pass
    
    def schedule(self, event_input_name, event_input_value, gpio_number, rate):
    
        if event_input_name == 'INIT':
            
            if gpio_number == None:
                print("Invalid GPIO")
            else:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(gpio_number, GPIO.IN)
                print("Initializing sensor...")
                return [event_input_value, None, -1]
        
        elif event_input_name == 'READ':
           
            if GPIO.input(gpio_number) == GPIO.LOW:
                vibration_status = 1
            else:
                vibration_status = 0
            if rate == None:
                rate=0
            print("Checking sensor for vibration...")
            print(vibration_status)
            time.sleep(rate)
            return [None, event_input_value, vibration_status] 
   
