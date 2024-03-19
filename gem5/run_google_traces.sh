#/bin/bash


# ./build/X86/gem5.opt drtrace.py  --path <path of folder containing all traces>  --workload <benchmark_name>  --players <Number of players to use> --dram <DRAM device to use>


# ./gem5/build/X86/gem5.opt --outdir=m5stats/gtraces/DDR -re gem5/drtrace.py --path ../../../data/google-traces/charlie --workload charlie --players 8 --dram ddr4_2400 &
# ./gem5/build/X86/gem5.opt --outdir=m5stats/gtraces/LLM -re gem5/drtrace.py --path ../../../data/google-traces/charlie --workload charlie --players 8 --dram LLM
# for num_players in 8 16 32 64 128 256
# do
#     # ./gem5/build/X86/gem5.opt --outdir=m5stats/gtraces/DDR4/players_$num_players -re gem5/drtrace.py --path ../../../data/google-traces/charlie --workload charlie --players $num_players --dram ddr4_2400 &
#     # ./gem5/build/X86/gem5.opt --outdir=m5stats/gtraces/DDR5/players_$num_players -re gem5/drtrace.py --path ../../../data/google-traces/charlie --workload charlie --players $num_players --dram ddr5_8400 &
#     # ./gem5/build/X86/gem5.opt --outdir=m5stats/gtraces/HBM2/players_$num_players -re gem5/drtrace.py --path ../../../data/google-traces/charlie --workload charlie --players $num_players --dram hbm_2000 &
#     ./gem5/build/X86/gem5.opt --outdir=m5stats/gtraces/LLM/players_$num_players -re gem5/drtrace.py --path ../../../data/google-traces/charlie --workload charlie --players $num_players --dram LLM
# done



for unified_queue in 1
do
    for interleave in 1
    do
        for RoRa in 1 0
        do
            for num_players in 48 #128
            do
                for mem in HBM DDR4
                do
                # ./build/X86/gem5.opt --outdir=m5stats/gtraces/LLM/players_$num_players/unified_queue_$unified_queue/interleave_$interleave/RoRa_$RoRa -re drtrace.py --path ../../../data/google-traces/charlie --workload charlie --players $num_players --dram LLM --unified-queue $unified_queue --intlv $interleave --RoRaBaChCo $RoRa
                    ./build/X86/gem5.opt --outdir=m5stats/gtraces/$mem/players_$num_players/unified_queue_$unified_queue/interleave_$interleave/RoRa_$RoRa -re drtrace.py --path ../../../../data/google-traces/charlie --workload charlie --players $num_players --dram $mem --unified-queue $unified_queue --intlv $interleave --RoRaBaChCo $RoRa &
                done
                for mem in LLM 
                do
                # ./build/X86/gem5.opt --outdir=m5stats/gtraces/LLM/players_$num_players/unified_queue_$unified_queue/interleave_$interleave/RoRa_$RoRa -re drtrace.py --path ../../../data/google-traces/charlie --workload charlie --players $num_players --dram LLM --unified-queue $unified_queue --intlv $interleave --RoRaBaChCo $RoRa
                    ./build/X86/gem5.opt --outdir=m5stats/gtraces/$mem/players_$num_players/unified_queue_$unified_queue/interleave_$interleave/RoRa_$RoRa -re drtrace.py --path ../../../../data/google-traces/charlie --workload charlie --players $num_players --dram $mem --unified-queue $unified_queue --intlv $interleave --RoRaBaChCo $RoRa
                done
            done
        done
    done
done
