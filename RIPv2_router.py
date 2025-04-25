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
# PERIODIC_UPDATES = None


class RIPv2_Router:

    def __init__(self, router_ID, inputs, outputs, timeout=90, garbage_time=60):
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
        self.routing_table = RoutingTable(timeout=90, garbage=60)

        # self.routing_table = RT_entry(self.router_ID)

        # self.routing_table = RT_entry(self.router_ID, metric)

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
        
        # for link in self.outputs:           # e.g. ['6110','1','1']
        #     port, metric_s, neigh_id_s = link
        #     neigh_id = int(neigh_id_s)
        #     cost     = int(metric_s)
        #     # directly connected → next_hop is the neighbour itself
        #     self.routing_table.add_or_update(neigh_id, neigh_id, cost)


        
        print("Seeding directly‐connected neighbours into routing table:")
        for port_s, metric_s, neigh_id_s in self.outputs:
            neigh_id = int(neigh_id_s)
            cost     = int(metric_s)
            print(f"  • dst={neigh_id}, next_hop={neigh_id}, metric={cost}")
            # use the same method you defined in RoutingTable.py:
            # it’s called add_or_update(...)
            self.routing_table.add_or_update(neigh_id,
                                            neigh_id,
                                            cost)
            
        print("Router Daemon Initialised...\n")
        print(f"Router: {self.router_ID}\n")
        print(f"Inputs: {self.inputs}\n")
        print(f"Outputs: {self.outputs}\n")


        # Show the table immediately:
        self.routing_table.print_table()

        self.periodic_updates = None 
        self.init_periodic_update() 

        # You might have a duplicate call to init_periodic_update() here - REMOVE IT if present
        # self.init_periodic_update() # <--- REMOVE THIS DUPLICATE CALL if you have it
        # --- ADD THIS BLOCK AFTER THE ABOVE init_periodic_update() CALL ---
        # Setup Periodic Status Printing Timer
        self._status_timer = None 
        self._start_status_timer()

########################
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
        print("\n--- Periodic Status Update ---") # Add a marker for periodic prints
        self.routing_table.print_table()
        print("------------------------------\n")

        # Reschedule the timer to run again
        self._start_status_timer()

########################


    def receive_packet(self, data):
        # upon arrival:
        self.packet_manager.receive_and_process_packet(data)
        # prune any fully garbage‐collected routes
        self.routing_table.prune()
        self.routing_table.print_table()



    def create_sockets(self): # Completed 
        '''
            We initialise the socket so that we can receive packets        
        '''
        sockets_list = {} #

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
            # --- ADD THIS LOGIC: Refresh Direct Routes ---
            # Ensure direct connections are always in the table with correct metric
            print("[INFO] Refreshing direct routes...")
            for port_s, metric_s, neigh_id_s in self.outputs:
                 neigh_id = int(neigh_id_s)
                 cost     = int(metric_s)
                 # Calling add_or_update with the direct link info.
                 # This updates or re-adds the entry and resets its timer.
                 # The next hop for a direct route is the neighbour itself.
                 self.routing_table.add_or_update(neigh_id, neigh_id, cost)
            # Optional: Print table after refreshing direct routes to see them active
            # self.routing_table.print_table()
            # --- END NEW LOGIC ---

            self.routing_table.prune()  # Prune dead entries *before* sending
            self.update_neighbours() # This sends updates based on the *current* table state
            print("Update packet Sent")

            # Reschedule the next periodic update
            # Use the periodic time from config if available (e.g., Router 1 config has 10s)
            # Otherwise, use a default (e.g., 30s is common, you have 10 + random 0-5 now)
            # Let's use 10 + random 0-5 as you have it currently
            periodic_interval = 10 # Base interval
            plus_minus = random.uniform(0, 5) # Random offset 0-5s
            self.periodic_updates = Timer(periodic_interval + plus_minus, send_update)
            self.periodic_updates.daemon = True # Ensure timer doesn't prevent exit
            self.periodic_updates.start()


        # You are calling init_periodic_update twice in __init__
        # self.init_periodic_update() # <-- Remove this duplicate call
        # The first call below is sufficient
        periodic_interval = 10 # Base interval from R1 config
        plus_minus = random.uniform(0, 5) # Random offset 0-5s
        self.periodic_updates = Timer(periodic_interval + plus_minus, send_update)
        self.periodic_updates.daemon = True
        self.periodic_updates.start()

        # def send_update():
        #     '''
        #         calls helper function to send an update to 
        #         all the neighbour routers
        #     '''
        #     self.routing_table.prune()  # Prune dead entries 
        #     self.update_neighbours()
        #     print("Update packet Sent")
        #     self.init_periodic_update()

        # plus_minus = random.uniform(0, 5)  # offset by a small random time (+/- 0 to 5 seconds)
        # self.periodic_updates = Timer(10 + plus_minus, send_update) # Triggers to send an update every 30 seconds
        # self.periodic_updates.start() # This triggers the timer to start (which is the line above)
    

    ######################## Testing 
    def update_neighbours(self):
        """
        Send a RIP response to each neighbour. We:
        1) build one or more packets for that neighbour,
        2) find the correct output port,
        3) pick a source socket,
        4) send each packet.
        """
        for neigh_id, link_metric in self.packet_manager.neighbours.items():
            # 1) Build all response packets for this neighbour
            packets = self.packet_manager.create_response_packets(neigh_id)
            if not packets:
                print(f"[!] No entries to send to Router {neigh_id}")
                continue

            # 2) Lookup the destination port in self.outputs
            try:
                out_port = next(
                    int(entry[0])
                    for entry in self.outputs
                    if int(entry[2]) == neigh_id
                )
            except StopIteration:
                print(f"[ERROR] No matching output port for neighbour {neigh_id}")
                continue

            # 3) Choose a local socket to send from (e.g. the first input port)
            send_sock = self.sockets[self.inputs[0]]

            # 4) Transmit each packet
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
                        # print(f"[DEBUG] Got {len(data)} bytes from {addr} on local port {sock.getsockname()[1]}")

                        local_port = sock.getsockname()[1]
                        print(f"[Received] Got {len(data)} bytes on local port {local_port} from {addr}")


                        print(f"Received packet from {addr}\n")
                        self.packet_manager.receive_and_process_packet(data)
                        print("Routing Table Updated...\n")

                        self.routing_table.prune()

                        self.routing_table.print_table()
                        

                    except Exception as e:
                        print(f"Error receiving data: {e}")






