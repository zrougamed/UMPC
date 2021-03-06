#!/usr/bin/env python3

import sys
import socket
import time
import json
# from contextlib import contextmanager 

import paho.mqtt.publish as publish


HOST = '127.0.0.1'
PORT = 50120
BUFSIZE = 1024
ADDR = (HOST, PORT)

DEVICES = json.load(open('devices.json', 'r')).get('devices', [])

class Client:
    def __init__(self, address):
        self.address = address
        self.ttl = 60  # 60 seconds TTL
        self.sent_history = []
        self.recv_history = []
        self.last_msg = time.time()

    def is_expired(self):
        now = time.time()
        if (now - self.last_msg) > 60:
            return True
        return False

    def received(self, msg):
        self.recv_history.append(msg)
        self.last_msg = time.time()

    def get_last_msg(self):
        if len(self.recv_history) > 0:
            return self.recv_history[-1]
        return str.encode("")

    def send(self, sock, data):
        self.sent_history.append(data)
        sock.sendto(str.encode(data), self.address)

    def __str__(self):
        return "Client(address=({}))".format(self.address)


class UdpServer:
    def __init__(self, address, callback=None):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind(address)
        self._clients = {}
        self._callback = callback

    def run(self):
        while True:
            data, addr = self._sock.recvfrom(BUFSIZE)
            if data is None:
                print("Got zero data from {}:{} - ignore..".format(addr[0], addr[1]))
                continue

            if not data.strip():
                continue
            print("Rec ...")
            print(data)
            print("Incoming {}:{} Data: {}".format(time.ctime(), addr[0], addr[1], data))
            if addr not in self._clients:
                self._clients[addr] = Client(addr)
                self._clients[addr].received(data)
                self._clients[addr].send(self._sock, "ACK: Welcome new client!")
                print("New client registered: {}".format(self._clients[addr]))
            else:
                self._clients[addr].received(data)
                self._clients[addr].send(self._sock, "ACK")

            # Cleanup expired clients..
            for c_key in self._clients:
                if self._clients[c_key].is_expired():
                    self._clients.pop(c_key)

            try:
                msg = json.loads(data.decode("utf-8"))
                if self._callback and callable(self._callback):
                    self._callback(msg)

            except json.decoder.JSONDecodeError as err:
                print("Error decoding JSON: {}".format(err))
                print("")

        self._sock.close()


class TB:
    def __init__(self, url, port=1883):
        self.url = url
        self.port = port 

    def get_device_token(self, device_name):
        for d in DEVICES:
            print(d)
            if d.get("name", "") == device_name:
                return d.get("token", "")
        return None

    def __call__(self, msg):
        device_name = msg.get("device")
        username = self.get_device_token(msg.get("device"))
        if not username:
            print("ERROR: Username not found")
            print("device_name", device_name)
            return

        credentials = {
            "username": username
        }
        payload = {
            "latitude": msg.get("latitude", 0),
            "longitude": msg.get("longitude", 0)

        }

        try:
            publish.single("v1/devices/me/telemetry",
                           json.dumps(payload),
                           hostname=self.url,
                           port=self.port,
                           auth=credentials)
            print("Packet sent !")
        except KeyError as err:
            print("Error from Paho MQTT: {}".format(err))


def mqtt_to_thingsboard(msg):
    print("debugging: {}".format(msg))
    device = msg.get("device")
    value = msg.get("value")


def main():
    tb = TB("broker.hivemq.com", 1883) # IP or Hostname  for the MQTT Server 
    # http://www.hivemq.com/demos/websocket-client/
    server = UdpServer(ADDR, callback=tb)
    try:
        print("Starting Server ...")
        server.run()
    except KeyboardInterrupt:
        print("Server shutdown..")
        sys.exit(1)


if __name__ == '__main__':
    main()

