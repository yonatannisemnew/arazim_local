import pydivert
import constants


try:
    # Filter for ICMP (Ping)
    with pydivert.WinDivert("icmp") as w:
        print("WinDivert is active! Try pinging 67.67.67.67...")

        for packet in w:
            # Check if someone is trying to ping our "fake" IP
            if packet.dst_addr == "67.67.67.67" and packet.icmp.type == 8:
                print(f"Intercepted Ping Request to {packet.dst_addr}!")

                # 1. Swap addresses
                src = packet.src_addr
                dst = packet.dst_addr
                packet.src_addr = dst
                packet.dst_addr = src

                # 2. Change ICMP Request (8) to ICMP Reply (0)
                packet.icmp.type = 0

                # 3. Direction must be flipped so it looks like it's coming 'in'
                packet.direction = 1

                # Send the "Fake" Reply
                w.send(packet)
                print(f"Sent fake Reply: {packet.src_addr} -> {packet.dst_addr}")
            else:
                # Let all other packets pass through normally
                w.send(packet)

except PermissionError:
    print("FAILED: Run as Administrator!")
except Exception as e:
    print(f"Error: {e}")