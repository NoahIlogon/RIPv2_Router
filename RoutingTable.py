'''
Author: Noah & Aljaž
Filename: RoutingTable.py
'''
from socket import *
import select
#############
from _Timer import * # Create this class
# from RoutingTable import RT_entry # To be implemented
from Packet import *
from threading import Timer

ROUTE_CHANGE_FLAG = False #A flag to indicate that information about the route has changed recently
GARBAGE_CHANGE_FLAG = False
TIMEOUT = False
GARBAGE_TIME = False
INF = 16 # Unreachable


class RT_entry:
    '''
        ██████╗  ██████╗ ██╗   ██╗████████╗██╗███╗   ██╗ ██████╗     ████████╗ █████╗ ██████╗ ██╗     ███████╗    
        ██╔══██╗██╔═══██╗██║   ██║╚══██╔══╝██║████╗  ██║██╔════╝     ╚══██╔══╝██╔══██╗██╔══██╗██║     ██╔════╝    
        ██████╔╝██║   ██║██║   ██║   ██║   ██║██╔██╗ ██║██║  ███╗       ██║   ███████║██████╔╝██║     █████╗      
        ██╔══██╗██║   ██║██║   ██║   ██║   ██║██║╚██╗██║██║   ██║       ██║   ██╔══██║██╔══██╗██║     ██╔══╝      
        ██║  ██║╚██████╔╝╚██████╔╝   ██║   ██║██║ ╚████║╚██████╔╝       ██║   ██║  ██║██████╔╝███████╗███████╗    
        ╚═╝  ╚═╝ ╚═════╝  ╚═════╝    ╚═╝   ╚═╝╚═╝  ╚═══╝ ╚═════╝        ╚═╝   ╚═╝  ╚═╝╚═════╝ ╚══════╝╚══════╝                                                                                                         
    We will:
    - store/update routing table
    - track timers per route
    - handle route expiry and elimination
    - Printing routing table

    '''


    def __init__(self, destination, next_hop, metric, timeout=30, garbage=30):
        self.destination = destination
        self.next_hop = next_hop
        self.changed = False 
        self.in_garbage = False
        self.metric = metric
        

        self.timeout_timer = Timer(timeout)
        self.garbage_timer = Timer(garbage)


    def reset_timeout(self):
        self.timeout_timer.start_timer()
        self.in_garbage = False

    def set_garbage_timer(self):
        self.garbage_timer.start_timer()
        self.in_garbage = True


    def handle_timeout(self):
        """Handles timeout event if it occurs"""

        print(f"Router {self.router_id} has timed out. Starting garbage collection.")
        self.metric = 16  # Set route as unreachable / INF
        self.set_garbage_timer()

    def handle_garbage(self, destination):
        """Handle garbage collection event if it occurs"""
        if destination in self.entries:
            print(f"Router {destination} has been deleted from the routing table due to garbage collection.")
            del self.entries[destination]
        
        
        # if destination in self.entries:
        #     print(f"Router {destination} has been deleted from the routing table due to garbage collection.")
        #     del self.entries[destination]


    def add_or_update_entry(self, destination, next_hop, metric):
        if destination not in self.entries:
            self.entries[destination] = RT_entry(destination, next_hop, metric)
        else:
            entry = self.entries[destination]
            entry.next_hop = next_hop
            entry.metric = metric
            entry.timeout_timer.start_timer()
            entry.in_garbage = False


    def generate_info(self, ID_list,):
        # Returns the routign table with the custom syntax
        return f"Destination: {self.IPv4_addy} | Next Hop: {self.next_hop} | Metric: {self.metric} | Changed: {ROUTE_CHANGE_FLAG} | Garbage: {GARBAGE_CHANGE_FLAG}"
    
    def print_table(self):
        '''
            This will print the current routing table of the router
        '''
        print("\n")
        print(f"________________Router: {self.router_id}________________")
        print("_________________________________________________________")
        print("| Router ID | Next Hop | Cost | Timeout | Garbage Timer |")
        print("|===========|==========|======|=========|===============|")

        for entry in self.entries.values():
            timeout = f"{int(entry.timeout_timer.update - time.time())}" if entry.timeout_timer.active else "N/A"
            garbage = f"{int(entry.garbage_timer.update - time.time())}" if entry.in_garbage else "N/A"
            print(f"| Destination: {self.IPv4_addy} | Next Hop: {self.next_hop} | Metric: {self.metric} | Changed: {ROUTE_CHANGE_FLAG} | Garbage: {GARBAGE_CHANGE_FLAG} |")

        print("---------------------------------------------------------------\n")


    def mark_garbage(self, destination_id):
        ''' 
            Mark route as unreachable; starting a garbage collection timer
        '''
        if destination_id in self.entries:
            entry = self.entries[destination_id]
            entry.metric = INF
            entry.changed = True
            entry.in_garbage = True

            if not entry.garbage_timer.active:
                entry.garbage_timer = Timer(120, lambda: self.remove_entry(destination_id))
                entry.garbage_timer.start_timer()



    def remove_entry(self, destination_id):
        if destination_id in self.entries:
            del self.entries[destination_id] # Entry Deleted
            print(f"[!] Route to {destination_id} deleted")

###############################################################

# class RoutingTable:
#     '''
#         Stores all the objects and instances of RT_entry inside a 
#         Routing Table !!!
#     '''
#     def __init__(self, router_ID):
#         self.router_id = router_ID
#         self.entries = {}
class RoutingTable:
    def __init__(self):
        self.entries = {}  # destination_id -> RT_entry

    def __len__(self):
        return len(self.entries)
    
    def __iter__(self):
        return iter(self.entries.values())


    def add_or_update_entry(self, destination, next_hop, metric):
        if destination not in self.entries:
            self.entries[destination] = RT_entry(destination, None, next_hop, metric)
        else:
            entry = self.entries[destination]
            entry.next_hop = next_hop
            entry.metric = metric
            entry.reset_timeout()

    def mark_garbage(self, destination_id):
        if destination_id in self.entries:
            entry = self.entries[destination_id]
            entry.metric = 16
            entry.set_garbage_timer()

    def print_table(self):
        print("Current Routing Table:")
        for dest_id, entry in self.entries.items():
            print(f"→ Dest: {dest_id}, Next Hop: {entry.next_hop}, Metric: {entry.metric}")
