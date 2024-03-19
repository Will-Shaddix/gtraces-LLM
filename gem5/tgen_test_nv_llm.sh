for IR in 20 #10 20 50
do
    for RD in  50 #100 50 #0 
    do
        for tgen in 16 #16 32
        do
            for mem in LLM DDR HBM
            do
            # command line inputs: traffic_pattern(linear or random) RD% Memory_Type(LLM,LL-NVM, LL-NVM3) #_of_traffic_generators length_of_simulation injection_rate mem_size(in GiB) num_of_mem_channels
            # build/X86/gem5.opt --outdir=tgen_test_res/no_xbar/linear/LLM/IR$IR/RD$RD/tgen$tgen -re tgen_test.py linear $RD LLM $tgen 10000us $IR 8 2
            # build/X86/gem5.opt --outdir=tgen_test_res/no_xbar/random/LLM/IR$IR/RD$RD/tgen$tgen -re tgen_test.py random $RD LLM $tgen 10000us $IR 8 2
            
                build/X86/gem5.opt --outdir=m5out/mem_comp/$mem/IR$IR/RD$RD/tgen$tgen -re tgen_test_no_xbar.py random $RD $mem $tgen 100000us $IR 8 1 &

            # build/X86/gem5.opt --outdir=tgen_test_res/linear/LLM/IR$IR/RD$RD/tgen$tgen -re tgen_test.py linear $RD LLM $tgen 5000us $IR 8 2
            # # build/X86/gem5.opt --outdir=tgen_test_res/linear/LL_NVM/IR$IR/RD$RD/tgen$tgen -re tgen_test.py linear $RD LL-NVM $tgen 10000us $IR 8 2
            # # build/X86/gem5.opt --outdir=tgen_test_res/linear/LL_NVM3/IR$IR/RD$RD/tgen$tgen -re tgen_test.py linear $RD LL-NVM3 $tgen 10000us $IR 8 2
            # build/X86/gem5.opt --outdir=tgen_test_res/linear/LL_NVM_based/IR$IR/RD$RD/tgen$tgen -re tgen_test.py linear $RD LL-NVM-based $tgen 5000us $IR 8 2
            # build/X86/gem5.opt --outdir=tgen_test_res/linear/LL_NVM_based2/IR$IR/RD$RD/tgen$tgen -re tgen_test.py linear $RD LL-NVM-based2 $tgen 5000us $IR 8 2

            # build/X86/gem5.opt --outdir=tgen_test_res/random/LLM/IR$IR/RD$RD/tgen$tgen -re tgen_test.py random $RD LLM $tgen 5000us $IR 8 2
            # # build/X86/gem5.opt --outdir=tgen_test_res/random/LL_NVM/IR$IR/RD$RD/tgen$tgen -re tgen_test.py random $RD LL-NVM $tgen 10000us $IR 8 2
            # # build/X86/gem5.opt --outdir=tgen_test_res/random/LL_NVM3/IR$IR/RD$RD/tgen$tgen -re tgen_test.py random $RD LL-NVM3 $tgen 10000us $IR 8 2
            # build/X86/gem5.opt --outdir=tgen_test_res/random/LL_NVM_based/IR$IR/RD$RD/tgen$tgen -re tgen_test.py random $RD LL-NVM-based $tgen 5000us $IR 8 2

            done
        done
    done
done