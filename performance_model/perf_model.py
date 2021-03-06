
from __future__ import division

__copyright__ = "Copyright (C) 2015 James Stevens"

__license__ = """
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

# Citations #
# Initial performance model is from the following paper:
# Hong, Kim, 2009,
#       "An analytical model for a gpu architecture
#        with memory-level and thread-level parallelism awareness,"

# parameters from Table 1 in Hong Kim paper

import math


class GPUStats(object):

    # threads_per_warp:           number of threads per warp
    # issue_cycles:               number of cycles to execute one instruction
    # sm_clock_freq:              clock frequency of SMs (GHz), renamed from "Freq"
    # mem_bandwidth:              bandwidth between DRAM and GPU cores (GB/s)
    # roundtrip_DRAM_access_latency: DRAM access latency (Mem_LD) (?cycles)
    # departure_del_coal:         delay between two coalesced mem trans (?cycles)
    # departure_del_uncoal:       delay between two uncoalesced mem trans (?cycles)
    # mem_trans_per_warp_coal:    number of coalsced mem trans per warp
    # mem_trans_per_warp_uncoal:  number of uncoalsced mem trans per warp

    def __init__(self, gpu_name):
        if (gpu_name == 'GTX280'):
            self.threads_per_warp = 32
            self.issue_cycles = 4  # ?
            self.sm_clock_freq = 1.3
            self.mem_bandwidth = 141.7
            self.roundtrip_DRAM_access_latency = 450
            self.departure_del_coal = 4
            self.departure_del_uncoal = 40
            self.mem_trans_per_warp_coal = 1
            self.mem_trans_per_warp_uncoal = 5.7  # see technical report??
            self.SM_count = 30
            self.max_threads_per_SM = 1024
            self.max_blocks_per_SM = 8
        elif (gpu_name == 'FX5600'):
            self.threads_per_warp = 32  # Table 1
            self.issue_cycles = 4  # Table 1
            self.sm_clock_freq = 1.35  # Table 3
            self.mem_bandwidth = 76.8  # Table 3
            self.roundtrip_DRAM_access_latency = 420  # Table 6
            self.departure_del_coal = 4  # Table 6
            self.departure_del_uncoal = 10  # Table 6
            self.mem_trans_per_warp_coal = 1  # Table 3
            self.mem_trans_per_warp_uncoal = 32  # Table 3
            self.SM_count = 16  # Table 3

            self.max_blocks_per_SM = 8
            self.max_threads_per_SM = 768
            self.max_warps_per_SM = 24
            self.reg32_per_SM = 8192
            self.reg_alloc_unit_size = 256
            self.reg_alloc_granularity = 'block'
            self.shared_mem_per_SM = 16384
            self.shared_mem_alloc_size = 512
            self.warp_alloc_granularity = 2

        elif (gpu_name == 'HKexample'):
            self.threads_per_warp = 32
            self.issue_cycles = 4
            self.sm_clock_freq = 1.0
            self.mem_bandwidth = 80
            self.roundtrip_DRAM_access_latency = 420
            self.departure_del_coal = 1
            self.departure_del_uncoal = 10
            self.mem_trans_per_warp_coal = 1
            self.mem_trans_per_warp_uncoal = 32
            self.SM_count = 16
            self.max_threads_per_SM = 1024
            self.max_blocks_per_SM = 8
        elif (gpu_name == 'TeslaK20'):
            self.threads_per_warp = 32
            self.issue_cycles = 4
            self.sm_clock_freq = 0.706
            self.mem_bandwidth = 208

            #TODO correct this:
            self.roundtrip_DRAM_access_latency = 230  # 230 from Kumar, 2014

            #TODO correct this:
            self.departure_del_coal = 1  # from Krishnamani, Clemson U, 2014, for K20

            #TODO correct this:
            self.departure_del_uncoal = 38

            self.mem_trans_per_warp_coal = 1  # TODO Is this correct?
            self.mem_trans_per_warp_uncoal = 32  # TODO check on this
            self.SM_count = 13

            self.max_blocks_per_SM = 16
            self.max_threads_per_SM = 2048 
            self.max_warps_per_SM = 64
            self.reg32_per_SM = 65536
            self.reg_alloc_unit_size = 256
            self.reg_alloc_granularity = 'warp'
            self.shared_mem_per_SM = 49152
            self.shared_mem_alloc_size = 256
            self.warp_alloc_granularity = 4
        elif (gpu_name == 'TeslaC2070'):
            self.threads_per_warp = 32
            self.issue_cycles = 4  # TODO what is this again?
            self.sm_clock_freq = 1.15
            self.mem_bandwidth = 144

            #TODO correct this:
            self.roundtrip_DRAM_access_latency = 400  #TODO just guessed

            #TODO correct this:
            self.departure_del_coal = 1  # TODO Is this correct??

            #TODO correct this:
            self.departure_del_uncoal = 38  # TODO Is this correct?

            self.mem_trans_per_warp_coal = 1  # TODO Is this correct?
            self.mem_trans_per_warp_uncoal = 32  # TODO check on this
            self.SM_count = 56

            # for occupancy
            self.max_blocks_per_SM = 8
            self.max_threads_per_SM = 1536 
            self.max_warps_per_SM = 48
            self.reg32_per_SM = 65536
            self.reg_alloc_unit_size = 64
            self.reg_alloc_granularity = 'warp'
            self.shared_mem_per_SM = 49152
            self.shared_mem_alloc_size = 128
            self.warp_alloc_granularity = 2
        else:
            print "Error: unknown hardware"
        #TODO use compute capability to get some of these numbers


def round_int_up_to(n, precision):
    return math.ceil(n/precision)*precision

def round_int_down_to(n, precision):
    return math.floor(n/precision)*precision

def get_occupancy_blocks(gstats, threads_per_block, reg32_per_thread,
                         shared_mem_per_block):
    effective_warps_per_block = math.ceil(threads_per_block/gstats.threads_per_warp)
    effective_threads_per_block = effective_warps_per_block*gstats.threads_per_warp
    if gstats.reg_alloc_granularity == 'block':
        effective_reg32_per_block = round_int_up_to(reg32_per_thread*
                                        gstats.threads_per_warp*
                                        round_int_up_to(effective_warps_per_block,
                                        gstats.warp_alloc_granularity), gstats.reg_alloc_unit_size)

    if threads_per_block == 0:
        limit_by_warps = gstats.max_blocks_per_SM
    else:
        limit_by_warps = math.floor(gstats.max_warps_per_SM/
                                    effective_warps_per_block)
    if reg32_per_thread == 0:
        limit_by_regs = gstats.max_blocks_per_SM
    else:
        if gstats.reg_alloc_granularity == 'block':
            limit_by_regs = math.floor(gstats.reg32_per_SM/effective_reg32_per_block)
        elif gstats.reg_alloc_granularity == 'warp':
            limit_by_regs = math.floor( round_int_down_to(
                            gstats.reg32_per_SM/round_int_up_to(
                            reg32_per_thread*gstats.threads_per_warp,
                            gstats.reg_alloc_unit_size),
                            gstats.warp_alloc_granularity)/
                            effective_warps_per_block )
        else:
            print "todo print error here"
    if shared_mem_per_block == 0:
        limit_by_shared_mem = gstats.max_blocks_per_SM
    else:
        limit_by_shared_mem = math.floor(gstats.shared_mem_per_SM/
                                         round_int_up_to(shared_mem_per_block,
                                         gstats.shared_mem_alloc_size))
    return min(limit_by_warps, limit_by_regs, limit_by_shared_mem,
               gstats.max_blocks_per_SM)


class KernelStats(object):

    # comp_instructions:        total dynamic # of computation ins'ns per thread
    # mem_instructions_uncoal:  # of uncoalesced memory instructions per thread
    # mem_instructions_coal:    number of coalesced memory instructions per thread
    # synch_instructions:       total dynamic # of synch instructions per thread
    # mem_insns_total:         mem_instructions_uncoal + mem_instructions_coal
                        #TODO paper does not explain this, make sure it's correct
    # total_instructions:       comp_instructions + mem_insns_total

    def __init__(self, comp_instructions, mem_instructions_uncoal,
                 mem_instructions_coal, synch_instructions,
                 reg32_per_thread=None,
                 shared_mem_per_block=None):
        self.comp_instructions = comp_instructions
        self.mem_instructions_uncoal = mem_instructions_uncoal
        self.mem_instructions_coal = mem_instructions_coal
        self.synch_instructions = synch_instructions
        self.mem_insns_total = mem_instructions_uncoal + mem_instructions_coal
        self.total_instructions = comp_instructions + self.mem_insns_total
        self.reg32_per_thread = reg32_per_thread
        self.shared_mem_per_block = shared_mem_per_block

    def __str__(self):
        return "\ncomp_insns: " + str(self.comp_instructions) + \
               "\nmem_insns_uncoal: " + str(self.mem_instructions_uncoal) + \
               "\nmem_insns_coal: " + str(self.mem_instructions_coal) + \
               "\nmem_insns_total: " + str(self.mem_insns_total) + \
               "\nsynch_insns: " + str(self.synch_instructions) + \
               "\ntotal_insns: " + str(self.total_instructions) + \
               "\nreg32_per_thread: " + str(self.reg32_per_thread) + \
               "\nshared_mem_per_block: " + str(self.shared_mem_per_block)


class ThreadConfig(object):
    def __init__(self, threads_per_block, blocks):
        self.threads_per_block = threads_per_block
        self.blocks = blocks


class PerfModel(object):

    def __init__(self, GPU_stats, kernel_stats, thread_config, dtype,
                 active_blocks=None):
        self.GPU_stats = GPU_stats
        self.kernel_stats = kernel_stats
        self.thread_config = thread_config
        data_size = dtype.itemsize

        # Calculate number of bytes loaded by full warp
        self.load_bytes_per_warp = GPU_stats.threads_per_warp * data_size

        # Determine # of blocks that can run simultaneously on one SM
        #TODO calculate this correctly figuring in register/shared mem usage
        if active_blocks is None:
            if self.kernel_stats.reg32_per_thread is None:
                print "TODO insert appropriate warning here (estimating reg usage)"
                self.kernel_stats.reg32_per_SM = 7
            if self.kernel_stats.shared_mem_per_block is None:
                print "TODO insert appropriate warning here (estimating reg usage)"
                self.kernel_stats.shared_mem_per_thread = 0
            self.active_blocks_per_SM = get_occupancy_blocks(self.GPU_stats,
                                            self.thread_config.threads_per_block,
                                            self.kernel_stats.reg32_per_thread,
                                            self.kernel_stats.shared_mem_per_block)
        else:
            self.active_blocks_per_SM = active_blocks
        #print("DEBUGGING... self.active_blocks_per_SM: ", self.active_blocks_per_SM)

        # Determine number of active SMs
        # active_SMs == SM_count, unless we have a very small number of blocks
        self.active_SMs = min(math.ceil(
                            thread_config.blocks/self.active_blocks_per_SM),
                            GPU_stats.SM_count)  # TODO floor or ceil?

        # Calculate number of active warps per SM
        self.active_warps_per_SM = self.active_blocks_per_SM*math.ceil(
                                    thread_config.threads_per_block /
                                    GPU_stats.threads_per_warp)


    def compute_total_cycles(self):

        # time (cycles) per warp spent on uncoalesced mem transactions
        mem_l_uncoal = self.GPU_stats.roundtrip_DRAM_access_latency + (
                       self.GPU_stats.mem_trans_per_warp_uncoal - 1) * \
                       self.GPU_stats.departure_del_uncoal

        # time (cycles) per warp spent on coalesced mem transactions
        mem_l_coal = self.GPU_stats.roundtrip_DRAM_access_latency

        if self.kernel_stats.mem_insns_total != 0:

            # percent of mem transactions that are uncoalesced
            weight_uncoal = self.kernel_stats.mem_instructions_uncoal/(
                            self.kernel_stats.mem_insns_total)

            # percent of mem transactions that are coalesced
            weight_coal = self.kernel_stats.mem_instructions_coal/(
                          self.kernel_stats.mem_insns_total)
        else:
            weight_uncoal = 0.
            weight_coal = 0.

        # weighted average of mem latency (cycles) per warp
        mem_l = mem_l_uncoal * weight_uncoal + mem_l_coal * weight_coal

        # "minimum departure distance between two consecutive memory warps" -HK
        # (cycles)
        departure_delay = self.GPU_stats.departure_del_uncoal * \
                          self.GPU_stats.mem_trans_per_warp_uncoal * \
                          weight_uncoal + self.GPU_stats.departure_del_coal * \
                          weight_coal

        if departure_delay != 0:
            # "If the number of active warps is less than MWP_Without_BW_full,
            # the processor does not have enough number of warps to utilize
            # memory level parallelism"
            mwp_without_bw_full = mem_l/departure_delay
            #mwp_without_bw_full = round(mwp_without_bw_full, 2)
        else:
            mwp_without_bw_full = 0

        mwp_without_bw = min(mwp_without_bw_full, self.active_warps_per_SM)

        # memory cycles per warp
        mem_cycles = mem_l_uncoal * self.kernel_stats.mem_instructions_uncoal  \
                    + mem_l_coal * self.kernel_stats.mem_instructions_coal

        # computation cycles per warp
        comp_cycles = self.GPU_stats.issue_cycles * \
                      self.kernel_stats.total_instructions

        # active warps per SM TODO: forget n
        n = self.active_warps_per_SM

        # how many times does an SM execute active_blocks_per_SM blocks?
        if self.active_blocks_per_SM != 0 and self.active_SMs != 0:
            self.reps_per_SM = math.ceil(self.thread_config.blocks/(
                        self.active_blocks_per_SM * self.active_SMs))
            # TODO added ceil above^, is that right?
        else:
            self.reps_per_SM = 0

        #print " ", self.reps_per_SM, self.thread_config.blocks, self.active_blocks_per_SM, self.active_SMs

        # bandwidth per warp (GB/second)
        if mem_l != 0:
            bw_per_warp = self.GPU_stats.sm_clock_freq * \
                          self.load_bytes_per_warp/mem_l
            #bw_per_warp = round(bw_per_warp, 3)
        else:
            bw_per_warp = 0

        # max memory warp parallelism (warps/SM) based on peak mem bandwidth
        if bw_per_warp != 0 and self.active_SMs != 0:
            mwp_peak_bw = self.GPU_stats.mem_bandwidth/(
                          bw_per_warp * self.active_SMs)
            #mwp_peak_bw = round(mwp_peak_bw, 2)
        else:
            mwp_peak_bw = 0

        # Memory Warp Parallelism (MWP)
        # MWP: # of memory warps per SM that can be handled during mem_L cycles
        # MWP is minimum of three quantities:
        #  mwp_peak_bw: maximum number of warps based on peak mem bandwidth
        #  mwp_without_bw: if peak bw not reached,
        #                  MWP is function of mem_l and departure_delay
        #  n: maximum number of active warps per SM based on machine resources
        #     like register usage, shared memory usage, etc.
        self.MWP = min(mwp_without_bw, mwp_peak_bw, n)
        #print " ", mwp_without_bw, mwp_peak_bw, n
        # TODO n already incorporated above
        #self.MWP = round(self.MWP, 2)

        # total cycles (per warp) / computation cycles (per warp)
        # = max computation warp parallelism
        if comp_cycles != 0:
            cwp_full = (mem_cycles + comp_cycles)/comp_cycles
            #cwp_full = round(cwp_full, 2)
        else:
            cwp_full = 0

        # CWP cannot be greater than the max number of active warps per SM
        self.CWP = min(cwp_full, n)
        if (self.MWP == n) and (self.CWP == n):
            if self.kernel_stats.mem_insns_total != 0:
                exec_cycles_app = (mem_cycles + comp_cycles +
                                  comp_cycles/self.kernel_stats.mem_insns_total *
                                  (self.MWP-1))*self.reps_per_SM
            else:
                exec_cycles_app = 0
        elif (self.CWP >= self.MWP) or (comp_cycles > mem_cycles):
            if self.kernel_stats.mem_insns_total != 0 and self.MWP != 0:
                exec_cycles_app = (mem_cycles * n/self.MWP +
                                  comp_cycles/self.kernel_stats.mem_insns_total *
                                  (self.MWP-1))*self.reps_per_SM
            else:
                exec_cycles_app = 0
            #print "<debugging> ", mem_cycles, n, self.MWP
            #print "<debugging> ", comp_cycles, self.kernel_stats.mem_insns_total,
            #print "<debugging> ", self.MWP, self.reps_per_SM
        else:  # (self.MWP > self.CWP)
            exec_cycles_app = (mem_l + comp_cycles * n)*self.reps_per_SM

        # compute cost of synchronization instructions
        synch_cost_old = departure_delay * (self.MWP-1) *  \
                         self.kernel_stats.synch_instructions * \
                         self.active_blocks_per_SM*self.reps_per_SM
        active_warps_per_block = math.ceil(self.thread_config.threads_per_block /
                                 self.GPU_stats.threads_per_warp)
        # NpWB = num. parallel warps per block (introduced in HK tech report?)
        NpWB = min(self.MWP, active_warps_per_block)
        synch_cost = departure_delay * (NpWB-1) *  \
                         self.kernel_stats.synch_instructions * \
                         self.active_blocks_per_SM*self.reps_per_SM

        # compute CPI (cycles per instruction) just to see what it is
        if self.GPU_stats.threads_per_warp != 0 and self.active_SMs != 0 \
                           and self.kernel_stats.total_instructions != 0:
            self.CPI = exec_cycles_app/(self.kernel_stats.total_instructions *
                       math.ceil(self.thread_config.threads_per_block /
                        self.GPU_stats.threads_per_warp) *
                       (self.thread_config.blocks/self.active_SMs))
            # TODO added ceil^, is this right?
        else:
            self.CPI = 0

        self.occ = n*(self.GPU_stats.threads_per_warp /
                      self.GPU_stats.max_threads_per_SM)
        '''
        print "<debug> mem_ld: ", self.GPU_stats.roundtrip_DRAM_access_latency
        print "<debug> departure_del_uncoal: ", self.GPU_stats.departure_del_uncoal
        print "<debug> threads_per_block: ", self.thread_config.threads_per_block
        print "<debug> blocks: ", self.thread_config.blocks
        print "<debug> active_blocks_per_sm: ", self.active_blocks_per_SM
        print "<debug> active_sms: ", self.active_SMs
        print "<debug> active_warps_per_sm: ", self.active_warps_per_SM
        print "<debug> comp_insts: ", self.kernel_stats.comp_instructions
        print "<debug> uncoal_mem_insts: ", self.kernel_stats.mem_instructions_uncoal
        print "<debug> coal_mem_insts: ", self.kernel_stats.mem_instructions_coal
        print "<debug> synch_insts: ", self.kernel_stats.synch_instructions
        print "<debug> mem_trans_per_warp_coal: ", self.GPU_stats.mem_trans_per_warp_coal  # noqa
        print "<debug> mem_trans_per_warp_uncoal: ", self.GPU_stats.mem_trans_per_warp_uncoal  # noqa
        print "<debug> load_bytes_per_warp: ", self.load_bytes_per_warp
        print "<debug> departure_delay: ", departure_delay
        print "<debug> mem_l: ", mem_l
        print "<debug> mwp_without_bw_full: ", mwp_without_bw_full
        print "<debug> bw_per_warp: ", bw_per_warp
        print "<debug> mwp_peak_bw: ", mwp_peak_bw
        print "<debug> MWP: ", self.MWP
        print "<debug> comp_cycles: ", comp_cycles
        print "<debug> mem_cycles: ", mem_cycles
        print "<debug> CWP_full: ", cwp_full
        print "<debug> CWP: ", self.CWP
        print "<debug> rep: ", self.reps_per_SM
        print "<debug> exec_cycles_app: ", exec_cycles_app
        print "<debug> synch_cost: ", synch_cost
        print "<debug> CPI: ", self.CPI
        '''
        return exec_cycles_app+synch_cost


