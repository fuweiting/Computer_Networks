from mininet.net import Mininet
from mininet.node import DefaultController, RemoteController
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.cli import CLI

class Topo1(Topo):
    def build(self):
        # Add 9 hosts h1, h2, h3, h4, h5, h6, h7, h8, h9
        h1 = self.addHost('h1', ip='10.0.0.1', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', ip='10.0.0.2', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', ip='10.0.0.3', mac='00:00:00:00:00:03')
        h4 = self.addHost('h4', ip='10.0.0.4', mac='00:00:00:00:00:04')
        h5 = self.addHost('h5', ip='10.0.0.5', mac='00:00:00:00:00:05')
        h6 = self.addHost('h6', ip='10.0.0.6', mac='00:00:00:00:00:06')
        h7 = self.addHost('h7', ip='10.0.0.7', mac='00:00:00:00:00:07')
        h8 = self.addHost('h8', ip='10.0.0.8', mac='00:00:00:00:00:08')
        h9 = self.addHost('h9', ip='10.0.0.9', mac='00:00:00:00:00:09')
        
        # Add 8 switches s1, s2, s3, s4, s5, s6, s7, s8
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')
        s5 = self.addSwitch('s5')
        s6 = self.addSwitch('s6')
        s7 = self.addSwitch('s7')
        s8 = self.addSwitch('s8')
        
        # Add links between hosts and switches
        self.addLink(h1, s1)  # connect Host 1 to Switch 1
        self.addLink(h2, s3)  # connect Host 2 to Switch 3
        self.addLink(h3, s7)  # connect Host 3 to Switch 7
        self.addLink(h4, s5)  # connect Host 4 to Switch 5
        self.addLink(h5, s5)  # connect Host 5 to Switch 5
        self.addLink(h6, s8)  # connect Host 6 to Switch 8
        self.addLink(h7, s8)  # connect Host 7 to Switch 8
        self.addLink(h8, s6)  # connect Host 8 to Switch 6
        self.addLink(h9, s4)  # connect Host 9 to Switch 4
        
        # Add links between switches
        self.addLink(s1, s2)  # connect Switch 1 to Switch 2
        self.addLink(s1, s3)  # connect Switch 1 to Switch 3
        self.addLink(s1, s6)  # connect Switch 1 to Switch 6
        self.addLink(s2, s3)  # connect Switch 2 to Switch 3
        self.addLink(s2, s4)  # connect Switch 2 to Switch 4
        self.addLink(s2, s5)  # connect Switch 2 to Switch 5
        self.addLink(s2, s7)  # connect Switch 2 to Switch 7
        self.addLink(s3, s4)  # connect Switch 3 to Switch 4
        self.addLink(s4, s5)  # connect Switch 4 to Switch 5
        self.addLink(s4, s8)  # connect Switch 4 to Switch 8
        self.addLink(s5, s7)  # connect Switch 5 to Switch 7
        self.addLink(s5, s8)  # connect Switch 5 to Switch 8
        self.addLink(s6, s7)  # connect Switch 6 to Switch 7

if __name__ == '__main__':
    topo = Topo1()
    # net = Mininet(topo=topo, controller=DefaultController, link=TCLink)
    net = Mininet(topo=topo, controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6653), link=TCLink)
    
    # Start network
    net.start()
    
    # Run the command-line interface for interactive testing
    CLI(net)
    
    # Stop network
    net.stop()