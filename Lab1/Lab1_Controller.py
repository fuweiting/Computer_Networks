from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, ipv4, tcp

class NetworkPolicyController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(NetworkPolicyController, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # Default rule: drop all packets
        match = parser.OFPMatch()
        actions = []
        self.add_flow(datapath, 0, match, actions)
        
        # IP address of nodes A, B, C and D
        IA = '10.0.0.01'                 
        IB = '10.0.0.02'
        IC = '10.0.0.03'
        ID = '10.0.0.04'
        
        # Ethernet address of nodes A, B, C and D
        EA = '00:00:00:00:00:01'
        EB = '00:00:00:00:00:02'
        EC = '00:00:00:00:00:03'
        ED = '00:00:00:00:00:04'
        
        # Policy 1: Nodes A, B, and C can talk to one another freely.
        self.allow_communication(datapath, IA, EA, IB, EB)
        self.allow_communication(datapath, IB, EB, IC, EC)
        self.allow_communication(datapath, IA, EA, IC, EC)
        
        # Policy 2: Node D has access to ports 22 and 80 of Nodes A and B, but nothing else.
        self.allow_access(datapath, ID, ED, IA, EA, [22, 80])
        self.allow_access(datapath, ID, ED, IB, EB, [22, 80])
        
        # Policy 3: Node D and Node C cannot talk to each other.
        self.block_communication(datapath, ID, ED, IC, EC)
        
    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        if actions:
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        else:
            inst = []

        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match, instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    def allow_communication(self, datapath, ip_src, eth_src, ip_dst, eth_dst):
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(eth_type=0x0800, ipv4_src=ip_src, ipv4_dst=ip_dst,
                                eth_src=eth_src, eth_dst=eth_dst)
        actions = [parser.OFPActionOutput(datapath.ofproto.OFPP_NORMAL)]
        self.add_flow(datapath, 1, match, actions)

    def allow_access(self, datapath, ip_src, eth_src, ip_dst, eth_dst, ports):
        parser = datapath.ofproto_parser
        for port in ports:
            match = parser.OFPMatch(eth_type=0x0800, ipv4_src=ip_src, ipv4_dst=ip_dst,
                                    eth_src=eth_src, eth_dst=eth_dst, ip_proto=6, tcp_dst=port)
            actions = [parser.OFPActionOutput(datapath.ofproto.OFPP_NORMAL)]
            self.add_flow(datapath, 2, match, actions)

    def block_communication(self, datapath, ip_src, eth_src, ip_dst, eth_dst):
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(eth_type=0x0800, ipv4_src=ip_src, ipv4_dst=ip_dst,
                                eth_src=eth_src, eth_dst=eth_dst)
        actions = []  # No action means drop the packet
        self.add_flow(datapath, 3, match, actions)