import socket
import sys
import time
from RoutingTable import RoutingTable


# Constants
LOCAL_HOST = "127.0.0.1"
PORT = 520
HDR_SIZE = 4
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
        # self.neighbours = {}
        # self.routing_table = {}
    ################################ Test
    # def create_response_packets(self, neighbour_id: int) -> list[bytes]:

    #     entries = list(self.routing_table)           # RTEntry instances
    #     if not entries:
    #         # header only
    #         hdr = bytearray(6)
    #         hdr[0] = CMD_RESPONSE
    #         hdr[1] = 2       #2
    #         hdr[2:4] = (0,0)
    #         hdr[4] = (self.router_ID >> 8) & 0xFF
    #         hdr[5] = self.router_ID & 0xFF
    #         return [bytes(hdr)]

    #     packets = []
    #     # chunk into ≤25 entries
    #     for i in range(0, len(entries), 25):
    #         chunk = entries[i:i+25]
    #         pkt = bytearray(4 + 20*len(chunk))
    #         # header
    #         pkt[0] = CMD_RESPONSE
    #         pkt[1] = 2
    #         pkt[2:4] = (0,0)
    #         # router ID
    #         pkt[4] = (self.router_ID >> 8) & 0xFF
    #         pkt[5] = self.router_ID & 0xFF

    #         base = 6
    #         for e in chunk:
    #             # AFI = 2
    #             pkt[base] = 0; pkt[base+1] = 2
    #             # route tag = 0
    #             pkt[base+2:base+4] = (0,0)
    #             # destination id (4 bytes big‐endian)
    #             dst = e.destination_id
    #             pkt[base+4:base+8] = dst.to_bytes(4, 'big')
    #             # subnet mask = 0.0.0.0 (4 bytes)
    #             pkt[base+8:base+12] = (0,0,0,0)
    #             # next hop = 0.0.0.0 (4 bytes)
    #             pkt[base+12:base+16] = (0,0,0,0)
    #             # metric
    #             m = INF if e.next_hop_id == neighbour_id else e.metric
    #             pkt[base+16:base+20] = m.to_bytes(4, 'big')

    #             base += 20

    #         packets.append(bytes(pkt))

        # return packets

     
     
    #################################
    def create_response_packets(self, neighbour_id: int) -> list[bytes]:
        """
        Create the request packet and send it to the server
        - Implemented correctly?
        - We should only be creating update packets and not request packets
        """

        # packets = []

        # if not(list(self.routing_table)):  # If no entry in table, only header will be sent over
        #     header = bytearray(6) #Creates teh ByteArray
        #     header.append(CMD_RESPONSE)  # Command
        #     header.append(2) # Version
        #     # packet.append((self.router_ID >> 8) & 0xFF)  # High byte
        #     # packet.append(self.router_ID & 0x00FF)  # Low byte
        #     header.append(0)  # Reserved byte 1
        #     header.append(0)  # Reserved byte 2
        #     header.append((self.router_ID >> 8) & 0xFF)
        #     header.append(self.router_ID & 0xFF)

        #     return [bytes(header)]


        # # for i in range(((len(self.routing_table) - 1) // 25) + 1):
        # for i in range(0, len(list(self.routing_table)), 25):
        # # Checks how many entries to add to the packet (max 25)
        #     num_entries = min(25, len(self.routing_table) - (i * 25))

        #     # Create a new packet with space for the header and entries
        #     packet_size = 6 + (num_entries * 20)  # 4 bytes for header + 20 bytes per entry
        #     packet = bytearray(packet_size)  # Creates the ByteArray

        #     # Add the header (Command = 2, Version = 2, Router ID)
        #     packet = bytearray() # Creates the ByteArray
        #     packet.append(CMD_RESPONSE) # Command field (2 = Response)
        #     packet.append(2) # Version field (2 = RIP v2)
        #     packet.append(0)  # Reserved byte 1
        #     packet.append(0)  # Reserved byte 2
        #     packet.append(self.router_ID >> 8) & 0xFF # Router ID - first byte
        #     packet.append(self.router_ID & 0xFF) # Router ID - second byte

        #     cur_index = 6  # Start adding entries after the header

        #     for entry in self.routing_table[i * 25: (i * 25) + num_entries]:

        #         # # Add the Metric (4 bytes)
        #         # packet[cur_index:cur_index+4] = entry.metric.to_bytes(6)  # Convert metric to 4 bytes
        #         # cur_index += 6

        #         # Address Family Identifier (2 bytes)
        #         packet[cur_index] = 0
        #         packet[cur_index+1] = 2 # AFI = 0x0002 for IPv4
        #         # Route Tag (2 Bytes)
        #         packet[cur_index+2] = 0 # Must be zero
        #         packet[cur_index+3] = 0 # Must be zero

        #         cur_index += 4

        #         # Destination Router's IPv4 Address (4 bytes) / (entry. = entry / The current entry being looped)
        #         packet[cur_index] = (entry.destination >> 24) & 0xFF
        #         packet[cur_index+1] = (entry.destination >> 16) & 0xFF
        #         packet[cur_index+2] = (entry.destination >> 8) & 0xFF
        #         packet[cur_index+3] = entry.destination & 0xFF

        #         cur_index += 4

        #         # Subnet Mask (8 bytes), must be zero!!
        #         for i in range(8):
        #             packet[cur_index+i] = 0

        #         cur_index += 8
                
        #         # Metric (4 bytes) / Path Cost.
        #         # # if entry.next_hop == neighbour['router_id']:
        #         if entry.next_hop == neighbour_id['Router-ID']:
        #             cost = INF
        #         else:
        #             entry.metric

        #         # if hasattr(entry, 'next_hop') and entry.next_hop == neighbour['router_id']:
        #         #     cost = INF
        #         # else:
        #         #     cost = entry.metric

        #         packet[cur_index] = (cost >> 24) & 0xFF
        #         packet[cur_index+1] = (cost >> 16) & 0xFF
        #         packet[cur_index+2] = (cost >> 8) & 0xFF
        #         packet[cur_index+3] = cost & 0xFF

        #         cur_index += 4


        #     packets.append(bytes(packet))  # Adds packet to the rest of the packets

        # return packets

        entries = list(self.routing_table)  # snapshot of RTEntry objects
        packets = []

        # If we have no entries at all, send a header‐only packet
        if not entries:
            hdr = bytearray(6)
            hdr[0] = CMD_RESPONSE          # Command = 2 (Response)
            hdr[1] = 2                     # Version = 2
            hdr[2] = 0                     # Reserved
            hdr[3] = 0                     # Reserved
            hdr[4] = (self.router_ID >> 8) & 0xFF
            hdr[5] =  self.router_ID       & 0xFF
            return [bytes(hdr)]

        # Otherwise, chunk into ≤25 entries per packet
        for i in range(0, len(entries), 25):
            chunk = entries[i : i + 25]
            pkt_len = 6 + 20 * len(chunk)
            pkt = bytearray(pkt_len)

            # --- HEADER (6 bytes) ---
            pkt[0] = CMD_RESPONSE          # 0: command
            pkt[1] = 2                     # 1: version
            pkt[2] = 0                     # 2: reserved
            pkt[3] = 0                     # 3: reserved
            pkt[4] = (self.router_ID >> 8) & 0xFF
            pkt[5] =  self.router_ID       & 0xFF

            # --- ENTRIES (20 bytes each) ---
            offset = 6
            for e in chunk:
                #  0–1: AFI = 0x0002
                pkt[offset + 0] = 0
                pkt[offset + 1] = 2

                #  2–3: Route tag = 0
                pkt[offset + 2] = 0
                pkt[offset + 3] = 0

                #  4–7: Destination ID (32‑bit big‑endian)
                dst = e.destination_id
                pkt[offset + 4] = (dst >> 24) & 0xFF
                pkt[offset + 5] = (dst >> 16) & 0xFF
                pkt[offset + 6] = (dst >>  8) & 0xFF
                pkt[offset + 7] =  dst        & 0xFF

                # 8–11: Subnet mask = 0.0.0.0
                pkt[offset +  8 : offset + 12] = bytes((0, 0, 0, 0))

                # 12–15: Next hop = 0.0.0.0
                pkt[offset + 12 : offset + 16] = bytes((0, 0, 0, 0))

                # 16–19: Metric, with split‐horizon (poison reverse)
                # If this route’s next_hop == neighbour_id → advertise metric = INF
                metric = INF if e.next_hop_id == neighbour_id else e.metric
                pkt[offset + 16] = (metric >> 24) & 0xFF
                pkt[offset + 17] = (metric >> 16) & 0xFF
                pkt[offset + 18] = (metric >>  8) & 0xFF
                pkt[offset + 19] =  metric        & 0xFF

                offset += 20

            packets.append(bytes(pkt))

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

        if len(entry) != 20:
            print(f"[ERROR] Bad entry length: {len(entry)} != 20")
            return False

        # 1) AFI (bytes 0–1) must equal 0x0002
        if entry[0] != 0 or entry[1] != 2:
            print(f"[ERROR] Bad AFI: {entry[0]:02x}{entry[1]:02x}")
            return False

        # 2) Route tag (bytes 2–3) must be zero
        if entry[2] != 0 or entry[3] != 0:
            print(f"[ERROR] Non‑zero route tag: {entry[2:4]}")
            return False

        # 3) Destination ID (bytes 4–7)
        dst = int.from_bytes(entry[4:8], "big")
        if not (0 <= dst <= 0xFFFFFFFF):
            print(f"[ERROR] Bad destination ID: {dst}")
            return False

        # 4) Subnet mask (bytes 8–11) must be a valid mask, 
        # here we accept 0.0.0.0 up to 255.255.255.255
        mask_bytes = entry[8:12]
        if any(b < 0 or b > 255 for b in mask_bytes):
            print(f"[ERROR] Bad subnet mask bytes: {tuple(mask_bytes)}")
            return False
        # (optional) you can check that mask is contiguous ones then zeros

        # 5) Next hop (bytes 12–15)
        nh_bytes = entry[12:16]
        if any(b < 0 or b > 255 for b in nh_bytes):
            print(f"[ERROR] Bad next‑hop bytes: {tuple(nh_bytes)}")
            return False

        # 6) Metric (bytes 16–19) must be in [1..16]
        metric = int.from_bytes(entry[16:20], "big")
        if not (1 <= metric <= INF):
            print(f"[ERROR] Bad metric: {metric} (must be 1..{INF})")
            return False

        # All checks passed
        return True

        # passed = True

        # family_identifier_first = int(entry[0]) # First Byte
        # family_identifier_second = int(entry[1]) # Second Byte
        # family_identifier = (family_identifier_first, family_identifier_second) # Family Identifier
        # if family_identifier != (0, 2): # Checks Family Identifier
        #     print("\nERROR: Invalid Address Family Identifier!") # "The address family identifier (AFI) for IPv4 is 0x0002."
        #     passed = False

        # route_tag_first = int(entry[2]) # First Byte
        # route_tag_second = int(entry[3]) # Second Byte
        # route_tag = (route_tag_first, route_tag_second) # Route Tag
        # if route_tag != (0, 0):
        #     print("\nERROR: Invalid Route Tag!") # "Route Tag – Used to distinguish routes learned from other routing protocols. 
        #                                        # The value is typically set to 0 for RIP routes."
        #     passed = False
            

        # IPv4_addy_first = int(entry[4]) # First Byte
        # IPv4_addy_second = int(entry[5]) # Second Byte
        # IPv4_addy_third = int(entry[6]) # Third Byte
        # IPv4_addy_forth = int(entry[7]) # Forth Byte
        # IPv4_addy = (IPv4_addy_first, IPv4_addy_second, IPv4_addy_third, IPv4_addy_forth) # IPv4 Address
        # for byte in IPv4_addy:
        #     if not (0 <= byte <= 255):  # Each byte must be between 0 and 255
        #         print(f"\nERROR: Invalid byte in IPv4 Address: {byte}! It must be between 0-255 inclusive.")
        #         passed = False

        # subnet_mask_first = int(entry[8])  # First Byte of subnet mask
        # subnet_mask_second = int(entry[9])  # Second Byte
        # subnet_mask_third = int(entry[10])  # Third Byte
        # subnet_mask_forth = int(entry[11])  # Fourth Byte
        # subnet_mask = (subnet_mask_first, subnet_mask_second, subnet_mask_third, subnet_mask_forth)  # Subnet Mask

        # # if subnet_mask == (0,0,0,0):
        # #     print("No subnet mask included")

        # # else:
        # #     for byte in subnet_mask:
        # #         if not (0 <= byte <= 255):  # Each byte of the subnet mask must be between 0 and 255
        # #             print(f"\nERROR: Invalid byte in Subnet Mask: {byte}! It must be between 0-255 inclusive.")
        # #             passed = False

        # next_hop_first = int(entry[12])  # First Byte of next hop
        # next_hop_second = int(entry[13])  # Second Byte
        # next_hop_third = int(entry[14])  # Third Byte
        # next_hop_forth = int(entry[15])  # Fourth Byte
        # next_hop = (next_hop_first, next_hop_second, next_hop_third, next_hop_forth)  # Next hop IP address

        # metric_first = int(entry[16])  # First byte of metric
        # metric_second = int(entry[17])  # Second byte of metric
        # metric_third = int(entry[18])  # Third byte of metric
        # metric_fourth = int(entry[19])  # Fourth byte of metric
        # received_metric = (metric_first << 24) + (metric_second << 16) + (metric_third << 8) + metric_fourth  # Combine the 4 bytes into a single metric
        
        # # if next_hop == (0,0,0,0):
        # #     if received_metric == INF:
        # #         print("ERROR: Next Hop is (0.0.0.0), indicating an unreachable destination. Metric is 16 (infinity).")
        # #         passed = False
        # #     else:
        # #         print("Next Hop is (0.0.0.0), indicating a directly connected route. No further hop required.")
        # #         # This is a valid case and the route is accepted as directly connected to the destination :)

        # # else:
        # #     for byte in next_hop:
        # #         if not (0 <= byte <= 255):  # Each byte of the next hop must be between 0 and 255
        # #             print(f"\nERROR: Invalid byte in Next Hop Address: {byte}! It must be between 0-255 inclusive.")
        # #             passed = False
        # return passed



    def receive_and_process_packet(self, packet: bytes):
        print("Packet Received Successfully!\nChecking for Validity…")

        # 1) Header
        received_ID = self.check_header(packet)
        if not received_ID:
            print("[ERROR] Packet Header Check Failed!")
            return

        # 2) How many 20‐byte entries?
        num_entries = (len(packet) - 6) // RT_SIZE

        for idx in range(num_entries):
            start = 6 + idx * RT_SIZE
            end   = start + RT_SIZE
            entry = packet[start:end]

            # 2a) Validate
            if not self.check_entry(entry):
                print(f"[ERROR] Bad entry #{idx} (bytes {start}–{end}); dropping packet.")
                return

            # 2b) Parse fields
            dest_id = int.from_bytes(entry[4:8], 'big')
            metric  = int.from_bytes(entry[16:20], 'big')

            # 3) Find cost to the sender (received_ID) in our RT
            cost = None
            for route in self.routing_table:
                if route.destination_id == received_ID:
                    cost = route.metric
                    break

            # 3a) Fallback: cost = link‐metric from self.neighbours
            if cost is None:
                cost = self.neighbours.get(received_ID, INF)

            # 4) New metric = recv_metric + link_cost (cap at INF)
            new_metric = min(metric + cost, INF)

            # 5) Apply split‐horizon: if next_hop == received_ID, poison
            #    (your create_response already handles that; here we just update)
            if new_metric >= INF:
                self.routing_table.mark_unreachable(dest_id)
            else:
                self.routing_table.add_or_update(dest_id,
                                                received_ID,
                                                new_metric)

        # Optionally: prune dead entries and/or trigger triggered update
        self.routing_table.prune()

            # #Compute updated metric
            # cost = None
            # for route in self.routing_table:
            #     if route.router_id == recieved_ID:
            #         cost = route.metric
            #         # print("[!] Checkpoint 2")
            #         break

            # if cost is None:
            #     # cost = 1
            #     for neighbor in self.neighbours:
            #         if neighbor['Router-ID'] == recieved_ID:
            #             cost = int(neighbor['metric']) 
            #             # print("[!] Checkpoint 3")
            #             break
            #     else:
            #         cost = INF

            # updated_metric = min(metric + cost, INF)

            # if updated_metric == INF:
            #     self.routing_table.mark_garbage(dest_id)

            # else:
            #     self.routing_table.add_or_update_entry(dest_id, recieved_ID, updated_metric)
    
