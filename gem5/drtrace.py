import m5
import argparse
import math
from m5.objects import *

"""
Usage:
------

```
./build/X86/gem5.opt \
    drtrace.py \
    --path <path of folder containing all traces> \
    --workload <benchmark_name> \
    --players <Number of players to use> \
    --dram <DRAM device to use>
```
"""

parser = argparse.ArgumentParser(
    description="A script to run google traces."
)

benchmark_choices = ["charlie", "delta", "merced", "whiskey"]

parser.add_argument(
    "--path",
    type=str,
    required=True,
    help="Main directory containing the traces.",
)

parser.add_argument(
    "--workload",
    type=str,
    required=True,
    help="Input the benchmark program to execute.",
    choices=benchmark_choices,
)

parser.add_argument(
    "--players",
    type=int,
    required=True,
    help="Input the number of players to use.",
)

parser.add_argument(
    "--dram",
    type = str,
    help = "Memory device to use"
)

parser.add_argument(
    "--unified-queue",
    type = int,
    help = "Is LLM unified? 1 for yes, 0 for no"
)

parser.add_argument(
    "--RoRaBaChCo",
    type = int,
    help = "Doess LLM have RoRaBaChCo? 1 for yes, 0 for no"
)

parser.add_argument(
    "--intlv",
    type = int,
    help = "Is LLM interleaved? 1 for yes, 0 for no"
)

args = parser.parse_args()


MemTypes = {
    'DDR4' : DDR4_2400_16x4,
    'HBM' : HBM_2000_4H_1x64,
    # 'ddr5_8400' : DDR5_8400_4x8,
    'LLM' : LLM
}

def get_mem_ranges(num_chnls, mem_size):
    cache_line_size = 64
    prev = 0 
    next = int(mem_size / num_chnls)
    size = next
    mem_ranges = []
    for i in range(num_chnls):
        mem_ranges.append(AddrRange(start = prev, end = next))
        prev = next
        next = next + size
        
    return mem_ranges

def get_intlv_memory(mem_type, addr_map):
    cache_line_size = 64
    intlv_size = cache_line_size
    cls = mem_type

    print(cls)
    print(cls.device_rowbuffer_size)

    if addr_map == 'RoRaBaChCo':
        rowbuffer_size = cls.device_rowbuffer_size.value * \
                        cls.devices_per_rank.value
        intlv_low_bit = int(math.log(rowbuffer_size, 2))
        print("low bit", intlv_low_bit)
    else:
        intlv_low_bit = int(math.log(intlv_size, 2))
    intlv_bits = intlv_bits = int(math.log(num_chnls, 2))
    
    return intlv_low_bit, intlv_bits

system = System()

system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "3GHz"
system.clk_domain.voltage_domain = VoltageDomain()

# Set up the system
system.mem_mode = "timing"  # Use timing accesses
system.mem_ranges = [AddrRange("8GiB")]  # Create an address range

if args.dram == 'HBM':
    system.mem_ctrl = HBMCtrl()
    system.mem_ctrl.dram = MemTypes[args.dram](range=AddrRange(start = '0', end = '8GiB', masks = [1 << 6], intlvMatch = 0))
    system.mem_ctrl.dram_2 = MemTypes[args.dram](range=AddrRange(start = '0', end = '8GiB', masks = [1 << 6], intlvMatch = 1))
elif args.dram == 'LLM':
    system.mem_scheduler = MemScheduler(read_buffer_size = 16, write_buffer_size = 32, resp_buffer_size = 64, unified_queue = args.unified_queue, \
                            service_write_threshold = 80)
    system.mem_ctrls = [MemCtrl() for i in range(64)]
    my_mem_ranges = get_mem_ranges(64, 8 * 1024 * 1024 * 1024)
    print(my_mem_ranges)
    num_chnls = 64

    if args.RoRaBaChCo == 1:
        intlv_low_bit, intlv_bits = get_intlv_memory(MemTypes[args.dram], 'RoRaBaChCo')
        print("rorabachco", intlv_low_bit, intlv_bits)
    else:
        intlv_low_bit, intlv_bits = get_intlv_memory(MemTypes[args.dram], 'NA')

    for i, mem_ctrl in enumerate(system.mem_ctrls):
        if (args.intlv == 1):
            mem_ctrl.dram = MemTypes[args.dram](range=AddrRange(start = '0', end = '8GiB',  intlvHighBit = intlv_low_bit + intlv_bits - 1, xorHighBit = 0, intlvBits = intlv_bits, intlvMatch=i))
        else:
            mem_ctrl.dram = MemTypes[args.dram](range=my_mem_ranges.pop(0))
        mem_ctrl.dram.read_buffer_size = 16
        mem_ctrl.dram.write_buffer_size = 32
        mem_ctrl.write_high_thresh_perc = 100
        mem_ctrl.write_low_thresh_perc = 90
        mem_ctrl.min_writes_per_switch = 1
        mem_ctrl.mem_sched_policy = 'fcfs'
        mem_ctrl.dram.page_policy = 'close' 
        # mem_ctrl.dram.subarray_per_bank = 8
        
    # print(my_mem_ranges)
    
    
else:
    system.mem_ctrl = MemCtrl()
    system.mem_ctrl.dram = MemTypes[args.dram](range=system.mem_ranges[0])

players = args.players

system.reader = DRTraceReader(
    directory="{}/{}/".format(args.path, args.workload), num_players=args.players
)
system.players = [
    DRTracePlayer(
        reader=system.reader,
        send_data=True,
        compress_address_range=system.mem_ranges[0],
    )
    for _ in range(players)
]

system.xbar = SystemXBar()
if args.dram != 'LLM':
    system.xbar.mem_side_ports = system.mem_ctrl.port
else:
    system.xbar.mem_side_ports = system.mem_scheduler.cpu_side
    for mem_ctrl in system.mem_ctrls:
        mem_ctrl.port = system.mem_scheduler.mem_side


for player in system.players:
    player.max_ipc = 8
    player.max_outstanding_reqs = 8
    player.cache = Cache(
        size="32KiB",
        assoc=8,
        tag_latency=1,
        data_latency=1,
        response_latency=1,
        mshrs=16,
        tgts_per_mshr=8,
    )
    player.port = player.cache.cpu_side
    player.cache.mem_side = system.xbar.cpu_side_ports
root = Root(full_system=False, system=system)

m5.instantiate()

print("Beginning simulation!")
exit_event = m5.simulate(500000000000)
print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")
