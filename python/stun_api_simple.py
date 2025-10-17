'''
    1. This code relays stun request and can be used when STUN server and NBI server are not on the same address.
    2. STUN Server still must be located on public ip and this code also.
    3. NBI Server must be able to contact this script.
'''
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import socket
import asyncio

# --- FastAPI Setup ---
app = FastAPI(title="STUN Server Simple UDP Relay")

# --- Configuration (STUN Server Machine) ---
# This MUST be the actual local IP and STUN port for binding
STUN_SERVER_IP = "192.168.191.200" # IP ADDRESS OF THE ACUTAL STUN SERVER
STUN_SERVER_PORT = 3478
# Buffer size for receiving the UDP reply
UDP_BUFFER_SIZE = 1024


# --- Data Model for Incoming Request ---
class PreconfiguredUdpRequest(BaseModel):
    """Data model for the JSON payload containing the pre-built message."""
    target_host: str
    target_port: int
    udp_message_string: str # The fully built 'msg' string

# --- Core UDP Sending Function ---

async def send_preconfigured_udp(target_host: str, target_port: int, udp_message_string: str):
    """Sends the pre-built UDP packet, binding the source socket to the STUN port."""
    
    udp_bytes = udp_message_string.encode('utf-8')
    sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind((STUN_SERVER_IP, STUN_SERVER_PORT))
        print(f"Bound successfully to {STUN_SERVER_IP}:{STUN_SERVER_PORT}")
    except socket.error as e:
        print(f"ERROR: Failed to bind to STUN port: {e}")
        sock.close()
        raise HTTPException(status_code=500, detail=f"Failed to bind STUN port: {e}")

    server_address_port = (target_host, target_port)
    
    # Send the packet 3 times, matching the original JS logic
    for i in range(3):
        try:
            sock.sendto(udp_bytes, server_address_port)
            print(f"Sent UDP packet to {target_host}:{target_port} (Attempt {i+1}/3)")
        except socket.error as e:
            print(f"ERROR sending UDP packet: {e}")
            
    # Wait for a reply
    sock.settimeout(3) 
    
    try:
        # Use asyncio.to_thread for the blocking call
        raw_data, sender = await asyncio.to_thread(sock.recvfrom, UDP_BUFFER_SIZE)
        
        # Simple decoding for logging/debugging
        try:
            response_msg = raw_data.decode('utf-8')
        except UnicodeDecodeError:
            response_msg = f"Binary/Unknown Data: {raw_data.hex()}"
            
        print(f"Received reply from {sender}: {response_msg}")
        return {"status": "success", "reply": response_msg, "sender": sender}
        
    except socket.timeout:
        print("UDP Recv timeout: No reply received.")
        return {"status": "sent_no_reply", "message": "UDP packet sent 3 times, but no reply received within timeout."}
    finally:
        sock.close()


# --- FastAPI Endpoint ---

@app.post("/relay_preconfigured_udp")
async def relay_preconfigured_udp_message(request: PreconfiguredUdpRequest):
    """Accepts a pre-built UDP message string and sends it out."""
    
    print("-" * 40)
    print(f"Relay Request Received for: {request.target_host}:{request.target_port}")
    print(f"UDP Message Length: {len(request.udp_message_string)} bytes")
    
    # Execute the UDP send logic
    try:
        result = await send_preconfigured_udp(
            request.target_host, 
            request.target_port, 
            request.udp_message_string
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error during UDP relay: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

# --- Run Command ---
# uvicorn stun_api_simple:app --host 0.0.0.0 --port 8558
