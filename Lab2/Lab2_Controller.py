import networkx as nx
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, arp

G = nx.Graph()
# Create an undirected and unweighted graph G, defining the network topology by adding edges
G.add_edges_from([
    # Host to switch connections
    ('h1', 's1'), ('h2', 's3'), ('h3', 's7'), ('h4', 's5'), ('h5', 's5'), 
    ('h6', 's8'), ('h7', 's8'), ('h8', 's6'), ('h9', 's4'),
    
    # Switch to switch connections
    ('s1', 's2'), ('s1', 's3'), ('s1', 's6'),
    ('s2', 's3'), ('s2', 's4'), ('s2', 's5'), ('s2', 's7'),
    ('s3', 's4'),
    ('s4', 's5'), ('s4', 's8'),
    ('s5', 's7'), ('s5', 's8'),
    ('s6', 's7')
    ])

# Define all source-to-destination host pairs
src_dst_pairs = [
    ('h1', 'h2'), ('h1', 'h3'), ('h1', 'h4'), ('h1', 'h5'), ('h1', 'h6'), ('h1', 'h7'), ('h1', 'h8'), ('h1', 'h9'),
    ('h2', 'h1'), ('h2', 'h3'), ('h2', 'h4'), ('h2', 'h5'), ('h2', 'h6'), ('h2', 'h7'), ('h2', 'h8'), ('h2', 'h9'),
    ('h3', 'h1'), ('h3', 'h2'), ('h3', 'h4'), ('h3', 'h5'), ('h3', 'h6'), ('h3', 'h7'), ('h3', 'h8'), ('h3', 'h9'),
    ('h4', 'h1'), ('h4', 'h2'), ('h4', 'h3'), ('h4', 'h5'), ('h4', 'h6'), ('h4', 'h7'), ('h4', 'h8'), ('h4', 'h9'),
    ('h5', 'h1'), ('h5', 'h2'), ('h5', 'h3'), ('h5', 'h4'), ('h5', 'h6'), ('h5', 'h7'), ('h5', 'h8'), ('h5', 'h9'),
    ('h6', 'h1'), ('h6', 'h2'), ('h6', 'h3'), ('h6', 'h4'), ('h6', 'h5'), ('h6', 'h7'), ('h6', 'h8'), ('h6', 'h9'),
    ('h7', 'h1'), ('h7', 'h2'), ('h7', 'h3'), ('h7', 'h4'), ('h7', 'h5'), ('h7', 'h6'), ('h7', 'h8'), ('h7', 'h9'),
    ('h8', 'h1'), ('h8', 'h2'), ('h8', 'h3'), ('h8', 'h4'), ('h8', 'h5'), ('h8', 'h6'), ('h8', 'h7'), ('h8', 'h9')
    ]

# Find two most-disjoint shortest paths
def find_two_disjoint_shortest_paths(G, source, destination):
    path_1 = nx.shortest_path(G, source, destination, weight='weight')
    G_2 = G.copy()
    for i in range(len(path_1) - 1):
        u, v = path_1[i], path_1[i+1]
        if "h" in u or "h" in v:
            continue
        G_2.remove_edge(u, v)
    path_2 = nx.shortest_path(G_2, source, destination, weight='weight')
    return path_1, path_2

# Calculate the two most-disjoint shortest paths for all source-destination pairs
paths = {}
for src, dst in src_dst_pairs:
    path_1, path_2 = find_two_disjoint_shortest_paths(G, src, dst)
    paths[(src, dst)] = (path_1, path_2)

# Output the two most-disjoint shortest paths of each (src, dst) pair on the controller terminal
for pair, (path_1, path_2) in paths.items():
    print(f"Paths for {pair}")
    print(f"Path 1: {path_1}")
    print(f"Path 2: {path_2}")

class ShortestPathController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ShortestPathController, self).__init__(*args, **kwargs)
        self.paths = paths
        
        # Mapping of host-to-switch and their ports
        self.host_ports = {
            ('h1', 's1'): 0, ('s1', 'h1'): 1,
            ('h2', 's3'): 0, ('s3', 'h2'): 1,
            ('h3', 's7'): 0, ('s7', 'h3'): 1,
            ('h4', 's5'): 0, ('s5', 'h4'): 1,
            ('h5', 's5'): 0, ('s5', 'h5'): 2,
            ('h6', 's8'): 0, ('s8', 'h6'): 1,
            ('h7', 's8'): 0, ('s8', 'h7'): 2,
            ('h8', 's6'): 0, ('s6', 'h8'): 1,
            ('h9', 's4'): 0, ('s4', 'h9'): 1,
        }
        
        # Mapping of switch-to-switch connections and their ports
        self.switch_ports = {
            ('s1', 's2'): 2, ('s2', 's1'): 1,
            ('s1', 's3'): 3, ('s3', 's1'): 2,
            ('s1', 's6'): 4, ('s6', 's1'): 2,
            ('s2', 's3'): 2, ('s3', 's2'): 3,
            ('s2', 's4'): 3, ('s4', 's2'): 2,
            ('s2', 's5'): 4, ('s5', 's2'): 3,
            ('s2', 's7'): 5, ('s7', 's2'): 2,
            ('s3', 's4'): 4, ('s4', 's3'): 3,
            ('s4', 's5'): 4, ('s5', 's4'): 4,
            ('s4', 's8'): 5, ('s8', 's4'): 3,
            ('s5', 's7'): 5, ('s7', 's5'): 3,
            ('s5', 's8'): 6, ('s8', 's5'): 4,
            ('s6', 's7'): 3, ('s7', 's6'): 4
        }
        
        # Dictionary to store datapath objects for connected switches
        self.datapaths = {}
        
        # Mapping of MAC addresses to host names
        self.mac_to_host = {
            "00:00:00:00:00:01": "h1",
            "00:00:00:00:00:02": "h2",
            "00:00:00:00:00:03": "h3",
            "00:00:00:00:00:04": "h4",
            "00:00:00:00:00:05": "h5",
            "00:00:00:00:00:06": "h6",
            "00:00:00:00:00:07": "h7",
            "00:00:00:00:00:08": "h8",
            "00:00:00:00:00:09": "h9"
        }

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        # Save the datapath and datapath ID when connecting to switches
        datapath = ev.msg.datapath
        dpid = datapath.id
        self.datapaths[dpid] = datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install a default flow table entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

        # Install flow table entries for all precomputed paths between host pairs,
        # ensuring communication between all hosts using the shortest paths
        self.install_all_paths()
    
    # Install a flow entry on a switch
    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    # Install the flow on both src_host to dst_host and dst_host to src_host, 
    # ensuring that the hosts pair can communicate to each other
    def install_all_paths(self):
        # Iterate through all precomputed host pairs and their paths
        for (src_host, dst_host), (path_1, path_2) in self.paths.items():
            # Two most-disjoint shortest paths are precomputed for each host pair
            # path_1 is used as the default path for communication
            
            # Install flows for src_host -> dst_host using path_1
            self.install_path_flow(path_1, src_host, dst_host)
            # Install flows for dst_host -> src_host using the reverse of path_1
            self.install_path_flow(path_1[::-1], dst_host, src_host)
            

    def install_path_flow(self, path, src_host, dst_host):
        # Retrieve the MAC addresses of the source and destination hosts
        src_mac = self.get_host_mac(src_host)
        dst_mac = self.get_host_mac(dst_host)

        # Iterate through all nodes in the path
        # Determine the output port for each hop in the path
        # Handle connections between hosts and switches, as well as switch-to-switch links
        for i in range(len(path)-1):
            u = path[i]
            v = path[i+1]

            # Determine the output port for the current link
            if u.startswith('h') or v.startswith('h'):
                out_port = self.host_ports.get((u, v))
                if out_port is None:
                    out_port = self.host_ports.get((v, u))
            else:
                out_port = self.switch_ports.get((u, v))
                if out_port is None:
                    out_port = self.switch_ports.get((v, u))

            if out_port is None:
                self.logger.error("No port mapping found for link (%s, %s)", u, v)
                continue

            # Install the flow on the current switch
            # If the current node `u` is a switch, install the flow there
            # If the current node `u` is a host, install the flow on the next switch `v`
            current_switch = u if u.startswith('s') else v
            dpid = int(current_switch.strip('s'))
            datapath = self.datapaths.get(dpid)
            if datapath is None:
                self.logger.error("No datapath found for switch %s (dpid=%d)", current_switch, dpid)
                continue

            parser = datapath.ofproto_parser
            match = parser.OFPMatch(eth_src=src_mac, eth_dst=dst_mac)
            actions = [parser.OFPActionOutput(out_port)]
            self.add_flow(datapath, 1, match, actions)

    # Get the MAC affress of a specified host
    def get_host_mac(self, hname):
        # Find the MAC address by iterating through the mac_to_host table
        for mac, host in self.mac_to_host.items():
            if host == hname:
                return mac
        return None

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        # Handle the Packet-In event from switches
        msg = ev.msg
        datapath = msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        # Ignore LLDP packets
        # LLDP (Link Layer Discovery Protocol) packets are used for topology discovery
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        # Flood ARP packets
        # ARP (Address Resolution Protocol) requests and replies are broadcast to all ports
        # Ensures MAC address resolution in the network
        pkt_arp = pkt.get_protocol(arp.arp)
        if pkt_arp is not None:
            if pkt_arp.opcode == arp.ARP_REQUEST or pkt_arp.opcode == arp.ARP_REPLY:
                actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
                out = parser.OFPPacketOut(datapath=datapath,
                                          buffer_id=ofproto.OFP_NO_BUFFER,
                                          in_port=in_port,
                                          actions=actions,
                                          data=msg.data)
                datapath.send_msg(out)
            return

        return