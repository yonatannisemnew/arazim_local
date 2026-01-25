import enableRST


def on_connect():
    #enables TCP RST packets, because we disabled them on connection
    enableRST.enable_rst()