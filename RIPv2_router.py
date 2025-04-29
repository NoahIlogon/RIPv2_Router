'''
Author: Noah & Aljaž
Filename: RIPv2_router.py
'''

################################# imports
from socket import *
import select

from threading import Timer
from RoutingTable import *
from Packet import *


import random
import time
################################# 



'''
██████╗  ██████╗ ██╗   ██╗████████╗███████╗██████╗ 
██╔══██╗██╔═══██╗██║   ██║╚══██╔══╝██╔════╝██╔══██╗
██████╔╝██║   ██║██║   ██║   ██║   █████╗  ██████╔╝
██╔══██╗██║   ██║██║   ██║   ██║   ██╔══╝  ██╔══██╗
██║  ██║╚██████╔╝╚██████╔╝   ██║   ███████╗██║  ██║
╚═╝  ╚═╝ ╚═════╝  ╚═════╝    ╚═╝   ╚══════╝╚═╝  ╚═╝
                                                   
'''

LOCAL_HOST = "127.0.0.1"
STATUS_PRINT_INTERVAL = 5.0


class RIPv2_Router:

    def __init__(self, router_ID, inputs, outputs, timeout=90, garbage_time=60):
        self.router_ID = router_ID
        self.inputs = inputs # Input Ports
        self.outputs = outputs # Output Ports      

        # Timeout & Garbage to be done !
        self.timeout = timeout # in seconds
        self.garbage_time = garbage_time
        self.timeout_timer = {} # Dict
        self.garbage_time = {} # Dict


        # Create input sockets
        self.sockets = self.create_sockets()

        self.routing_table = RoutingTable(timeout=90, garbage=60)

        # Setup to send periodic updates
        self.periodic_updates = None
        neigh_map = {
            int(link[2]): int(link[1])
            for link in self.outputs
        }
        self.packet_manager = Packet(self.routing_table,
                                     self.router_ID,
                                     neigh_map,
                                     self.sockets)

        
        for port_s, metric_s, neigh_id_s in self.outputs:
            neigh_id = int(neigh_id_s)
            cost     = int(metric_s)

            self.routing_table.add_or_update(neigh_id,
                                            neigh_id,
                                            cost)
            
        print("Router Daemon Initialised...\n")
        print(f"Router: {self.router_ID}\n")
        print(f"Inputs: {self.inputs}\n")
        print(f"Outputs: {self.outputs}\n")


        # Show the table
        self.routing_table.print_table()

        self.init_periodic_update() 


        self._status_timer = None 
        self._start_status_timer()


    def _start_status_timer(self):
        """Starts the periodic timer for printing the routing table status."""
        # Ensure any existing timer is cancelled before starting a new one
        if self._status_timer:
            self._status_timer.cancel()

        self._status_timer = Timer(STATUS_PRINT_INTERVAL, self._print_status)
        self._status_timer.daemon = True # Allow program to exit even if this timer is running
        self._status_timer.start()

    def _print_status(self):
        """Callback function for the status timer - prints the table and reschedules."""
        print("\n--- Periodic Status Update ---") # periodically prints an update
        self.routing_table.print_table()
        print("------------------------------\n")

        # Reschedule the timer to run again
        self._start_status_timer()



    def receive_packet(self, data):
        # when a packet is received
        self.packet_manager.receive_and_process_packet(data)
        self.routing_table.prune()
        self.routing_table.print_table()



    def create_sockets(self): 
        '''
            We initialise the socket so that we can receive packets        
        '''
        sockets_list = {} 

        try:
            for port in self.inputs:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setblocking(False) # make it non blocking
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
                all the neighbour routers and refreshes direct routes
            '''

            self.routing_table.prune()  # Prune dead entries before sending
            self.update_neighbours() # This sends updates based on the *current* table state
            print("Update packet Sent")

            periodic_interval = 30 # Base interval
            plus_minus = random.uniform(-5, 5) # Random offset -5 - 5s
            self.periodic_updates = Timer(periodic_interval + plus_minus, send_update)
            self.periodic_updates.daemon = True # make sure timer doesnt stop exit
            self.periodic_updates.start()

        send_update()
    

    ######################## Testing 
    def update_neighbours(self):
        """
        Send a RIP response to each neighbour. We:
        1) build one or more packets for neighbour
        2) find the correct output port
        3) pick a output socket
        4) send each packet.
        """
        for neigh_id, link_metric in self.packet_manager.neighbours.items():
            # 1
            packets = self.packet_manager.create_response_packets(neigh_id)
            if not packets:
                print(f"[ERROR] No entries to send to Router {neigh_id}")
                continue

            # 2
            try:
                out_port = next(
                    int(entry[0])
                    for entry in self.outputs
                    if int(entry[2]) == neigh_id
                )
            except StopIteration:
                print(f"[ERROR] No matching output port for neighbour {neigh_id}")
                continue

            # 3
            send_sock = self.sockets[self.inputs[0]]

            # 4
            for pkt in packets:
                try:
                    send_sock.sendto(pkt, (LOCAL_HOST, out_port))
                    print(f"[Sent]  {len(pkt)} bytes to Router {neigh_id} "
                        f"on port {out_port}")
                except Exception as e:
                    print(f"[ERROR] Sending to {neigh_id}@{out_port}: {e}")


    def monitor_RT(self): 
        '''
            This is an infinite loop where we will listen for updates in the sockets and process updates
            and send out updates to other routers.
        '''

        while True: 
            readable, _, _ = select.select(list(self.sockets.values()), [], [], 1.0)
            

            if readable:    
                for sock in readable:
                    try:
                        data, addr = sock.recvfrom(4096)


                        local_port = sock.getsockname()[1]
                    

                        self.packet_manager.receive_and_process_packet(data)
                        

                        self.routing_table.prune()

                        self.routing_table.print_table()
                        

                    except Exception as e:
                        print(f"[Error] receiving data: {e}")






