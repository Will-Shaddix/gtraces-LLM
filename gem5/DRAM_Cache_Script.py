from m5.objects import *
import m5
import argparse
from m5.objects.DRAMInterface import *
#from m5.objects.DRAMAlloyInterface import *
from m5.objects.NVMInterface import *
from math import log
import math

def interleave_addresses(dram_class, num_chnl, intlv_size, start, size):
    # if dram_class.addr_mapping == "RoRaBaChCo":
    #     rowbuffer_size = (
    #         dram_class.device_rowbuffer_size.value
    #         * dram_class.devices_per_rank.value
    #     )
    #     intlv_low_bit = log(rowbuffer_size, 2)
    # elif dram_class.addr_mapping in ["RoRaBaCoCh", "RoCoRaBaCh"]:
    #     intlv_low_bit = log(intlv_size, 2)
    # else:
    #     raise ValueError(
    #         "Only these address mappings are supported: "
    #         "RoRaBaChCo, RoRaBaCoCh, RoCoRaBaCh"
    #     )

    # assert dram_class.addr_mapping == 'RoRaBaCoCh'

    # intlv_low_bit = log(intlv_size, 2)
    # intlv_bits = log(num_chnl, 2)
    # mask_list = []

    # for ib in range(int(intlv_bits)):
    #     mask_list.append(1 << int(ib + intlv_low_bit))
    num_chnls = num_chnl
    intlv_bits = int(math.log(num_chnls, 2))
    cache_line_size = 64
    intlv_low_bit = int(math.log(cache_line_size, 2))



    # # for interleaving across pseudo channels (at 64B currently)
    # mask_list.insert(0, 1 << 6)
    ret_list = []
    # for i in range(num_chnl):
    #     ret_list.append(AddrRange(
    #         start=start,
    #         size=size,
    #         masks=mask_list,
    #         intlvMatch=(i << 1) | 0,
    #     ))
    #     ret_list.append(AddrRange(
    #         start=start,
    #         size=size,
    #         masks=mask_list,
    #         intlvMatch=(i << 1) | 1,
    #     ))

    for i in range (num_chnl):
        ret_list.append(AddrRange( start=start,
             size=size,
             intlvHighBit = intlv_low_bit + intlv_bits - 1,
             intlvBits = intlv_bits, ##number of bits for interleaving 
             intlvMatch = i))

    return ret_list

args = argparse.ArgumentParser()

args.add_argument(
    "traffic_mode",
    type = str,
    help = "Traffic type to use"
)

args.add_argument(
    "rd_prct",
    type=int,
    help="Read Percentage",
)

args.add_argument(
    "hit",
    type=int,
    help="Read Percentage",
)

args.add_argument(
    "dirty",
    type=int,
    help="Read Percentage",
)

args.add_argument(
    "near_mem_type",
    type=str,
    help="NVM or DRAM",
)

args.add_argument(
    "far_mem_type",
    type=str,
    help="NVM or DRAM or LL_NVM_PCM or LL_NVM_PCM_3",
)

args.add_argument(
    "policy",
    type=str,
    help="Policy for Policy Manager",
)

options = args.parse_args()
options.num_near_chnls = 8

bpc = 32
num_LLM_chnls = options.num_near_chnls * bpc
num_chnls = options.num_near_chnls


system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "5GHz"
system.clk_domain.voltage_domain = VoltageDomain()
system.mem_mode = 'timing'

# system.generator = PyTrafficGen()
system.generators = [PyTrafficGen() for i in range(8)]



system.mem_ctrl = PolicyManager(range=AddrRange('3GiB'))#, loc_mem_policy=options.policy, NMT_Max_Entries=64000000)
system.mem_ctrl.tRP = '14.16ns'
system.mem_ctrl.tRCD_RD = '14.16ns'
system.mem_ctrl.tRL = '14.16ns'

system.membusPolManLocMem = L2XBar(width=64)
# system.membusPolManLocMem.frontend_latency = options.xbarLatency
# system.membusPolManLocMem.response_latency  = options.xbarLatency
# system.membusPolManLocMem.max_routing_table_size = 900000
system.membusPolManLocMem.cpu_side_ports = system.mem_ctrl.loc_req_port


# loc_ranges = ['0', '384MiB', '768MiB', '1152MiB', '1536MiB', '1920MiB', '2304MiB', '2688MiB', '3072MiB']

# system.loc_mem_ctrlrs = [HBMCtrl() for i in range(8)]
system.loc_mem_ctrlrs = [MemCtrl() for i in range(num_chnls)]


if(options.near_mem_type == "DRAM"):
    loc_ranges = interleave_addresses(DDR4_2400_16x4, options.num_near_chnls, 128, 0, '3GiB') # 3GB Local memory spread across 8 HBM Controllers and a DDR channel
    print("size of loc_Ranges: " + str(len(loc_ranges)))
    print("mhere")
    for i in range (0,8):
        system.loc_mem_ctrlrs[i].dram = DDR4_2400_16x4(range=loc_ranges[i], in_addr_map=False, null=True) # why the dram and dram_2?
        # system.loc_mem_ctrlrs[i].dram_2 = DDR4_2400_16x4(range=loc_ranges[2*i+1], in_addr_map=False, null=True)
        system.loc_mem_ctrlrs[i].port = system.membusPolManLocMem.mem_side_ports
        # system.loc_mem_ctrlrs.dram.read_buffer_size = 4
        # system.loc_mem_ctrlrs.dram.write_buffer_size = 4
        # system.loc_mem_ctrlrs.dram_2.read_buffer_size = 4
        # system.loc_mem_ctrlrs.dram_2.write_buffer_size = 4
elif(options.near_mem_type == "NVM"):
    loc_ranges = interleave_addresses(NVM_2400_1x64, 8, 128, 0, '3GiB') # 3GB Local memory spread across 8 HBM Controllers and a DDR channel
    print("size of loc_Ranges: " + str(len(loc_ranges)))
    print("mhere")
    for i in range (0,num_chnls):
        system.loc_mem_ctrlrs[i].dram =NVM_2400_1x64(range=loc_ranges[i], in_addr_map=False, null=True) # why the dram and dram_2?
        # system.loc_mem_ctrlrs[i].dram_2 = DDR4_2400_16x4(range=loc_ranges[2*i+1], in_addr_map=False, null=True)
        system.loc_mem_ctrlrs[i].port = system.membusPolManLocMem.mem_side_ports
    #system.far_mem_ctrl.dram = NVM_2400_1x64(range=AddrRange('3GiB'), in_addr_map=False, null=True)
elif(options.near_mem_type == "LLM"):
    loc_ranges = interleave_addresses(LLM, num_LLM_chnls, 128, 0, '3GiB') # 3GB Local memory spread across 8 HBM Controllers and a DDR channel
    print("size of loc_Ranges: " + str(len(loc_ranges)))
    print("mhere")
    for i in range (0,num_LLM_chnls):
        system.loc_mem_ctrlrs[i].dram =LLM(range=loc_ranges[i], in_addr_map=False, null=True) # why the dram and dram_2?
        # system.loc_mem_ctrlrs[i].dram_2 = DDR4_2400_16x4(range=loc_ranges[2*i+1], in_addr_map=False, null=True)
        system.loc_mem_ctrlrs[i].port = system.membusPolManLocMem.mem_side_ports
        
elif(options.near_mem_type == "LL_NVM_PCM"):
    loc_ranges = interleave_addresses(LL_NVM_PCM, 8, 128, 0, '3GiB') # 3GB Local memory spread across 8 HBM Controllers and a DDR channel
    print("size of loc_Ranges: " + str(len(loc_ranges)))
    print("mhere")
    for i in range (0,8):
        system.loc_mem_ctrlrs[i].dram =LL_NVM_PCM(range=loc_ranges[i], in_addr_map=False, null=True) # why the dram and dram_2?
        # system.loc_mem_ctrlrs[i].dram_2 = DDR4_2400_16x4(range=loc_ranges[2*i+1], in_addr_map=False, null=True)
        system.loc_mem_ctrlrs[i].port = system.membusPolManLocMem.mem_side_ports
        
elif(options.near_mem_type == "LL_NVM_PCM_3"):
    loc_ranges = interleave_addresses(LL_NVM_PCM_3, 8, 128, 0, '3GiB') # 3GB Local memory spread across 8 HBM Controllers and a DDR channel
    print("size of loc_Ranges: " + str(len(loc_ranges)))
    print("mhere")
    for i in range (0,8):
        system.loc_mem_ctrlrs[i].dram =LL_NVM_PCM_3(range=loc_ranges[i], in_addr_map=False, null=True) # why the dram and dram_2?
        # system.loc_mem_ctrlrs[i].dram_2 = DDR4_2400_16x4(range=loc_ranges[2*i+1], in_addr_map=False, null=True)
        system.loc_mem_ctrlrs[i].port = system.membusPolManLocMem.mem_side_ports
    #system.far_mem_ctrl.dram = NVM_2400_1x64(range=AddrRange('3GiB'), in_addr_map=False, null=True)
# main memory

print("right here")

# DRAM Main memory
# system.far_mem_ctrl = MemCtrl()
# system.far_mem_ctrl.dram = DDR3_1600_8x8(range=AddrRange('3GiB'), in_addr_map=False, null=True)
# system.far_mem_ctrl = [MemCtrl() for i in range(8)]



if(options.far_mem_type == "DRAM"):
    system.far_mem_ctrl = MemCtrl()
    system.far_mem_ctrl.dram = DDR3_1600_8x8(range=AddrRange('3GiB'), in_addr_map=False, null=True)

elif(options.far_mem_type == "NVM"):
    system.far_mem_ctrl = MemCtrl()
    system.far_mem_ctrl.dram = NVM_2400_1x64(range=AddrRange('3GiB'), in_addr_map=False, null=True)
elif(options.far_mem_type == "LLM"):
    system.far_mem_ctrl = MemCtrl()
    system.far_mem_ctrl.dram = LLM(range=AddrRange('3GiB'), in_addr_map=False, null=True)
        
elif(options.far_mem_type == "LL_NVM_PCM"):
    system.far_mem_ctrl = MemCtrl()
    system.far_mem_ctrl.dram = LL_NVM_PCM(range=AddrRange('3GiB'), in_addr_map=False, null=True)

        
elif(options.far_mem_type == "LL_NVM_PCM_3"):
    system.far_mem_ctrl = MemCtrl()
    system.far_mem_ctrl.dram = LL_NVM_PCM3(range=AddrRange('3GiB'), in_addr_map=False, null=True)
else:
    print("INVALID MEMORY TYPE: " + str(options.far_mem_type))


# system.far_mem_ctrl.dram_2 = HBM_2000_4H_1x64(range=AddrRange('3GiB'), in_addr_map=False, null=True)
# system.far_mem_ctrl.port = system.mem_ctrl.far_req_port
system.membusPolManFarMem = L2XBar(width=64)
system.membusPolManFarMem.cpu_side_ports = system.mem_ctrl.far_req_port
system.membusPolManFarMem.mem_side_ports = system.far_mem_ctrl.port
system.far_mem_ctrl.dram.read_buffer_size = 128
system.far_mem_ctrl.dram.write_buffer_size = 128

system.mem_ctrl.orb_max_size = 256
system.mem_ctrl.dram_cache_size = "128MiB"

if options.hit==1 :
    system.mem_ctrl.always_hit = True
else:
    system.mem_ctrl.always_hit = False

if options.dirty==1 :
    system.mem_ctrl.always_dirty = True
else:
    system.mem_ctrl.always_dirty = False

#system.generator.port = system.mem_ctrl.port
system.membus = L2XBar(width=64)
for generator in system.generators:
    #generator.port = system.mem_ctrl.port
    generator.port = system.membus.cpu_side_ports

system.membus.mem_side_ports = system.mem_ctrl.port

def createRandomTraffic(tgen):
    yield tgen.createRandom(900000000,            # duration getting rid of 2 0's
                            0,                      # min_addr
                            AddrRange('3GiB').end,  # max_adr
                            64,                     # block_size
                            200,                   # min_period was 10
                            200,                   # max_period was 10
                            options.rd_prct,        # rd_perc
                            0)                      # data_limit
    yield tgen.createExit(0)

def createLinearTraffic(tgen):
    yield tgen.createLinear(900000000,            # duration 
                            0,                      # min_addr
                            AddrRange('3GiB').end,  # max_adr
                            64,                     # block_size
                            10000,                   # min_period was 1000
                            10000,                   # max_period
                            options.rd_prct,        # rd_perc
                            0)                      # data_limit
    yield tgen.createExit(0)
    
def createStridedTraffic(tgen):
    yield tgen.createStrided(900000000,            # duration 
                            0,                      # min_addr
                            AddrRange('3GiB').end,  # max_adr
                            64,                     # block_size
                            10000,                   # min_period was 1000
                            10000,                   # max_period
                            options.rd_prct,        # rd_perc
                            0)                      # data_limit
    yield tgen.createExit(0)

root = Root(full_system=False, system=system)

m5.instantiate()

if options.traffic_mode == 'linear':
    for generator in system.generators:
    # system.generator.start(createLinearTraffic(system.generator))
        generator.start(createLinearTraffic(generator))
elif options.traffic_mode == 'random':
    #system.generator.start(createRandomTraffic(system.generator))
    for generator in system.generators:
        generator.start(createRandomTraffic(generator))
else:
    print('Wrong traffic type! Exiting!')
    exit()

exit_event = m5.simulate()
print(f"Exit reason {exit_event.getCause()}")


