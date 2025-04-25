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

 
    def create_response_packets(self, neighbour_id: int) -> list[bytes]:
        """
        Create the request packet and send it to the server
        - Implemented correctly?
        - We should only be creating update packets and not request packets
        """
        
        packets = []
        entries = list(self.routing_table)  # Snapshot of RT

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

                print(f"[DEBUG] Sending route to {entry.destination_id} via {entry.next_hop_id} to neighbour {neighbour_id}")
                
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

        # if len(entry) != 20:
        #     print(f"[ERROR] Bad entry length: {len(entry)} != 20")
        #     return False

        # # 1) AFI (bytes 0–1) must equal 0x0002
        # if entry[0] != 0 or entry[1] != 2:
        #     print(f"[ERROR] Bad AFI: {entry[0]:02x}{entry[1]:02x}")
        #     return False

        # # 2) Route tag (bytes 2–3) must be zero
        # if entry[2] != 0 or entry[3] != 0:
        #     print(f"[ERROR] Non‑zero route tag: {entry[2:4]}")
        #     return False

        # # 3) Destination ID (bytes 4–7)
        # dst = int.from_bytes(entry[4:8], "big")
        # if not (0 <= dst <= 0xFFFFFFFF):
        #     print(f"[ERROR] Bad destination ID: {dst}")
        #     return False

        # # 4) Subnet mask (bytes 8–11) must be a valid mask, 
        # # here we accept 0.0.0.0 up to 255.255.255.255
        # mask_bytes = entry[8:12]
        # if any(b < 0 or b > 255 for b in mask_bytes):
        #     print(f"[ERROR] Bad subnet mask bytes: {tuple(mask_bytes)}")
        #     return False
        # # (optional) you can check that mask is contiguous ones then zeros

        # # 5) Next hop (bytes 12–15)
        # nh_bytes = entry[12:16]
        # if any(b < 0 or b > 255 for b in nh_bytes):
        #     print(f"[ERROR] Bad next‑hop bytes: {tuple(nh_bytes)}")
        #     return False

        # # 6) Metric (bytes 16–19) must be in [1..16]
        # metric = int.from_bytes(entry[16:20], "big")
        # if not (1 <= metric <= INF):
        #     print(f"[ERROR] Bad metric: {metric} (must be 1..{INF})")
        #     return False
        
        # print("hehehhe")

        # # All checks passed
        # return True

        passed = True
        

        if len(entry) != 20:
            print(f"[ERROR] Bad entry length: {len(entry)} != 20")
            return False

        family_identifier_first = int(entry[0]) # First Byte
        family_identifier_second = int(entry[1]) # Second Byte
        family_identifier = (family_identifier_first, family_identifier_second) # Family Identifier
        if family_identifier != (0, 2): # Checks Family Identifier
            print("\n[ERROR] Invalid Address Family Identifier!") # "The address family identifier (AFI) for IPv4 is 0x0002."
            passed = False

        route_tag_first = int(entry[2]) # First Byte
        route_tag_second = int(entry[3]) # Second Byte
        route_tag = (route_tag_first, route_tag_second) # Route Tag
        if route_tag != (0, 0):
            print("\n[ERROR] Invalid Route Tag!") # "Route Tag – Used to distinguish routes learned from other routing protocols. 
                                               # The value is typically set to 0 for RIP routes."
            passed = False
            

        IPv4_addy_first = int(entry[4]) # First Byte
        IPv4_addy_second = int(entry[5]) # Second Byte
        IPv4_addy_third = int(entry[6]) # Third Byte
        IPv4_addy_forth = int(entry[7]) # Forth Byte
        IPv4_addy = (IPv4_addy_first, IPv4_addy_second, IPv4_addy_third, IPv4_addy_forth) # IPv4 Address
        addy = True
        for byte in IPv4_addy:
            if not (0 <= byte <= 0xFFFFFFFF):  # Each byte must be between 0 and 255
                print(f"[ERROR] Invalid byte in IPv4 Address: {byte}!")
                passed = False
                addy = False
        if not addy:
            print("\n-------------Destiantion ID-------------")
            print(f"[ERROR] Invalid IPv4 Address: {IPv4_addy}!")
            print("------------------------------------------")


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
            print("\n-------------Subnet Mask-------------")
            print(f"[ERROR] Bad subnet mask bytes: {subnet_mask}")
            print("---------------------------------------")

       

        next_hop_first = int(entry[12])  # First Byte of next hop
        next_hop_second = int(entry[13])  # Second Byte
        next_hop_third = int(entry[14])  # Third Byte
        next_hop_forth = int(entry[15])  # Fourth Byte
        next_hop = (next_hop_first, next_hop_second, next_hop_third, next_hop_forth)  # Next hop IP address
        hop = True
        for byte in next_hop:
            if not (0 <= byte <= 255):  # Each byte must be between 0 and 255
                print(f"ERROR: Invalid byte in Next Hop: {byte}! It must be between 0-255 inclusive.")
                hop = False
                passed = False
        if not hop:
            print("\n-------------Next Hop-------------")
            print(f"[ERROR] Bad subnet mask bytes: {next_hop}")
            print("-------------------------------------")

        metric_first = int(entry[16])  # First byte of metric
        metric_second = int(entry[17])  # Second byte of metric
        metric_third = int(entry[18])  # Third byte of metric
        metric_fourth = int(entry[19])  # Fourth byte of metric
        received_metric = (metric_first << 24) + (metric_second << 16) + (metric_third << 8) + metric_fourth  # Combine the 4 bytes into a single metric
        if not (1 <= received_metric <= INF):
            print(f"[ERROR] Invalid metric: {received_metric} (must be between 1 - {INF})")
            passed = False
        return passed


    # def receive_and_process_packet(self, packet: bytes):
        # print("Packet Recieved Succesfully! \n"
        # "Checking for Validity!...")
     
        # packet_size = 0
        # received_ID = self.check_header(packet)–
        #     print("[ERROR] Packet Header Check Failed!\n")
        #     return
        # print(f"[✓] Received update from Router {received_ID}")
        
        # # 2) How many 20‐byte entries?
        # num_entries = (len(packet) - 6) // RT_SIZE
        # print(f"[✓] Received update from Router {received_ID} with {num_entries} entries")
      
        # for entry_index in range(num_entries):
        #     if packet_size > 25:
        #         print("ERROR: Invalid packet length")
        #         return
        #     entry_start_index = 6 + entry_index * RT_SIZE # (Start of Example) 1. Start at 6 + 0 * 20 = 6 | 2. 6 + 1 * 20 = 26...
        #     entry_end_index = entry_start_index + RT_SIZE # 1. Then 6 + 20 = 26 | 2. 26 + 20 = 46...
        #     entry = packet[entry_start_index:entry_end_index] # 1. So 6-26 | 2. 26-46... | Checks every 20bytes (End of Example)
        #     packet_size += 1

        #     if not self.check_entry(entry):
        #         # If entry invalid, log the error and drop the packet
        #         print(f"ERROR: Invalid or empty entry at index {entry_index} (starting at byte {entry_start_index}). \n"
        #         "Dropping Packet!...")
        #         return

        #     # 2b) Parse fields
        #     dest_id = int.from_bytes(entry[4:8], 'big')
        #     metric  = int.from_bytes(entry[16:20], 'big')

        #     # 3) Find cost to the sender (received_ID) in our RT
        #     cost = None
        #     for route in self.routing_table:
        #         if route.destination_id == received_ID:
        #             cost = route.metric
        #             break

        #     # 3a) Fallback: cost = link‐metric from self.neighbours
        #     if cost is None:
        #         cost = self.neighbours.get(received_ID, INF)

        #     # 4) New metric = recv_metric + link_cost (cap at INF)
        #     new_metric = min(metric + cost, INF)

        #     # 5) Apply split‐horizon: if next_hop == received_ID, poison
        #     #    (your create_response already handles that; here we just update)
        #     entry_obj = None

        #     # Loop through routing table entries to find the destination
        #     for entry in self.routing_table:
        #         if entry.destination_id == dest_id:
        #             entry_obj = entry
        #             break

        #     # If we found the entry, reset its timeout
        #     if entry_obj:
        #         entry_obj.reset_timeout()

        #     # Now handle the metric update logic
        #     if new_metric >= INF:
        #         self.routing_table.mark_unreachable(dest_id)
        #     else:
        #         self.routing_table.add_or_update(dest_id, received_ID, new_metric)
            
        # print("[Success] Packet Check Passed.. \n")
        # # Optionally: prune dead entries and/or trigger triggered update
        # self.routing_table.prune()
    
    def receive_and_process_packet(self, packet: bytes):
        print("Packet Received Succesfully! \n"
        "Checking for Validity!...")

        received_ID = self.check_header(packet)
        if not received_ID:
            print("[ERROR] Packet Header Check Failed!\n")
            return # Drop the packet if header is invalid

        print(f"[✓] Received update from Router {received_ID}")

        # Ensure the sender is a direct neighbour
        # We need the link cost to the neighbour to add it to received metrics
        link_cost_to_sender = self.neighbours.get(received_ID)
        if link_cost_to_sender is None:
            print(f"[WARN] Received update from non-neighbour {received_ID}. Ignoring packet.")
            return # Ignore updates from non-neighbours

        # 2) How many 20‐byte entries?
        packet_len = len(packet)
        if packet_len < HDR_SIZE or (packet_len - HDR_SIZE) % RT_SIZE != 0:
            print(f"[ERROR] Invalid packet length: {packet_len}. Must be 6 + N * 20.")
            return

        num_entries = (packet_len - HDR_SIZE) // RT_SIZE
        print(f"[✓] Received update from Router {received_ID} with {num_entries} entries")

        # Process each route entry in the packet
        for entry_index in range(num_entries):
            entry_start_index = HDR_SIZE + entry_index * RT_SIZE
            entry_end_index = entry_start_index + RT_SIZE
            entry_bytes = packet[entry_start_index:entry_end_index]

            if not self.check_entry(entry_bytes):
                # If entry invalid, log the error and skip this entry.
                print(f"[ERROR] Invalid entry at index {entry_index} (starting at byte {entry_start_index}). Skipping this entry.")
                continue # Skip this invalid entry, continue with the next one

            # 2b) Parse fields from the entry
            dest_id = int.from_bytes(entry_bytes[4:8], 'big')
            received_metric  = int.from_bytes(entry_bytes[16:20], 'big')

            # 4) Calculate the new metric for *our* table: received_metric + link_cost_to_sender (cap at INF)
            # RIP adds the cost of the incoming interface (the link to the sender)
            # If the received metric is already INF, the new metric is also INF.
            if received_metric >= INF:
                new_metric = INF
            else:
                new_metric = min(received_metric + link_cost_to_sender, INF)

            # 5) Update the routing table based on the new metric and the source neighbour (received_ID)
            # The add_or_update method handles the timer reset logic correctly:
            # - Resets timer if the update is from the current next hop.
            # - Updates route and resets timer if a better path is found.
            # - Does nothing (but timer still ticks) if the received route is worse.
            #
            # If the new metric to the destination via this neighbour is INF, mark it unreachable.
            # This handles cases where a neighbour explicitly sends an INF metric or the calculated metric exceeds INF.
            if new_metric >= INF:
                self.routing_table.mark_unreachable(dest_id)
            else:
                # Otherwise, add or update the route through this neighbour
                self.routing_table.add_or_update(dest_id, received_ID, new_metric)


        print("Packet Check Passed!\n")
        # Prune dead entries whose garbage timers have expired after processing updates
        self.routing_table.prune()

        # Optional: Trigger a triggered update if there were significant changes to the routing table.
        # This is not strictly required by the core RIP timeout/garbage mechanism but is good practice.
        # self.update_neighbours() # Uncomment if you want triggered updates on receiving packets
