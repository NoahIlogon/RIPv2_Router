'''
The config file reader will:
- take a txt file and check it for validity
- initialise the router daemon.

<Configparser will create this dict format>
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
from RIPv2_router import * 
from collections import Counter


TIME_DEFAULT = 0 
LOCAL_HOST = '127.0.0.1'
ROUTER_ID = None
ROUTER_INPUTS = []
ROUTER_OUTPUTS = []
ROUTER_ID_CHECK_PORT_BASE = 7777 

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
        the terminal and will try to parse it with the config parser
    '''

    try:
        content = configparser.ConfigParser()
        content.read(config_file)

    except configparser.ParsingError:
        print("[ERROR] Invalid File\n")
        sys.exit()

    return content


def check_router_id_taken(router_id): 

    ''' 

    Tries to bind a unique socket based on the Router ID. 

    If bind fails, it means Router ID is already taken. 

    ''' 

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 

    try: 

        sock.bind((LOCAL_HOST, ROUTER_ID_CHECK_PORT_BASE + router_id)) 

    except OSError: 

        sys.exit(f"ERROR: Router ID {router_id} already taken. Another router is using it.") 

    return sock # Keep the socket open to reserve the ID 


def read_router_ID(config_data):
    '''
        retreives router ID value from config file
        and assesses the validity then returns the router ID
    '''

    try:
        router_id = int(config_data.get("ConfigFile", "Router-ID")) # Finds value under Router-ID field

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
        and assess validity and returns the router input(s)
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


if __name__ == "__main__":
    init_daemon()
    id_check_socket = check_router_id_taken(ROUTER_ID) 
    router_instance = RIPv2_Router(ROUTER_ID, ROUTER_INPUTS, ROUTER_OUTPUTS)
    router_instance.monitor_RT()  # Start listening for updates (INF loop)

