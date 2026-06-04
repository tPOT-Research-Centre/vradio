from zeroconf import Zeroconf, ServiceBrowser

class SpotifyServiceListener:
    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            print(f"Discovered Spotify Connect device: {name}")
            print(f"  Address: {'.'.join(map(str, info.addresses[0]))}:{info.port}")
            print(f"  Properties: {info.properties}")

    def update_service(self, zeroconf, type, name):
        # Optional: handle updates (e.g., IP or properties changed)
        print(f"Service updated: {name}")

    def remove_service(self, zeroconf, type, name):
        print(f"Service {name} removed")

zeroconf = Zeroconf()
listener = SpotifyServiceListener()
browser = ServiceBrowser(zeroconf, "_spotify-connect._tcp.local.", listener)

try:
    input("Press enter to exit...\n\n")
finally:
    zeroconf.close()
