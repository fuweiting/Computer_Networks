from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.cli import CLI

class Topo1(Topo):
    def build(self):
        # Add 4 hosts hA, hB, hC, hD
        hA = self.addHost('Host_A', ip='10.0.0.1', mac='00:00:00:00:00:01')
        hB = self.addHost('Host_B', ip='10.0.0.2', mac='00:00:00:00:00:02')
        hC = self.addHost('Host_C', ip='10.0.0.3', mac='00:00:00:00:00:03')
        hD = self.addHost('Host_D', ip='10.0.0.4', mac='00:00:00:00:00:04')
        
        # Add 3 switches s1, s2, s3
        s1 = self.addSwitch('Switch_1')
        s2 = self.addSwitch('Switch_2')
        s3 = self.addSwitch('Switch_3')
        
        # Add links between hosts and switches
        self.addLink(hA, s3, port1=1, port2=1)      # connect Host_A's port #1 to Switch_3's port #1
        self.addLink(hB, s1, port1=1, port2=3)      # connect Host_B's port #1 to Switch_1's port #3
        self.addLink(hC, s2, port1=1, port2=3)      # connect Host_C's port #1 to Switch_2's port #3
        self.addLink(hD, s2, port1=1, port2=2)      # connect Host_D's port #1 to Switch_2's port #2
        
        # Add links between switches
        self.addLink(s1, s2, port1=2, port2=4)      # connect Switch_1's port #2 to Switch_2's port #4
        self.addLink(s1, s3, port1=1, port2=3)      # connect Switch_1's port #1 to Switch_3's port #3
        self.addLink(s2, s3, port1=1, port2=2)      # connect Switch_2's port #1 to Switch_3's port #2
        
if __name__ == '__main__':
    topo = Topo1()
    net = Mininet(topo=topo, controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6653), link=TCLink)
    
    # Start network
    net.start()
    
    # Run the command-line interface for interactive testing
    CLI(net)
    
    # Stop network
    net.stop()