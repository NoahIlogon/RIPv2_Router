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
        
        for link in self.outputs:           # e.g. ['6110','1','1']
            port, metric_s, neigh_id_s = link
            neigh_id = int(neigh_id_s)
            cost     = int(metric_s)
            # directly connected → next_hop is the neighbour itself
            self.routing_table.add_or_update(neigh_id, neigh_id, cost)


        print("Router Daemon Initialised...\n")
        print(f"Router: {self.router_ID}\n")
        print(f"Inputs: {self.inputs}\n")
        print(f"Outputs: {self.outputs}\n")

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

        # Show the table immediately:
        self.routing_table.print_table()

        # now start periodic updates
        self.init_periodic_update()


        

        # self.packet_manager = Packet(self.routing_table,
        #                             self.router_ID,
        #                             self.outputs,
        #                             self.sockets)

        self.init_periodic_update() # periodic update loop is initialised

        
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
        self.periodic_updates = Timer(30 + plus_minus, send_update) # Triggers to send an update every 30 seconds
        self.periodic_updates.start() # This triggers the timer to start (which is the line above)
    

    # def update_neighbours(self):
    #     '''
    #         sends an update packet to all neighbours
    #     '''
    #     for link in self.outputs:  # EXAMPLE: link = ['5000', '1', '1']
    #         port = int(link[0])
    #         metric = int(link[1])
    #         neighbour_id = int(link[2])

    #         packet = self.packet_manager.create_packet({
    #             'router_id': neighbour_id,
    #             'metric': metric
    #         })

    #         if not packet:
    #             print(f"[!] No Packet created for Router: {neighbour_id}")

    #         try:
    #             send_to_socket = self.sockets[self.inputs[0]]
    #             send_to_socket.sendto(packet, (LOCAL_HOST, port))

    #         except Exception as e:
    #             print(f"[ERROR] Sending to Router: {neighbour_id} - Port: {port}\n {e}\n") 

    #         else:
    #             print(f"[SUCCESS] Packet sent to Router: {neighbour_id} - Port: {port}\n")
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
                    print(f"[→] Sent {len(pkt)} bytes to Router {neigh_id} "
                        f"on port {out_port}")
                except Exception as e:
                    print(f"[ERROR] Sending to {neigh_id}@{out_port}: {e}")



    ########################

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


    # def init_timer(self, dst_id):
    #     '''
    #         Timer is Initialised
    #     '''
        
    #     if dst_id in self.timeout_timer:
    #         self.timeout_timer[dst_id]
    

    ####################### Listen respond and listen to incoming packets



    def monitor_RT(self): 
        '''
            This is an infinite loop where we will listen for updates in the sockets and process updates
            and send out updates to other routers.
        '''

        while True: 
            readable, _, _ = select.select(list(self.sockets.values()), [], [], 1.0)
            
            # if readable:
            #     print(f"[DEBUG] {len(readable)} socket(s) ready: {list(self.sockets.keys())}")
            
            for sock in readable:
                try:
                    data, addr = sock.recvfrom(1024)
                    # print(f"[DEBUG] Got {len(data)} bytes from {addr} on local port {sock.getsockname()[1]}")

                    local_port = sock.getsockname()[1]
                    print(f"[RX] Got {len(data)} bytes on local port {local_port} from {addr}")


                    print(f"Received packet from {addr}\n")
                    self.packet_manager.receive_and_process_packet(data)
                    print("Routing Table Updated...\n")

                    self.routing_table.prune()

                    self.routing_table.print_table()
                    

                except Exception as e:
                    print(f"Error receiving data: {e}")






