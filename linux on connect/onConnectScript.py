import disableRST


def on_connect():
    #disables TCP RST packets, because the OS gets confused and misleads clients to think ports are closed
    disableRST.disable_rst()