import socket
import sys
import time
from RoutingTable import RoutingTable


# Constants
LOCAL_HOST = "127.0.0.1"
PORT = 520
HDR_SIZE = 6
RT_SIZE = 20 # Routing table size

CMD_REQUEST = 1
CMD_RESPONSE = 2


INF = 16


class Packet:

    def __init__(self, table, router_ID, neighbors: dict, sockets:dict): # outputs instead of neighbours
        self.routing_table = table
        self.router_ID = router_ID
        self.sockets = sockets
        self.neighbours = neighbors

 
    def create_response_packets(self, neighbour_id: int) -> list[bytes]: # Creates an Update packet
        """
        Create the update packet
        """
        
        packets = []
        entries = list(self.routing_table)  # instance of RT

        if not entries:
            header = bytearray(6)
            header[0] = CMD_RESPONSE
            header[1] = 2
            header[2:4] = (0, 0)
            header[4] = (self.router_ID >> 8) & 0xFF
            header[5] = self.router_ID & 0xFF
            
            return [bytes(header)]


        for i in range(0, len(entries), 25):
            # Remove entries destined for the neighbor
            entry_chunk = [
                entry for entry in entries[i:i + 25]
                if entry.destination_id != neighbour_id
            ]
            if not entry_chunk:
                continue  # Skip empty chunks

            packet = bytearray(6 + 20 * len(entry_chunk))

            # Header
            packet[0] = CMD_RESPONSE
            packet[1] = 2
            packet[2:4] = (0, 0)
            packet[4] = (self.router_ID >> 8) & 0xFF
            packet[5] = self.router_ID & 0xFF

            cur_index = 6
            for entry in entry_chunk:
                # AFI + Route Tag
                packet[cur_index] = 0
                packet[cur_index + 1] = 2
                packet[cur_index + 2] = 0
                packet[cur_index + 3] = 0
                cur_index += 4

                # Destination ID (4 bytes)
                packet[cur_index] = (entry.destination_id >> 24) & 0xFF
                packet[cur_index + 1] = (entry.destination_id >> 16) & 0xFF
                packet[cur_index + 2] = (entry.destination_id >> 8) & 0xFF
                packet[cur_index + 3] = entry.destination_id & 0xFF
                cur_index += 4

                # Subnet Mask (8 bytes = 0s)
                for j in range(8):
                    packet[cur_index + j] = 0
                cur_index += 8

                # print(f"[DEBUG] Sending route to {entry.destination_id} via {entry.next_hop_id} to neighbour {neighbour_id}")
                
                # Metric with poison reverse
                cost = INF if entry.next_hop_id == neighbour_id else entry.metric

                packet[cur_index] = (cost >> 24) & 0xFF
                packet[cur_index + 1] = (cost >> 16) & 0xFF
                packet[cur_index + 2] = (cost >> 8) & 0xFF
                packet[cur_index + 3] = cost & 0xFF
                cur_index += 4

            packets.append(bytes(packet))

        return packets

    
    def check_header(self, packet: bytes):
        """
            Checks if the RIP header is correct. If it is correct, returns
            the ID of the router it recieved it from
        """
        command = int(packet[0])
        version = int(packet[1])
        reserved = (packet[2], packet[3])  # Reserved bytes must be zero
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
            - returns passed
        """

        passed = True
        

        if len(entry) != 20:
            print(f"[ERROR] Bad entry length: {len(entry)} != 20")
            return False

        family_identifier_first = int(entry[0]) # First Byte
        family_identifier_second = int(entry[1]) # Second Byte
        family_identifier = (family_identifier_first, family_identifier_second) # Family Identifier
        if family_identifier != (0, 2): # Checks Family Identifier
            print("\n[ERROR] Invalid Address Family Identifier!") 
            passed = False
            return passed

        route_tag_first = int(entry[2]) # First Byte
        route_tag_second = int(entry[3]) # Second Byte
        route_tag = (route_tag_first, route_tag_second) # Route Tag
        if route_tag != (0, 0):
            print("\n[ERROR] Invalid Route Tag!") #  distinguish routes learned from other routing protocols. 
                                               
            passed = False
            return passed
            

        IPv4_addy_first = int(entry[4]) # First Byte
        IPv4_addy_second = int(entry[5]) # Second Byte
        IPv4_addy_third = int(entry[6]) # Third Byte
        IPv4_addy_forth = int(entry[7]) # Forth Byte
        IPv4_addy = (IPv4_addy_first, IPv4_addy_second, IPv4_addy_third, IPv4_addy_forth) # IPv4 Address
        addy = True
        for byte in IPv4_addy:
            if not (0 <= byte <= 0x255):  # Each byte must be between 0 and 255
                print(f"[ERROR] Invalid byte in IPv4 Address: {byte}!")
                passed = False
                addy = False

        if not addy:
            print(f"[ERROR] Invalid IPv4 Address: {IPv4_addy}!")
            return passed


        subnet_mask_first = int(entry[8])  # First Byte of subnet mask
        subnet_mask_second = int(entry[9])  # Second Byte
        subnet_mask_third = int(entry[10])  # Third Byte
        subnet_mask_forth = int(entry[11])  # Fourth Byte
        subnet_mask = (subnet_mask_first, subnet_mask_second, subnet_mask_third, subnet_mask_forth)  # Subnet Mask
        mask = True
        for byte in subnet_mask:
            if not (0 <= byte <= 255):  # Each byte must be between 0 and 255
                print(f"[ERROR] Invalid byte in Subnet Mask {byte}! It must be between 0-255 inclusive.")
                mask = False
                passed = False

        if not mask:
            print(f"[ERROR] Bad subnet mask bytes: {subnet_mask}")
            return passed

       

        next_hop_first = int(entry[12])  # First Byte of next hop
        next_hop_second = int(entry[13])  # Second Byte
        next_hop_third = int(entry[14])  # Third Byte
        next_hop_forth = int(entry[15])  # Fourth Byte
        next_hop = (next_hop_first, next_hop_second, next_hop_third, next_hop_forth)  # Next hop address
        hop = True
        for byte in next_hop:
            if not (0 <= byte <= 255):  # Each byte must be between 0 and 255
                print(f"ERROR: Invalid byte in Next Hop: {byte}! It must be between 0-255 inclusive.")
                hop = False
                passed = False

        if not hop:
            print(f"[ERROR] Bad subnet mask bytes: {next_hop}")
            return passed

        metric_first = int(entry[16])  # First byte 
        metric_second = int(entry[17])  # Second byte 
        metric_third = int(entry[18])  # Third byte 
        metric_fourth = int(entry[19])  # Fourth byte 
        received_metric = (metric_first << 24) + (metric_second << 16) + (metric_third << 8) + metric_fourth  # Combine the 4 bytes into a single metric

        if not (1 <= received_metric <= INF):
            print(f"[ERROR] Invalid metric: {received_metric} (must be between 1 - {INF})")
            passed = False
        return passed


    
    def receive_and_process_packet(self, packet: bytes):
        print("Packet Received Succesfully! \n"
        "Checking for Validity!...")

        received_ID = self.check_header(packet)
        if not received_ID:
            print("[ERROR] Packet Header Check Failed!\n")
            return # Drop the packet if header is invalid

        link_cost_to_sender = self.neighbours.get(received_ID)
        if link_cost_to_sender is None:
            print(f"[ERROR] Received update from non-neighbour {received_ID}. Ignoring packet.")
            return # Ignore updates from non-neighbours

        self.routing_table.reset_direct_neighbour_timer(received_ID)

        packet_len = len(packet)
        if packet_len < HDR_SIZE or (packet_len - HDR_SIZE) % RT_SIZE != 0:
            print(f"[ERROR] Invalid packet length: {packet_len}. Must be 6 + N * 20.")
            return

        num_entries = (packet_len - HDR_SIZE) // RT_SIZE

        # Process each route entry in packet
        for entry_index in range(num_entries):
            entry_start_index = HDR_SIZE + entry_index * RT_SIZE
            entry_end_index = entry_start_index + RT_SIZE
            entry_bytes = packet[entry_start_index:entry_end_index]

            if not self.check_entry(entry_bytes):
                # If entry invalid, log the error and skip this entry.
                print(f"[ERROR] Invalid entry at index {entry_index} (starting at byte {entry_start_index}). Skipping this entry.")
                continue # skip entry

            dest_id = int.from_bytes(entry_bytes[4:8], 'big')
            received_metric  = int.from_bytes(entry_bytes[16:20], 'big')

            if received_metric >= INF:
                new_metric = INF
            else:
                new_metric = min(received_metric + link_cost_to_sender, INF)

            if new_metric >= INF:
                self.routing_table.mark_unreachable(dest_id)

            else:
                # Otherwise, add or update the route through neighbour
                self.routing_table.add_or_update(dest_id, received_ID, new_metric)

        self.routing_table.prune() # remove dead entries

