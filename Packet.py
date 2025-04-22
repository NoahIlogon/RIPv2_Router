import socket
import sys
import time


# RIP Contstants
LOCAL_HOST = "127.0.0.1"
PORT = 520
HDR_SIZE = 4
RT_SIZE = 20 # Routing table size

CMD_REQUEST = 1
CMD_RESPONSE = 2


INF = 16

class Packet:

    def __init__(self, table, router_ID, neighbors, socket): # outputs instead of neighbours
        self.routing_table = table
        self.router_ID = router_ID
        self.socket = socket
        self.neighbours = {}
        # self.routing_table = {}
        

    def create_packet(self, neighbour):
        """
        Create the request packet and send it to the server
        - Implemented correctly?
        - We should only be creating update packets and not request packets
        """
        from RoutingTable import RT_entry
        packets = []

        if len(self.routing_table) == 0:  # If no entry in table, only header will be sent over
            packet = bytearray() #Creates teh ByteArray
            packet.append(2)  # Command
            packet.append(2) # Version
            # packet.append((self.router_ID >> 8) & 0xFF)  # High byte
            # packet.append(self.router_ID & 0x00FF)  # Low byte
            packet.append(0)  # Reserved byte 1
            packet.append(0)  # Reserved byte 2
            packet.append(self.router_ID >> 8)
            packet.append(self.router_ID & 0x00FF)

                  
            # packets.append(packet)
            return packet


        for i in range(((len(self.routing_table) - 1) // 25) + 1):
        # Checks how many entries to add to the packet (max 25)
            num_entries = min(25, len(self.routing_table) - (i * 25))

            # Create a new packet with space for the header and entries
            packet_size = 4 + (num_entries * 20)  # 4 bytes for header + 20 bytes per entry
            #packet = bytearray(packet_size)  # Creates the ByteArray

            # Add the header (Command = 2, Version = 2, Router ID)
            packet = bytearray() # Creates the ByteArray
            packet.append(2) # Command field (2 = Response)
            packet.append(2) # Version field (2 = RIP v2)
            packet.append(self.router_ID >> 8) # Router ID - first byte
            packet.append(self.router_ID & 0x00FF) # Router ID - second byte

            cur_index = 4  # Start adding entries after the header

            for entry in self.routing_table[i * 25: (i * 25) + num_entries]:

                # # Add the Metric (4 bytes)
                # packet[cur_index:cur_index+4] = entry.metric.to_bytes(4)  # Convert metric to 4 bytes
                # cur_index += 4

                # Address Family Identifier (2 bytes)
                packet[cur_index] = 0
                packet[cur_index+1] = 2 # AFI = 0x0002 for IPv4
                # Route Tag (2 Bytes)
                packet[cur_index+2] = 0 # Must be zero
                packet[cur_index+3] = 0 # Must be zero

                cur_index+=4

                # Destination Router's IPv4 Address (4 bytes) / (entry. = entry / The current entry being looped)
                packet[cur_index] = entry.dst_id >> 24
                packet[cur_index+1] = 0xff & (entry.router_ID >> 16)
                packet[cur_index+2] = 0xffff & (entry.dst_id >> 8)
                packet[cur_index+3] = 0xffffff & entry.dst_id

                cur_index += 4

                # Subnet Mask (8 bytes), must be zero!!
                for i in range(8):
                    packet[cur_index+i] = 0

                cur_index += 8
                
                # Metric (4 bytes) / Path Cost.
                # if entry.next_hop == neighbour['router_id']:
                if hasattr(entry, 'next_hop') and entry.next_hop == neighbour['router_id']:
                    cost = INF
                else:
                    cost = entry.metric

                packet[cur_index] = cost >> 24
                packet[cur_index+1] = 0xff & (cost >> 16)
                packet[cur_index+2] = 0xffff & (cost >> 8)
                packet[cur_index+3] = 0xffffff & cost

                cur_index += 4


                packets.append(packet)  # Adds packet to the rest of the packets

        return packets




    
    def check_header(self, packet):
        """Checks if the RIP header is correct. If it is correct, it returns
        the ID of the router it recieved it from"""
        command = int(packet[0])
        version = int(packet[1])
        reserved = (packet[2], packet[3])  # Reserved bytes must be zero
        # router_ID = int(packet[4:6])
        router_ID = int.from_bytes(packet[4:6], byteorder='big')
        
        if command != 2:
            if command == 1:
                print("ERROR: Packet is a request packet!...")
            else:
                print("ERROR: Invalid Packet...\n"
                      "Packet must be either\n"
                      "1 - Request Packet\n"
                      "2 - Response Packet\n"
                      "Dropping Packet!...")
            return False
        
        if version != 2:
            print("ERROR: Invalid Version!...\n"
                  "Version must be 2..\n"
                  "Dropping Packet!...")
            return False
        
        if reserved != (0, 0):
            print(f"ERROR: Invalid Packet! Reserved bytes must be zero.\nCurrently Reserved = {reserved}\n"
            "Dropping Packet!...")
            return False
        if not router_ID or (1 > router_ID > 64000):
            print(f"ERROR: Invalid router ID! {router_ID} is out of valid range | Must be between 1-64000 inclusive..\n"
                  "Dropping Packet!...")
            return False

        return router_ID


    def check_entry(self, entry):
        """Checks the entry and insures that the entry and all of its components are valid
            - consider returning some values?
        """
        passed = True

        family_identifier_first = int(entry[0]) # First Byte
        family_identifier_second = int(entry[1]) # Second Byte
        family_identifier = (family_identifier_first, family_identifier_second) # Family Identifier
        if family_identifier != (0, 2): # Checks Family Identifier
            print("\nERROR: Invalid Address Family Identifier!") # "The address family identifier (AFI) for IPv4 is 0x0002."
            passed = False

        route_tag_first = int(entry[2]) # First Byte
        route_tag_second = int(entry[3]) # Second Byte
        route_tag = (route_tag_first, route_tag_second) # Route Tag
        if route_tag != (0, 0):
            print("\nERROR: Invalid Route Tag!") # "Route Tag – Used to distinguish routes learned from other routing protocols. 
                                               # The value is typically set to 0 for RIP routes."
            passed = False
            

        IPv4_addy_first = int(entry[4]) # First Byte
        IPv4_addy_second = int(entry[5]) # Second Byte
        IPv4_addy_third = int(entry[6]) # Third Byte
        IPv4_addy_forth = int(entry[7]) # Forth Byte
        IPv4_addy = (IPv4_addy_first, IPv4_addy_second, IPv4_addy_third, IPv4_addy_forth) # IPv4 Address
        for byte in IPv4_addy:
            if not (0 <= byte <= 255):  # Each byte must be between 0 and 255
                print(f"\nERROR: Invalid byte in IPv4 Address: {byte}! It must be between 0-255 inclusive.")
                passed = False

        subnet_mask_first = int(entry[8])  # First Byte of subnet mask
        subnet_mask_second = int(entry[9])  # Second Byte
        subnet_mask_third = int(entry[10])  # Third Byte
        subnet_mask_forth = int(entry[11])  # Fourth Byte
        subnet_mask = (subnet_mask_first, subnet_mask_second, subnet_mask_third, subnet_mask_forth)  # Subnet Mask

        if subnet_mask == (0,0,0,0):
            print("No subnet mask included")

        else:
            for byte in subnet_mask:
                if not (0 <= byte <= 255):  # Each byte of the subnet mask must be between 0 and 255
                    print(f"\nERROR: Invalid byte in Subnet Mask: {byte}! It must be between 0-255 inclusive.")
                    passed = False

        next_hop_first = int(entry[12])  # First Byte of next hop
        next_hop_second = int(entry[13])  # Second Byte
        next_hop_third = int(entry[14])  # Third Byte
        next_hop_forth = int(entry[15])  # Fourth Byte
        next_hop = (next_hop_first, next_hop_second, next_hop_third, next_hop_forth)  # Next hop IP address

        metric_first = int(entry[16])  # First byte of metric
        metric_second = int(entry[17])  # Second byte of metric
        metric_third = int(entry[18])  # Third byte of metric
        metric_fourth = int(entry[19])  # Fourth byte of metric
        received_metric = (metric_first << 24) + (metric_second << 16) + (metric_third << 8) + metric_fourth  # Combine the 4 bytes into a single metric
        
        if next_hop == (0,0,0,0):
            if received_metric == INF:
                print("ERROR: Next Hop is (0.0.0.0), indicating an unreachable destination. Metric is 16 (infinity).")
                passed = False
            else:
                print("Next Hop is (0.0.0.0), indicating a directly connected route. No further hop required.")
                # This is a valid case and the route is accepted as directly connected to the destination :)

        else:
            for byte in next_hop:
                if not (0 <= byte <= 255):  # Each byte of the next hop must be between 0 and 255
                    print(f"\nERROR: Invalid byte in Next Hop Address: {byte}! It must be between 0-255 inclusive.")
                    passed = False
                

        

        return passed



    def recieve_and_process_packet(self, packet):
        '''
            To implemet:
            - Update routing table 
            - Start/reset Garbage/ timer | add timer resets
            - If metric changes trigger an update
            - If metric is 16 then trigger garbage
            self.routing_table.update_entry(...)
            self.routing_table.mark_as_garbage(...)
        '''
        print("Packet Recieved Succesfully! \n"
        "Checking for Validity!...")
        packet_size = 0
        packet_len = len(packet)
        recieved_ID = self.check_header(packet)

        if not recieved_ID:
            print("[ERROR]: Packet Header Check Failed!...\n")
            return


        num_entries = (packet_len - 4) // RT_SIZE # RT_SIZE = 20

        for entry_index in range(num_entries): # Need to call the Routing table entries here
            if packet_size > 25:
                print("ERROR: Invalid packet length")
                return
            entry_start_index = 4 + entry_index * RT_SIZE # (Start of Example) 1. Start at 4 + 0 * 20 = 4 | 2. 4 + 1 * 20 = 24...
            entry_end_index = entry_start_index + RT_SIZE # 1. Then 4 + 20 = 24 | 2. 24 + 20 = 44...
            entry = packet[entry_start_index:entry_end_index] # 1. So 4-24 | 2. 24-44... | Checks every 20bytes (End of Example)
            # packet_size += 1

            # Validate the current entry
            if not self.check_entry(entry):
                # If entry invalid, log the error and drop the packet
                print(f"ERROR: Invalid or empty entry at index {entry_index} (starting at byte {entry_start_index}). \n"
                "Dropping Packet!...")
                return
            
            # Extract details from the entry 
            dest_id = int.from_bytes(entry[4:8], byteorder='big')
            next_hop = tuple(entry[12:16])
            metric = int.from_bytes(entry[16:20], byteorder='big')
            # print("[!] Checkpoint 1")

            #Compute updated metric
            cost = None
            for route in self.routing_table:
                if route.router_id == recieved_ID:
                    cost = route.metric
                    # print("[!] Checkpoint 2")
                    break

            if cost is None:
                # cost = 1
                for neighbor in self.neighbours:
                    if neighbor['Router-ID'] == recieved_ID:
                        cost = int(neighbor['metric']) 
                        # print("[!] Checkpoint 3")
                        break
                else:
                    cost = INF

            updated_metric = min(metric + cost, INF)

            if updated_metric == INF:
                self.routing_table.mark_garbage(dest_id)

            else:
                self.routing_table.add_or_update_entry(dest_id, recieved_ID, updated_metric)

        
        self.routing_table.print_table()
        self.routing_table.add_or_update_entry(dest_id, recieved_ID, updated_metric)
        self.routing_table.print_table()

            




