# COSC364 RIPv2 Project
### Aljaž Smrekar & Noah Ilogon
### Date: 18/2/25

## Important Notes:
- MAX 15 Hops

# Exectuting the Daemon
=======================
python3 router.py >config_file<
=======================


### https://datatracker.ietf.org/doc/html/rfc2453#section-4

## Steps to Succeed

Overview of RIP

RIP is a distance-vector routing protocol, and it’s used by routers to exchange information about network reachability within an Autonomous System (AS). It uses hop count as its metric, meaning the cost to reach a destination is represented by the number of routers (hops) between the source and the destination.
Key Concepts:

    RIP Metrics:
        The metric represents the "cost" of reaching a particular destination. It’s an integer between 1 and 15.
        A metric of 16 means the destination is unreachable.
        The metric for directly-connected networks (networks that a router is directly attached to) is typically 1.

    Routing Table:
        Each router using RIP maintains a routing table, which stores information about reachable destinations. Each entry typically includes:
            The IPv4 address of the destination.
            The metric (cost to reach the destination).
            The next hop (the next router in the path to the destination).
            Various timers (such as timeout and garbage collection timers).
            A route change flag to track when routes have changed.

    Routing Protocol Messages:
        RIP messages are exchanged via UDP on port 520. There are two types of RIP messages:
            Request: A router sends a request to ask for routing table updates.
            Response: A router sends a response, either as a direct reply to a request or as an unsolicited update to inform neighbors of changes in the routing table.
        Each RIP message contains one or more RIP entries (each representing a reachable destination).

    Message Structure:
        Command: Specifies whether the message is a request (1) or response (2).
        Version: Specifies which version of RIP is used (RIP version 2 in your case).
        RIP Entry: Each entry includes the following fields:
            Address Family Identifier (AFI): Type of address (IPv4, in this case, is AF_INET with the value 2).
            Destination Address: The IPv4 address of the destination.
            Metric: The cost of reaching the destination (1-15).
            Subnet Mask: Used in RIP version 2 to allow for more flexible routing and supporting variable-length subnet masks (VLSM).

    Unsolicited Updates:
        RIP routers periodically send unsolicited updates to inform neighbors of any changes in their routing table, even if no request was made. This helps ensure that the routing tables are kept up-to-date.

    Timers in RIP:
        Update Timer: Determines how often a router sends out its routing updates. Typically, the default is 30 seconds.
        Invalid Timer: When a route hasn't been updated for 180 seconds, it is considered invalid.
        Hold-down Timer: Prevents a router from receiving route updates that could be incorrect due to recent network changes.
        Garbage Collection Timer: After a route becomes invalid, it is eventually removed after a period (usually 120 seconds).

Details on Routing Table Entries (RTE):

The routing table entries have the following structure:

    Address Family Identifier (AFI): A short 2-byte identifier for the address type. For IPv4, this is always 2.
    IPv4 Address: The destination network address.
    Metric: The cost to reach the destination network. If a metric is 16, the destination is unreachable.

Steps for Implementing RIP in Your Router

When implementing RIP, your router should:

    Read Configuration:
        Read the configuration file (such as Router1.txt) to get information about input ports (for receiving routing packets) and output ports (to send updates to neighbors).

    Create Sockets:
        Create UDP sockets bound to the specified input ports (which correspond to the ports on which your router expects to receive RIP packets). These will be used to receive routing updates from peer routers.
        You can also create a socket for sending routing updates to neighbors. Typically, this is done by using port 520 or another valid UDP port.

    Routing Table Update:
        When a RIP packet is received, update the routing table based on the received routing information. This includes adjusting the metrics of the routes, adding new routes, or removing obsolete routes.

    Sending Routing Updates:
        Periodically send updates (unsolicited updates) to neighbors to notify them of any changes to your routing table. This helps ensure consistency across all routers.

    Timers and Garbage Collection:
        Implement timers for holding down, invalidating, and garbage collecting routes that are no longer valid.

    Event Loop:
        Continuously listen for events (routing updates or timer expirations) and process them as needed.

### 1. Design the Overall Structure
The program consists of multiple independent RIP daemon processes that:

Read a configuration file.
Open UDP sockets on specified input ports.
Send and receive RIP packets.
Maintain a routing table that updates dynamically.
Implement split-horizon with poisoned reverse.
Handle timers for periodic updates and route invalidation.
### 2. Configuration File Parsing
The configuration file contains:

router-id <int> → Unique router identifier.
input-ports <int, int, ...> → Ports this daemon listens on.
outputs <port-metric-id, port-metric-id, ...> → Connections to neighbors.
I'll write a parser that:

Reads this file.
Stores the values in a dictionary or class.
Example config:

yaml
Copy
Edit
router-id 1
input-ports 5001, 5002
outputs 6001-1-2, 6002-2-3
### 3. Setting Up Sockets
Open a UDP socket for each input port.
Bind sockets to 127.0.0.1:port.
Use select() for non-blocking event handling.
### 4. Implementing the RIP Protocol
Each daemon should:

Build a routing table from received updates.
Send periodic updates to neighbors.
Implement split-horizon with poisoned reverse (do not send back a route received from a neighbor).
Expire routes after a timeout if no updates are received.
Packet Format:

Version = 2
Command = 2 (Response)
Router ID stored in the "zero" field.
Each route entry contains:
Router ID
Metric (1-16)
Next Hop Router ID
I'll represent packets as byte arrays for UDP transmission.

### 5. Event Loop for Handling Packets & Timers
Use select.select() to handle incoming packets without blocking.
Maintain a timer for periodic updates and route expiry.
Use randomized update intervals to avoid synchronization issues.
### 6. Testing & Debugging
Write multiple config files.
Run multiple processes.
Check if routing tables converge correctly.
Simulate failures by killing a process and restarting it.
### 7. Documentation & Report
Explain design choices.
Provide example configs.
Document test cases and expected outcomes.
This is my rough plan. Which part do you need help with first?




### MORE

Steps to Implement:
Parse the Configuration File (Extract router ID, input ports, and outputs)
Create and Bind UDP Sockets (For input ports)
Implement the Routing Table (Store known routes and update based on RIPv2 rules)
Handle Incoming RIP Packets (Using select() for event-driven processing)
Send Periodic and Triggered Updates (With split-horizon and poisoned reverse)
Monitor Route Timeouts (Remove unreachable routes)