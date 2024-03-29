from ipaddress import ip_address
import snap7
class S7_READ:    
    def __init__(self):
        self.state = None
        self.client = snap7.client.Client()
        
    def schedule(self, event_name, event_value, ip_address, rack, number, port, db_number,start, size):

        if event_name == 'INIT':
            self.client.connect(ip_address,rack,number,port)
            status = self.client.get_connected()
            if(status == True):
                print('Connection sucessfully initiated with device at {0}'.format(ip_address))
            else:
                print('Error initiating connection with S7 PLC')
            return [event_value, None, None]

        elif event_name == 'READ':
            #db_read(db_number: int, start: int, size: int)
            data = self.client.db_read(db_number,start,size)
            print(data)
            int_val = int.from_bytes(data, "big")
            return [None, event_value, int_val]