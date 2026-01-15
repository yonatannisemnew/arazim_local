import os
import sys 
import time
import pydivert
import constants

def windivert_filter() -> str:
    return "icmp"

def packet_filter(packet) -> bool:
    """
    filters packet based on:
    direction, icmp reply, magic
    :param packet: the intercepted packet
    return: bool
    """
    return packet.icmp and packet.icmp.type == constants.ICMP_REPLY_TYPE \
        and packet.direction == constants.PAKCET_DIRECTION_IN \
            and packet.payload.startswith(constants.PAYLOAD_MAGIC)
    
def extract_icmp_payload(packet):
    '''
    extract our data from payload assuming it passed packet_filter

    param packet: the intercepted packet
    return: the data after our magic bytes
    '''
    return packet.payload[len(constants.PAYLOAD_MAGIC):]

def sniffer(): 
    wind_filter = windivert_filter()
    with pydivert.WinDivert(wind_filter) as w:
        print("STARTED IN SNIFFER")
        for packet in w:
            if packet_filter(packet):
                #its our packet
                icmp_payload = extract_icmp_payload(packet)
                new_packet = pydivert.Packet(icmp_payload, interface=packet.interface, direction=packet.direction)
                w.send(new_packet)
                
            w.send(packet)
                

def main(argc, argv):
    subnet = argv[1]
    mask = argv[2]
    router_ip = argv[3]
    our_ip = argv[4]
    sniffer()

if __name__ == "__main__":
    argc = len(sys.argv)
    argv = sys.argv
    main(len(sys.argv), sys.argv)