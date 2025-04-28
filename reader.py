'''
This Module will read through the info in a config file to create
daemon router instance.

We need to Process 3 Parameters:
router_ID, input_ports, outputs  ~~ #if one is missing; stop program with an err message

CONDITIONS TO BE MET:
router_ID's of all routers are distinct

 If two routers A and B are neighbours it must:
 - Provide an input port x at B that is also listed as output port of A
 - Provide an input port y at A that is also listed as output port of B  # 2 way comms
 - Ensure no other host

{
    'Config-File': {
        'Router-ID': '0',
        'Input-Ports': '6110, 6201, 7345',
        'Output-Ports': '5000-1-1, 5002-5-4',
        'Periodic-Time': '',
        'Timeout': ''
    }
}

'''

import sys
import os
import configparser
from RIPv2_router import * # call this to initialise the daemon
from collections import Counter

# import RIPv2_router

TIME_DEFAULT = 0 # change this later on
LOCAL_HOST = '127.0.0.1'
ROUTER_ID = None
ROUTER_INPUTS = []
ROUTER_OUTPUTS = []


def init_daemon():
    '''
        Initialises the Router Daemon
    '''
    
    if len(sys.argv) < 2:  # Check if a file argument is provided (1st Param)
        raise Exception("ERROR: Please provide config file :)")
        sys.exit()

    file = os.path.join("config-files", sys.argv[1])

    if not os.path.isfile(file):  # Checks if the file exists if not raise ERROR
        raise Exception(f"ERROR: Invalid File!")
        sys.exit()

    content = read_config_file(file) # Returns the content of the config file
    router_id = read_router_ID(content) # Calls functions to retreive data from the config files 
    read_output_ports(content) # Retrieves a list of output ports in the format: "[PORT-METRIC-ID]"
    read_input_ports(content)

    print("\n######################\n")
    print(f">> Router ID: {ROUTER_ID}\n")

    print(f">> Output ports: {ROUTER_OUTPUTS}\n")
    
    print(f">> Input ports: {ROUTER_INPUTS}")

    print("\nConfiguration File Accepted ")
    print("\n#######################\n")
    

def read_config_file(config_file):
    '''
        This function will read the config file passed in 
        the terminal and will
    '''

    try:
        content = configparser.ConfigParser()
        content.read(config_file)

    except configparser.ParsingError:
        print("[ERROR] Invalid File\n")
        sys.exit()

    return content


def read_router_ID(config_data):
    '''
        retreives router ID val from config file
        and assesses the validity (maybe return the ID)
    '''

    try:
        router_id = int(config_data.get("ConfigFile", "Router-ID")) # Finds the value under Router-ID field

    except configparser.ParsingError as e:
        print(f"[ERROR] parsing the config file: {e}")
        sys.exit()

    except KeyError:
        raise Exception("ERROR: No Router ID found in the config.")
        
    except ValueError:
        raise Exception("ERROR: Router ID is not a valid integer.")
        
    if not (1 <= router_id <= 64000):
        raise Exception("ERROR: Router ID must be within the range of 1 - 64000..")
        
    global ROUTER_ID
    ROUTER_ID = router_id
    return router_id

    


def read_input_ports(config_file):
    '''
        retreives the list of input ports in the config file 
        and assess validity and returns
    '''

    try:
        router_input = config_file['ConfigFile']['Input-Ports'].split(', ') # list of ports

        if router_input == [""]: # Checks if there is no given router input
            print("ERROR: No input ports found..")
            sys.exit()

        for port in router_input: # Loop through each port, strip whitespaces and convert the ports into an integer
            port = int(port.strip())
            ROUTER_INPUTS.append(port)
            if 1024 < port > 64000: # Checks if the ports are valid
                raise ValueError

        check_ports = set(ROUTER_INPUTS) # Check if there are any duplicates
        if len(check_ports) != len(ROUTER_INPUTS):
            raise Exception("ERROR: Duplciate input ports given | Cannot have a duplicated input port..")

        return ROUTER_INPUTS
        
    except ValueError:
        print("ERROR: Each input port must be a positive integer between 1024-64000 inclusively")
        sys.exit()

    except KeyError:
        print('ERROR: "Input-Ports" missing in the Config File.')
        sys.exit()


def read_output_ports(config_file):
    '''
        retreives the list of output ports in the config file   
        and assess validity
        In the format: {'port': 5000, 'metric': 1, 'router_id': 2},

    '''

    duplicate_port_check = []

    try:
        router_outputs = config_file['ConfigFile']['Output-Ports'].split(', ') # list of ports
        if router_outputs == [""]:
            print("ERROR: No output ports found..")
            sys.exit()

            
        for port in router_outputs: # Loop through each port, strip whitespaces and convert the ports into an integer
            split = port.split('-')
            if len(split) != 3:
                print("ERROR: Invalid output port format" 
                f"\nExpected: 'Port-Metric-ID' | Given: {split}")
                sys.exit()

            duplicate_port_check.append(int(split[0]))

            ROUTER_OUTPUTS.append(split)

        for port in  duplicate_port_check:
            if 1024 < port > 64000: # Checks if the ports are valid
                raise ValueError

        for key, value in Counter(duplicate_port_check).items(): # Check if there are any duplicates
            if value >= 2:
                raise Exception("ERROR: Duplciate output ports found | Cannot have a duplicated output port..")

        return ROUTER_OUTPUTS
        
    except ValueError:
        print("ERROR: Each output port must be a positive integer between 1024-64000 inclusively")
        sys.exit()

    except KeyError:
        print('ERROR: "Output-Ports" missing in the Config File.')
        sys.exit()

def create_socket(ports):
    '''
        Creates a socket for each port and binds it
    '''
    pass


if __name__ == "__main__":
    init_daemon()
    router_instance = RIPv2_Router(ROUTER_ID, ROUTER_INPUTS, ROUTER_OUTPUTS)
    router_instance.monitor_RT()  # Start listening for updates INF loop

