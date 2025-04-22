'''
Author: Noah & Aljaž
Filename: RIPv2_router.py
'''

################################# imports
from socket import *
import select

# from reader import read_config_file, read_input_ports
from threading import Timer
from RoutingTable import *
from Packet import *
from _Timer import *

import random
################################# 



'''
██████╗  ██████╗ ██╗   ██╗████████╗███████╗██████╗ 
██╔══██╗██╔═══██╗██║   ██║╚══██╔══╝██╔════╝██╔══██╗
██████╔╝██║   ██║██║   ██║   ██║   █████╗  ██████╔╝
██╔══██╗██║   ██║██║   ██║   ██║   ██╔══╝  ██╔══██╗
██║  ██║╚██████╔╝╚██████╔╝   ██║   ███████╗██║  ██║
╚═╝  ╚═╝ ╚═════╝  ╚═════╝    ╚═╝   ╚══════╝╚═╝  ╚═╝
                                                   

#######################
[X] Create Sockets() ~ initialises the sockets to receive packets
[] Packet Process Update() ~ Process packets received & making changes to routing table
[] Trigger_Update() ~ Send out triggered update to neighbours with paths that have changed
[] Check_Timeout()  ~ put all the unreachable or timedout paths into garbage heap if not already in there
[] Check_garbage() ~ remove the paths from routing table if their garbage collection timer is expired
[] periodic_update() ~ send the whole routing table to each neighbour
[] main() ~ inf loop to check router's listening sockets for any updates and monitor how up to date the routing table is
#######################
'''

LOCAL_HOST = "127.0.0.1"

# PERIODIC_UPDATES = None


class RIPv2_Router:

    def __init__(self, router_ID, inputs, outputs, timeout=30, garbage_time=30):
        self.router_ID = router_ID
        self.inputs = inputs # Input Ports
        self.outputs = outputs # Output Ports        ROUTER_OUTPUTS

        # Timeout & Garbage to be done !
        self.timeout = timeout # in seconds
        self.garbage_time = garbage_time
        self.timeout_timer = {} # Dict
        self.garbage_time = {} # Dict

        # Create input sockets
        self.sockets = self.create_sockets()

        # Read Packet

        # # Initiate the routing table
        # self.routing_table = []  # Start with an empty routing table
        # self.routing_table.append(RT_entry(address, next_hop, metric))
        self.routing_table = RoutingTable()

        # self.routing_table = RT_entry(self.router_ID)

        # self.routing_table = RT_entry(self.router_ID, metric)

        # Setup to send periodic updates
        self.periodic_updates = None

        print("Router Daemon Initialised...\n")
        print(f"Router: {self.router_ID}\n")
        print(f"Inputs: {self.inputs}\n")
        print(f"Outputs: {self.outputs}\n")


        

        self.packet_manager = Packet(self.routing_table,
                                    self.router_ID,
                                    self.outputs,
                                    self.sockets)

        self.init_periodic_update() # periodic update loop is initialised

        
        



    def create_sockets(self): # Completed 
        '''
            We initialise the socket so that we can receive packets        
        '''
        sockets_list = {} #

        try:
            for port in self.inputs:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind((LOCAL_HOST, port))
                sockets_list[port] = sock
            return sockets_list

        except Exception as e:
            print(f"Error creating sockts {e}")
            
    
    def init_periodic_update(self):
        '''
            Starts the update loop & sends update to neighbours
        '''
        def send_update():
            '''
                calls helper function to send an update to 
                all the neighbour routers
            '''
            self.update_neighbours()
            print("Update packet Sent")
            self.init_periodic_update()

        plus_minus = random.uniform(0, 5)  # offset by a small random time (+/- 0 to 5 seconds)
        self.periodic_updates = Timer(10 + plus_minus, send_update) # Triggers to send an update every 30 seconds
        self.periodic_updates.start() # This triggers the timer to start (which is the line above)
    

    def update_neighbours(self):
        '''
            sends an update packet to all neighbours
        '''
        for link in self.outputs:  # EXAMPLE: link = ['5000', '1', '1']
            port = int(link[0])
            metric = int(link[1])
            neighbour_id = int(link[2])

            packet = self.packet_manager.create_packet({
                'router_id': neighbour_id,
                'metric': metric
            })

            if not packet:
                print(f"[!] No Packet created for Router: {neighbour_id}")

            try:
                send_to_socket = self.sockets[self.inputs[0]]
                send_to_socket.sendto(packet, (LOCAL_HOST, port))

            except Exception as e:
                print(f"[ERROR] Sending to Router: {neighbour_id} - Port: {port}\n {e}\n") 

            else:
                print(f"[SUCCESS] Packet sent to Router: {neighbour_id} - Port: {port}\n")

        # Sorry Bro had to comment thsi out but I copied lots of tit form you :)
        # for link in self.outputs: # ROUTER_OUTPUTS
        #     neighbour_id = link['Router-ID']
        #     port = link['Port']

        #     packet = self.packet_manager.create_packet(neighbour_id)

        #     if not packet:
        #         print(f"[!] No Packet created for Router: {neighbour_id}")

        #     try:
        #         send_to_socket = self.sockets[self.inputs[0]]
        #         send_to_socket.sendto(packet, (LOCAL_HOST, port))

        #     except Exception as e:
        #         print(f"[ERROR] Sending to Router: {neighbour_id} - Port: {port}\n {e}\n") 

        #     else: # Packet successfully sent to socket
        #         print(f"[SUCCESS] Packet sent to Router: {neighbour_id} - Port: {port}\n")

                

        


#     #######################################
# '''
#     ████████╗██╗███╗   ███╗███████╗██████╗ 
#     ╚══██╔══╝██║████╗ ████║██╔════╝██╔══██╗
#        ██║   ██║██╔████╔██║█████╗  ██████╔╝
#        ██║   ██║██║╚██╔╝██║██╔══╝  ██╔══██╗
#        ██║   ██║██║ ╚═╝ ██║███████╗██║  ██║
#        ╚═╝   ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝     
#     30s                                 
# '''


    def init_timer(self, dst_id):
        '''
            Timer is Initialised
        '''
        
        if dst_id in self.timeout_timer:
            self.timeout_timer[dst_id]
    

    ####################### Listen respond and listen to incoming packets

    '''
        Get up and teach instead of handing out these
        ██████╗  █████╗  ██████╗██╗  ██╗███████╗████████╗███████╗
        ██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██╔════╝╚══██╔══╝██╔════╝
        ██████╔╝███████║██║     █████╔╝ █████╗     ██║   ███████╗
        ██╔═══╝ ██╔══██║██║     ██╔═██╗ ██╔══╝     ██║   ╚════██║
        ██║     ██║  ██║╚██████╗██║  ██╗███████╗   ██║   ███████║
        ╚═╝     ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝ yo
    '''

    def monitor_RT(self): 
        '''
            This is an infinite loop where we will listen for updates in the sockets and process updates
            and send out updates to other routers.
        '''

        while True: # Is this right?
            readable, _, _ = select.select(list(self.sockets.values()), [], [], 1)
            for sock in readable:
                try:
                    data, addr = sock.recvfrom(1024)
                    print(f"Received packet from {addr}\n")
                    self.packet_manager.recieve_and_process_packet(data)
                    print("Routing Table Updated...\n")
                    for route in self.routing_table:
                        print(f"→ Destination: {route.router_id}, Next Hop: {route.next_hop}, Metric: {route.metric}")
                    print("-" * 50)

                except Exception as e:
                    print(f"Error receiving data: {e}")






# if __name__ == "__main__":
#     reader()

