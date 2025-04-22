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

    def __init__(self, destination_id: int, next_hop_id: int, metric: int, timeout: float = 30.0, garbage: float = 30.0):
        
        self.destination_id = destination_id
        self.next_hop_id = next_hop_id
        self.metric = metric

        self._timeout_interval = timeout
        self._garbage_interval = garbage

        self._timeout_timer = None
        self._garbage_timer = None
        self.in_garbage = False

        # start the per‐entry timeout
        self.reset_timeout()

    def reset_timeout(self):
        """(Re)start the timeout timer."""
        
        if self._timeout_timer:
            self._timeout_timer.cancel()

        # after timeout, switch to garbage state
        self._timeout_timer = threading.Timer(self._timeout_interval,
                                              self._on_timeout)
        self._timeout_timer.daemon = True
        self._timeout_timer.start()

        # if previously in garbage, cancel that
        if self._garbage_timer:
            self._garbage_timer.cancel()
        self.in_garbage = False

    def _on_timeout(self):
        """Called when the route times out—mark INF and start garbage."""
        self.metric = INF
        self.in_garbage = True
        self._garbage_timer = threading.Timer(self._garbage_interval,
                                              self._on_garbage)
        self._garbage_timer.daemon = True
        self._garbage_timer.start()

    def _on_garbage(self):
        """Route fully aged out; caller (RoutingTable) will prune it."""
        # nothing here—RoutingTable will check `in_garbage` + age

    def cancel_timers(self):
        if self._timeout_timer:
            self._timeout_timer.cancel()
        if self._garbage_timer:
            self._garbage_timer.cancel()

    def is_dead(self) -> bool:
        """After garbage_interval has elapsed, this entry is ready for removal."""
        return self.in_garbage and (self._garbage_timer is not None
                                    and not self._garbage_timer.is_alive())

    def __repr__(self):
        return (f"<RTEntry dst={self.destination_id} nh={self.next_hop_id} "
                f"m={self.metric}{' GARB' if self.in_garbage else ''}>")



class RoutingTable:
    """
    Manages a set of RTEntry instances, keyed by destination_id.
    """

    def __init__(self, timeout: float = 30.0, garbage: float = 30.0):
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
        
        with self._lock:
            if destination_id not in self._entries:
                e = RTEntry(destination_id,
                            next_hop_id,
                            metric,
                            timeout=self._timeout,
                            garbage=self._garbage)
                self._entries[destination_id] = e

            else:
                e = self._entries[destination_id]
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
                e.metric = INF
                e.in_garbage = True
                
                # start garbage countdown immediately
                e._garbage_timer = threading.Timer(self._garbage,
                                                   lambda: None)
                e._garbage_timer.daemon = True
                e._garbage_timer.start()

    def prune(self):
        """
        Remove any entries whose garbage timer has expired.
        """

        with self._lock:
            to_delete = [
                dst for dst, e in self._entries.items() if e.is_dead()
            ]

            for dst in to_delete:
                e = self._entries.pop(dst)
                e.cancel_timers()

    def __iter__(self):
        """
        Iterate current RTEntry objects (thread‐safe snapshot).
        """
        with self._lock:
            return iter(list(self._entries.values()))

    def __len__(self):
        with self._lock:
            return len(self._entries)

    def __repr__(self):
        with self._lock:
            lines = ["RoutingTable:"]
            for e in self._entries.values():
                lines.append("  " + repr(e))
            return "\n".join(lines)

    def print_table(self):
        print(self.__repr__())
