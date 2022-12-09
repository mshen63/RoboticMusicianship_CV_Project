# NOTE: mini function for testing your UDP connection w the computer running the server and MAX
from pythonosc import udp_client

PORT_TO_MAX = 5002
IP = "192.168.2.2"

global client
client = udp_client.SimpleUDPClient(IP, PORT_TO_MAX)
input("hello")
while True:
    print("sent")
    client.send_message("/point", 1)
    input("pause")