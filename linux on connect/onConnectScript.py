import disableRST
import editRouting
def on_connect():
    #disables TCP RST packets, because the OS gets confused and misleads clients to think ports are closed
    disableRST.disable_rst()
    #Edits the routing table so 127.x.x.x will go through loopback, to be picked up by our sniffers
    editRouting.edit_routing()
