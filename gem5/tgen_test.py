from m5.objects import *
from m5.util.convert import *
from m5.util import addToPath
import m5
import argparse
from m5.objects.DRAMInterface import *
from m5.objects.NVMInterface import *
from math import log
import math

def interleave_addresses(dram_class, num_chnl, intlv_size, start, size):

    num_chnls = num_chnl
    intlv_bits = int(math.log(num_chnls, 2))
    cache_line_size = 64
    intlv_low_bit = int(math.log(cache_line_size, 2))
    ret_list = []

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
    "mem_type",
    type=str,
    help="LLM or LL_NVM_PCM or LL_NVM_PCM_3 or LL_NVM_PCM2",
)

args.add_argument(
    "num_tgens",
    type=int,
    help="number of traffic generators",
)

args.add_argument('duration', type = str,
                    help = '''real time duration to generate traffic
                    e.g. 1s, 1ms, 1us, 1ns''')

args.add_argument('injection_rate', type = int,
                    help = '''The amount of traffic generated
                    by the traffic generator in GBps''')

args.add_argument(
    'mem_size', 
    type = int,
    help = '''The memory size in GB'''
)

args.add_argument(
    'num_chnls', 
    type = int,
    help = '''Number of  memory channels'''
)

options = args.parse_args()

options.unified_queue = 0

options.duration = int(toLatency(options.duration) * 1e12)

options.block_size = 64

injection_period = int((1e12 * options.block_size) /
                    (options.injection_rate * 1073741824))
options.min_period = injection_period
options.max_period = injection_period

bpc = 16
num_LLM_chnls = options.num_chnls * bpc
num_chnls = options.num_chnls

mem_sizes = options.mem_size
mem_ranges = interleave_addresses(LLM, num_LLM_chnls, 64, 0, str(options.mem_size) + 'GiB')


system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "5GHz"
system.clk_domain.voltage_domain = VoltageDomain()
system.mem_mode = 'timing'

system.generators = [PyTrafficGen() for i in range(options.num_tgens)]


system.scheds = [MemScheduler(read_buffer_size = 1, write_buffer_size = 32, resp_buffer_size = 64, unified_queue = options.unified_queue, \
                        service_write_threshold = 100 - int(options.rd_prct)) ] #for i in range(num_chnls)]

system.mem_ctrlrs = [MemCtrl() for i in range(num_LLM_chnls)]


    
for i in range (0,num_LLM_chnls):
    # curr_mem = str(int( (i * 1024 * mem_sizes) / num_LLM_chnls)) + 'MiB'
    # next_mem = str(int(((i+1) * 1024 * mem_sizes) / num_LLM_chnls)) + 'MiB'
    #print(curr_mem, next_mem, i)
    # print(mem_ranges[i].start())
    
    # if(options.mem_type == "LLM"):
    #     system.mem_ctrlrs[i].dram =LLM(range=AddrRange(curr_mem, next_mem), in_addr_map=True, null=True)
    # if(options.mem_type == "LL-NVM"):
    #     system.mem_ctrlrs[i].dram =LL_NVM_PCM(range=AddrRange(curr_mem, next_mem), in_addr_map=True, null=True) 
    # if(options.mem_type == "LL-NVM2"):
    #     system.mem_ctrlrs[i].dram =LL_NVM_PCM_2(range=AddrRange(curr_mem, next_mem), in_addr_map=True, null=True) 
    # if(options.mem_type == "LL-NVM3"):
    #     system.mem_ctrlrs[i].dram =LL_NVM_PCM_3(range=AddrRange(curr_mem, next_mem), in_addr_map=True, null=True) 
    if(options.mem_type == "LLM"):
        system.mem_ctrlrs[i].dram =LLM(range=mem_ranges[i], in_addr_map=True, null=True)
    if(options.mem_type == "LL-NVM-based"):
        system.mem_ctrlrs[i].dram =LL_NVM_PCM_based(range=mem_ranges[i], in_addr_map=True, null=True)
    if(options.mem_type == "LL-NVM-based2"):
        system.mem_ctrlrs[i].dram =LL_NVM_PCM_based2(range=mem_ranges[i], in_addr_map=True, null=True)
    if(options.mem_type == "LL-NVM"):
        system.mem_ctrlrs[i].dram =LL_NVM_PCM(range=mem_ranges[i], in_addr_map=True, null=True) 
    if(options.mem_type == "LL-NVM2"):
        system.mem_ctrlrs[i].dram =LL_NVM_PCM_2(range=mem_ranges[i], in_addr_map=True, null=True) 
    if(options.mem_type == "LL-NVM3"):
        system.mem_ctrlrs[i].dram =LL_NVM_PCM_3(range=mem_ranges[i], in_addr_map=True, null=True) 

    system.scheds[0].mem_side = system.mem_ctrlrs[i].port
            
        
# main memory


# system.membus = L2XBar(width=64)
system.membus = IOXBar(width=64)

system.membus.frontend_latency = 1
system.membus.response_latency  = 1
#system.membus.max_routing_table_size = 90000




#for i in range(options.num_chnls):
system.scheds[0].cpu_side = system.membus.mem_side_ports 

for generator in system.generators:
    generator.port = system.membus.cpu_side_ports


def createRandomTraffic(tgen, tgen_options):
    yield tgen.createRandom(tgen_options.duration,  # duration getting rid of 2 0's
                            0,                      # min_addr
                            AddrRange(str(options.mem_size) + 'GiB').end,  # max_addr
                            tgen_options.block_size,                     # block_size
                            tgen_options.min_period,                   # min_period was 10
                            tgen_options.max_period,                   # max_period was 10
                            tgen_options.rd_prct,        # rd_perc
                            0)                      # data_limit
    yield tgen.createExit(0)

def createLinearTraffic(tgen, tgen_options):
    yield tgen.createLinear(tgen_options.duration,  # duration 
                            0,                      # min_addr
                            AddrRange(str(options.mem_size) + 'GiB').end,  # max_addr
                            tgen_options.block_size,# block_size
                            tgen_options.min_period,# min_period was 10
                            tgen_options.max_period,# max_period
                            tgen_options.rd_prct,   # rd_perc
                            0)                      # data_limit
    yield tgen.createExit(0)
    
def createStridedTraffic(tgen, tgen_options):
    yield tgen.createStrided(tgen_options.duration,            # duration 
                            0,                      # min_addr
                            AddrRange('3GiB').end,  # max_adr
                            64,                     # block_size
                            10000,                   # min_period was 1000
                            10000,                   # max_period
                            tgen_options.rd_prct,        # rd_perc
                            0)                      # data_limit
    yield tgen.createExit(0)

root = Root(full_system=False, system=system)

m5.instantiate()

if options.traffic_mode == 'linear':
    for generator in system.generators:
    # system.generator.start(createLinearTraffic(system.generator))
        generator.start(createLinearTraffic(generator, options))
elif options.traffic_mode == 'random':
    #system.generator.start(createRandomTraffic(system.generator))
    for generator in system.generators:
        generator.start(createRandomTraffic(generator, options))
else:
    print('Wrong traffic type! Exiting!')
    exit()

exit_event = m5.simulate()
print(f"Exit reason {exit_event.getCause()}")


