# RoutingTable.py

import time
import threading

INF = 16

'''
██████╗  ██████╗ ██╗   ██╗████████╗██╗███╗   ██╗ ██████╗     ████████╗ █████╗ ██████╗ ██╗     ███████╗
██╔══██╗██╔═══██╗██║   ██║╚══██╔══╝██║████╗  ██║██╔════╝     ╚══██╔══╝██╔══██╗██╔══██╗██║     ██╔════╝
██████╔╝██║   ██║██║   ██║   ██║   ██║██╔██╗ ██║██║  ███╗       ██║   ███████║██████╔╝██║     █████╗  
██╔══██╗██║   ██║██║   ██║   ██║   ██║██║╚██╗██║██║   ██║       ██║   ██╔══██║██╔══██╗██║     ██╔══╝  
██║  ██║╚██████╔╝╚██████╔╝   ██║   ██║██║ ╚████║╚██████╔╝       ██║   ██║  ██║██████╔╝███████╗███████╗
╚═╝  ╚═╝ ╚═════╝  ╚═════╝    ╚═╝   ╚═╝╚═╝  ╚═══╝ ╚═════╝        ╚═╝   ╚═╝  ╚═╝╚═════╝ ╚══════╝╚══════╝
                                                                                                      
'''

class RTEntry:
    """
    Creates an object for one 
    """

    def __init__(self, destination_id: int, next_hop_id: int, metric: int, timeout: float = 90.0, garbage: float = 60.0):
        
        self.destination_id = destination_id
        self.next_hop_id = next_hop_id
        self.metric = metric

        self._timeout_interval = timeout
        self._garbage_interval = garbage

        self._timeout_timer = None
        self._garbage_timer = None
        self.in_garbage = False

        self._timeout_start_time = None
        self._garbage_start_time = None

        # start the per‐entry timeout
        self.reset_timeout()


    def reset_timeout(self):
        """(Re)start the timeout timer."""
        
        if self._timeout_timer:
            self._timeout_timer.cancel()
            # print(f"[DEBUG] Cancelled timeout for {self.destination_id}\n")
        
        if self._garbage_timer:
            self._garbage_timer.cancel()
            self._garbage_start_time = None

        self._timeout_start_time = time.monotonic() # We record the start time with this method
        # after timeout, switch to garbage state
        self._timeout_timer = threading.Timer(self._timeout_interval, self._on_timeout)
        self._timeout_timer.daemon = True
        self._timeout_timer.start()
        # print(f"[DEBUG] Timer has been initiated {self.destination_id}\n")

        self.in_garbage = False


    def _on_timeout(self):
        """Called when the route times out—mark INF and start garbage."""

        if self.metric < INF:
            self.metric =INF
            
            self.in_garbage = True
            # Start the garbage timer
            self._garbage_start_time = time.monotonic() # <--- Record start time
            self._garbage_timer = threading.Timer(self._garbage_interval, self._on_garbage)
            self._garbage_timer.daemon = True
            self._garbage_timer.start()
            # print(f"[DEBUG] Garbage timer initiated for {self.destination_id} ({self._garbage_interval:.1f}s)")



    def _on_garbage(self): # Noah - To complete this
        """Route has expired and will need to be pruned"""
        # print(f"[Garbage] Route to {self.destination_id} has expired and will be pruned..\n")


    def mark_unreachable(self):
        """Mark the route with metric INF and initiate the garbage timer if not already."""
        if self.metric < INF: # Only act if not already INF
            self.metric = INF
            # print(f"[UNREACHABLE] Route to {self.destination_id} marked unreachable. Metric set to INF.")

            if not self.in_garbage: # Start garbage timer only if not already in garbage
                 self.in_garbage = True
                 # Start garbage countdown immediately
                 # Cancel any lingering timeout timer as the route is now INF
                 if self._timeout_timer:
                     self._timeout_timer.cancel()
                     self._timeout_start_time = None

                 self._garbage_start_time = time.monotonic() # <--- Record start time
                 self._garbage_timer = threading.Timer(self._garbage_interval, self._on_garbage)
                 self._garbage_timer.daemon = True
                 self._garbage_timer.start()
                #  print(f"[DEBUG] Garbage timer initiated (mark_unreachable) for {self.destination_id} ({self._garbage_interval:.1f}s)")


    def cancel_timers(self):
        """Cancel both timeout and garbage timers."""
        if self._timeout_timer:
            self._timeout_timer.cancel()
            self._timeout_start_time = None
        if self._garbage_timer:
            self._garbage_timer.cancel()
            self._garbage_start_time = None

    def is_dead(self) -> bool:
        """After garbage_interval has elapsed, this entry is ready for removal."""
        return self.in_garbage and (self._garbage_timer is not None
                                    and not self._garbage_timer.is_alive())

    def __repr__(self):
        '''
            Prints info about the routing table entry
        '''
        status = "Active"
        timeout_display = "N/A"
        garbage_display = "N/A"

        current_time = time.monotonic()

        if self.metric == INF:
            status = "Unreachable (Garbage)"
            # Timeout has expired or route was marked INF
            timeout_display = "Expired"
            if self.in_garbage and self._garbage_timer and self._garbage_start_time is not None:
                 # Calculate remaining garbage time
                 elapsed_garbage_time = current_time - self._garbage_start_time
                 remaining_garbage_time = max(0.0, self._garbage_interval - elapsed_garbage_time)
                 garbage_display = f"{remaining_garbage_time:.1f}s left"
            elif self.in_garbage:
                 garbage_display = "Timer not running?" # Should not happen if in_garbage is true
            else:
                 garbage_display = "Garbage not started" # Should not happen if metric is INF


        elif self._timeout_timer and self._timeout_start_time is not None:
             status = "Active"
             # Calculate remaining timeout time
             elapsed_timeout_time = current_time - self._timeout_start_time
             remaining_timeout_time = max(0.0, self._timeout_interval - elapsed_timeout_time)
             timeout_display = f"{remaining_timeout_time:.1f}s left"
             garbage_display = "Inactive" # Garbage timer is not relevant for active routes

        
        return (
            f"\n############ Routing Table Entry #############\n"
            f"\nDestination: {self.destination_id}\n"
            f"Next Hop: {self.next_hop_id}\n"
            f"Metric: {self.metric}\n"
            f"Status: {status}\n" 
            f"Timeout: {timeout_display}\n" # <--- Modified to show time left
            f"Garbage: {garbage_display}\n" # <--- Modified to show time left
            f"\n##############################################\n"
            )



class RoutingTable:
    """
    Manages a set of RTEntry instances, keyed by destination_id
    """

    def __init__(self, timeout: float = 90.0, garbage: float = 90.0): # CHanged them from 30 and 30 to 90 and 60
        self._entries = {}  # dst_id -> RTEntry
        self._timeout = timeout
        self._garbage = garbage
        self._lock = threading.Lock()

    def add_or_update(self,
                      destination_id: int,
                      next_hop_id: int,
                      metric: int):
        """
        If new: insert a fresh RTEntry.  
        If existing: update next_hop and metric, reset its timeout.
        """
        # print(f"[UPDATE] Route to {destination_id} via {next_hop_id} updated. Metric={metric}")
        
        
        with self._lock:

            if destination_id not in self._entries:

                # print(f"[UPDATE] New route to {destination_id} via {next_hop_id} added with metric {metric}")
                e = RTEntry(destination_id, next_hop_id, metric, timeout=self._timeout, garbage=self._garbage)

                self._entries[destination_id] = e


            else:
                e = self._entries[destination_id]


                current_metric = e.metric
                is_from_current_next_hop = (e.next_hop_id == next_hop_id)

                if is_from_current_next_hop:
                    if metric == current_metric:
                         # Same metric, same next hop - reset timer
                        #  print(f"[UPDATE] Route to {destination_id} via {next_hop_id}: Same metric ({metric}). Resetting timer.")
                         e.reset_timeout()
                    elif metric < INF:
                        # Better or worse metric from current next hop (but not INF) - update metric and reset timer
                        # print(f"[UPDATE] Route to {destination_id} via {next_hop_id}: Metric changed from {current_metric} to {metric}. Updating and resetting timer.")
                        e.metric = metric
                        e.reset_timeout()
                    else: # metric is INF from current next hop
                        # Poison reverse received or neighbour marked it INF
                        # print(f"[UPDATE] Route to {destination_id} via {next_hop_id}: Received INF from current next hop. Marking unreachable.")
                        e.mark_unreachable() # This sets metric to INF and starts garbage timer

                else: # Update from a different next hop
                    if metric < current_metric:
                         # Better path found via a different neighbour
                        #  print(f"[UPDATE] Route to {destination_id}: Found better path via {next_hop_id} (metric {metric} < current {current_metric}). Updating route and resetting timer.")
                         e.next_hop_id = next_hop_id
                         e.metric = metric
                         e.reset_timeout()


    def mark_unreachable(self, destination_id: int):
        """
        Set the route’s metric to INF and let its garbage timer run out.
        """
        with self._lock:
            if destination_id in self._entries:
                e = self._entries[destination_id]
                # Use the method on the entry object to handle timer transitions
                e.mark_unreachable()

    def prune(self):
        """
        Remove any entries whose garbage timer has expired.
        """

        with self._lock:
            to_delete = [dst for dst, e in self._entries.items() if e.is_dead()]

            for dst in to_delete:
                # print(f"[PRUNE] Removing route to {dst} (Garbage timer expired).")
                e = self._entries.pop(dst)
                e.cancel_timers()


############################

    def __iter__(self):
        """
        Iterate current RTEntry objects (thread‐safe snapshot).
        """
        with self._lock:
            # Return a list copy to iterate safely while the table might be modified
            return iter(list(self._entries.values()))

    def __len__(self):
        with self._lock:
            return len(self._entries)

    def __repr__(self):
        with self._lock:
            lines = [f"RoutingTable (Entries: {len(self._entries)}):"]
            if not self._entries:
                 lines.append("  (empty)")
            else:
                # Sort entries for consistent output
                sorted_entries = sorted(self._entries.values(), key=lambda e: e.destination_id)
                for e in sorted_entries:
                    # Indent the representation of each entry
                    entry_lines = repr(e).strip().split('\n')
                    for line in entry_lines:
                         lines.append("  " + line)
            return "\n".join(lines)
        
    def print_table(self):
        print(self.__repr__())

    def reset_direct_neighbour_timer(self, neighbour_id: int):
       
        with self._lock:
        
            if neighbour_id in self._entries:
                 e = self._entries[neighbour_id]
           
                 if e.destination_id == neighbour_id and e.next_hop_id == neighbour_id:
                      e.reset_timeout()
