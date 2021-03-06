from __future__ import division
import sys
sys.path.append("../performance_model")
from perf_model import GPUStats, KernelStats, ThreadConfig, PerfModel
import math
import numpy as np
import matplotlib.pyplot as plt
import loopy as lp
from loopy.statistics import estimate_regs_per_thread
'''
from pyopencl.tools import (  # noqa
        pytest_generate_tests_for_pyopencl
        as pytest_generate_tests)
'''
TOLERANCE = 0.001

def test_HK_example():
    gstats = GPUStats('HKexample')
    kstats = KernelStats(27, 6, 0, 6)
    tconfig = ThreadConfig(128, 80)
    model = PerfModel(gstats, kstats, tconfig, np.dtype(np.float32), active_blocks=5)
    expected = 50738
    print "total cycles: ", model.compute_total_cycles(), "expected: ~", expected

    expect_cwp = 20
    expect_mwp = 2.28

    print "CWP: ", model.CWP, "expected: ~", expect_cwp
    print "MWP: ", model.MWP, "expected: ~", expect_mwp
    #assert (abs(model.compute_total_cycles() - expected) / expected) < TOLERANCE


def test_HK_sepia():

    print "TESTING sepia..."

    # input size: 7000x7000
    n = 7000.
    gstats = GPUStats('FX5600')
    reg32_per_thread = 7
    shared_mem_per_block = 52
    kstats = KernelStats(71, 6, 0, 1, reg32_per_thread, shared_mem_per_block)  # TODO synch_insns=0 ?
    expected = 153

    trials = 17
    threads = [(x+6)*(x+6) for x in range(trials)]
    times = []
    occupancies = []
    CPIs = []
    CWPs = []
    MWPs = []
    print "blk sz\tactive\tocc\t\tcwp\t\tmwp\t\tcpi\t\ttime"
    for i in range(trials):
        #print " ", n*n/threads[i], math.ceil(n/(threads[i]**0.5))**2, n
        tconfig = ThreadConfig(threads[i], math.ceil(n/(threads[i]**0.5))**2)
        model = PerfModel(gstats, kstats, tconfig, np.dtype(np.float32))
        times.append(model.compute_total_cycles() /
                    (gstats.sm_clock_freq*(10**9))*(10**3))
        occupancies.append(model.occ)
        CPIs.append(model.CPI)
        CWPs.append(model.CWP)
        MWPs.append(model.MWP)
        print "%i\t%i\t%f\t%f\t%f\t%f\t%f" % (threads[i], model.active_blocks_per_SM,
                                              occupancies[i], CWPs[i], MWPs[i],
                                              CPIs[i], times[i])

    expect_avg_occ = 0.835
    expect_avg_cpi = 26
    expect_avg_cwp = 14
    expect_avg_mwp = 2

    print "\nexpected time (approx): ", expected
    print "\n\tactual (avg)\texpected (avg)\trel err"
    print "occ:\t%f\t%f\t%f" % (np.average(occupancies), expect_avg_occ, 
                    (np.average(occupancies)-expect_avg_occ)/expect_avg_occ)
    print "CPI:\t%f\t%f\t%f" % (np.average(CPIs), expect_avg_cpi, 
                    (np.average(CPIs)-expect_avg_cpi)/expect_avg_cpi)
    print "CWP:\t%f\t%f\t%f" % (np.average(CWPs), expect_avg_cwp, 
                    (np.average(CWPs)-expect_avg_cwp)/expect_avg_cwp)
    print "MWP:\t%f\t%f\t%f" % (np.average(MWPs), expect_avg_mwp, 
                    (np.average(MWPs)-expect_avg_mwp)/expect_avg_mwp)
    print ""
    '''
    plt.figure("sepia")
    plt.title("sepia")
    plt.plot(threads, times, 'b*')
    axes = plt.gca()
    axes.set_ylim([0, 330])
    #plt.show()
    '''
    #assert 1 == 0


def test_HK_blackscholes():

    print "TESTING blackscholes..."

    # input size: 9000000
    n = 9000000.
    gstats = GPUStats('FX5600')
    reg32_per_thread = 11
    shared_mem_per_block = 36
    kstats = KernelStats(137, 7, 0, 0, reg32_per_thread, shared_mem_per_block)  # TODO synch_insns=0 ?
    expected = 34

    trials = 9
    threads = [(x*2+6)*(x*2+6) for x in range(trials)]
    times = []
    occupancies = []
    CPIs = []
    CWPs = []
    MWPs = []
    print "blk sz\tactive\tocc\t\tcwp\t\tmwp\t\tcpi\t\ttime"
    for i in range(trials):
        #print " ", n/threads[i], math.ceil(n/threads[i]), n
        tconfig = ThreadConfig(threads[i], math.ceil(n/threads[i]))
        model = PerfModel(gstats, kstats, tconfig, np.dtype(np.float32))
        times.append(model.compute_total_cycles() /
                    (gstats.sm_clock_freq*(10**9))*(10**3))
        occupancies.append(model.occ)
        CPIs.append(model.CPI)
        CWPs.append(model.CWP)
        MWPs.append(model.MWP)
        print "%i\t%i\t%f\t%f\t%f\t%f\t%f" % (threads[i], model.active_blocks_per_SM,
                                              occupancies[i], CWPs[i], MWPs[i],
                                              CPIs[i], times[i])

    expect_avg_occ = 0.745
    expect_avg_cpi = 16
    expect_avg_cwp = 9
    expect_avg_mwp = 2

    print "\nexpected time (approx): ", expected
    print "\n\tactual (avg)\texpected (avg)\trel err"
    print "occ:\t%f\t%f\t%f" % (np.average(occupancies), expect_avg_occ, 
                    (np.average(occupancies)-expect_avg_occ)/expect_avg_occ)
    print "CPI:\t%f\t%f\t%f" % (np.average(CPIs), expect_avg_cpi, 
                    (np.average(CPIs)-expect_avg_cpi)/expect_avg_cpi)
    print "CWP:\t%f\t%f\t%f" % (np.average(CWPs), expect_avg_cwp, 
                    (np.average(CWPs)-expect_avg_cwp)/expect_avg_cwp)
    print "MWP:\t%f\t%f\t%f" % (np.average(MWPs), expect_avg_mwp, 
                    (np.average(MWPs)-expect_avg_mwp)/expect_avg_mwp)
    print ""
    '''
    plt.figure("blackscholes")
    plt.title("blackscholes")
    plt.plot(threads, times, 'b*')
    axes = plt.gca()
    axes.set_ylim([0, 78])
    #plt.show()
    '''
    #assert 1 == 0
    #assert (abs(model.compute_total_cycles() - expected) / expected) < TOLERANCE


def test_HK_linear():

    print "TESTING linear..."

    # input size: 10000x10000
    n = 10000.
    gstats = GPUStats('FX5600')
    reg32_per_thread = 15
    shared_mem_per_block = 60
    kstats = KernelStats(111, 30, 0, 0, reg32_per_thread, shared_mem_per_block)  # TODO synch_insns=0 ?
    expected = 775

    trials = 9
    threads = [(x*2+6)*(x*2+6) for x in range(trials)]
    times = []
    occupancies = []
    CPIs = []
    CWPs = []
    MWPs = []
    print "blk sz\tactive\tocc\t\tcwp\t\tmwp\t\tcpi\t\ttime"
    for i in range(trials):
        #tconfig = ThreadConfig(threads[i], (math.ceil(n/(threads[i]**0.5))**2)/2.0)
        tconfig = ThreadConfig(threads[i], (math.ceil(n/(threads[i]**0.5))**2))
        # TODO why do I have to divide by 2.0 to match HK results?
        #print " ", n*n/threads[i], math.ceil(n/(threads[i]**0.5))**2, n
        model = PerfModel(gstats, kstats, tconfig, np.dtype(np.float32))
        times.append(model.compute_total_cycles() /
                    (gstats.sm_clock_freq*(10**9))*(10**3))
        occupancies.append(model.occ)
        CPIs.append(model.CPI)
        CWPs.append(model.CWP)
        MWPs.append(model.MWP)
        print "%i\t%i\t%f\t%f\t%f\t%f\t%f" % (threads[i], model.active_blocks_per_SM,
                                              occupancies[i], CWPs[i], MWPs[i],
                                              CPIs[i], times[i])

    expect_avg_occ = 0.59
    expect_avg_cpi = 73
    expect_avg_cwp = 14
    expect_avg_mwp = 2

    print "\nexpected time (approx): ", expected
    print "\n\tactual (avg)\texpected (avg)\trel err"
    print "occ:\t%f\t%f\t%f" % (np.average(occupancies), expect_avg_occ, 
                    (np.average(occupancies)-expect_avg_occ)/expect_avg_occ)
    print "CPI:\t%f\t%f\t%f" % (np.average(CPIs), expect_avg_cpi, 
                    (np.average(CPIs)-expect_avg_cpi)/expect_avg_cpi)
    print "CWP:\t%f\t%f\t%f" % (np.average(CWPs), expect_avg_cwp, 
                    (np.average(CWPs)-expect_avg_cwp)/expect_avg_cwp)
    print "MWP:\t%f\t%f\t%f" % (np.average(MWPs), expect_avg_mwp, 
                    (np.average(MWPs)-expect_avg_mwp)/expect_avg_mwp)
    print ""
    #'''
    plt.figure("linear")
    plt.title("linear")
    plt.plot(threads, times, 'b*')
    axes = plt.gca()
    axes.set_ylim([0, 2*1395])
    #axes.set_ylim([0, 1395])
    #plt.show()
    #'''
    #assert 1 == 0
    #assert (abs(model.compute_total_cycles() - expected) / expected) < TOLERANCE


def test_HK_SVM():

    print "TESTING SVM..."

    # input size: 736*992
    n1 = 736.
    n2 = 992.
    gstats = GPUStats('FX5600')
    reg32_per_thread = 9
    shared_mem_per_block = 44
    kstats = KernelStats(10871, 0, 819, 0, reg32_per_thread, shared_mem_per_block)  # TODO synch_insns=0 ?
    expected = 14

    trials = 17
    threads = [(x+6)*(x+6) for x in range(trials)]
    times = []
    occupancies = []
    CPIs = []
    CWPs = []
    MWPs = []
    print "blk sz\tactive\tocc\t\tcwp\t\tmwp\t\tcpi\t\ttime"
    for i in range(trials):
        tconfig = ThreadConfig(threads[i],
                    math.ceil(n1/(threads[i]**0.5))*math.ceil(n2/(threads[i]**0.5)))
                    #math.ceil(n1/(threads[i]**0.5))*math.ceil(n2/(threads[i]**0.5))/4.0)
                    # TODO why do I have to divide by 4.0 to match HK results?
        model = PerfModel(gstats, kstats, tconfig, np.dtype(np.float32))
        times.append(model.compute_total_cycles() /
                    (gstats.sm_clock_freq*(10**9))*(10**3))
        occupancies.append(model.occ)
        CPIs.append(model.CPI)
        CWPs.append(model.CWP)
        MWPs.append(model.MWP)
        print "%i\t%i\t%f\t%f\t%f\t%f\t%f" % (threads[i], model.active_blocks_per_SM,
                                              occupancies[i], CWPs[i], MWPs[i],
                                              CPIs[i], times[i])

    expect_avg_occ = 0.84
    expect_avg_cpi = 3.5
    expect_avg_cwp = 9
    expect_avg_mwp = 12

    print "\nexpected time (approx): ", expected
    print "\n\tactual (avg)\texpected (avg)\trel err"
    print "occ:\t%f\t%f\t%f" % (np.average(occupancies), expect_avg_occ, 
                    (np.average(occupancies)-expect_avg_occ)/expect_avg_occ)
    print "CPI:\t%f\t%f\t%f" % (np.average(CPIs), expect_avg_cpi, 
                    (np.average(CPIs)-expect_avg_cpi)/expect_avg_cpi)
    print "CWP:\t%f\t%f\t%f" % (np.average(CWPs), expect_avg_cwp, 
                    (np.average(CWPs)-expect_avg_cwp)/expect_avg_cwp)
    print "MWP:\t%f\t%f\t%f" % (np.average(MWPs), expect_avg_mwp, 
                    (np.average(MWPs)-expect_avg_mwp)/expect_avg_mwp)
    print ""
    #'''
    plt.figure("svm")
    plt.title("svm")
    plt.plot(threads, times, 'b*')
    axes = plt.gca()
    axes.set_ylim([0, 60])
    plt.show()
    #'''
    #assert 1 == 0
    #assert (abs(model.compute_total_cycles() - expected) / expected) < TOLERANCE


def test_reg_counter_basic():

    knl = lp.make_kernel(
            "[n,m,l] -> {[i,k,j]: 0<=i<n and 0<=k<m and 0<=j<l}",
            [
                """
                c[i, j, k] = a[i,j,k]*b[i,j,k]/3.0+a[i,j,k]
                e[i, k+1] = g[i,k]*h[i,k+1]
                """
            ],
            name="basic", assumptions="n,m,l >= 1")

    knl = lp.add_and_infer_dtypes(knl,
                        dict(a=np.float32, b=np.float32, g=np.float64, h=np.float64))
    regs = estimate_regs_per_thread(knl)
    assert regs == 6


def test_reg_counter_reduction():

    knl = lp.make_kernel(
            "{[i,k,j]: 0<=i<n and 0<=k<m and 0<=j<l}",
            [
                "c[i, j] = sum(k, a[i, k]*b[k, j])"
            ],
            name="matmul_serial", assumptions="n,m,l >= 1")

    knl = lp.add_and_infer_dtypes(knl, dict(a=np.float32, b=np.float32))
    regs = estimate_regs_per_thread(knl)
    assert regs == 6


def test_reg_counter_logic():

    knl = lp.make_kernel(
            "{[i,k,j]: 0<=i<n and 0<=k<m and 0<=j<l}",
            [
                """
                e[i,k] = if(not(k<l-2) and k>6 or k/2==l, g[i,k]*2, g[i,k]+h[i,k]/2)
                """
            ],
            name="logic", assumptions="n,m,l >= 1")

    knl = lp.add_and_infer_dtypes(knl, dict(g=np.float32, h=np.float64))
    regs = estimate_regs_per_thread(knl)
    assert regs == 6


def test_reg_counter_specialops():

    knl = lp.make_kernel(
            "{[i,k,j]: 0<=i<n and 0<=k<m and 0<=j<l}",
            [
                """
                c[i, j, k] = (2*a[i,j,k])%(2+b[i,j,k]/3.0)
                e[i, k] = (1+g[i,k])**(1+h[i,k+1])
                """
            ],
            name="specialops", assumptions="n,m,l >= 1")

    knl = lp.add_and_infer_dtypes(knl,
                        dict(a=np.float32, b=np.float32, g=np.float64, h=np.float64))
    regs = estimate_regs_per_thread(knl)
    assert regs == 6


def test_reg_counter_bitwise():

    knl = lp.make_kernel(
            "{[i,k,j]: 0<=i<n and 0<=k<m and 0<=j<l}",
            [
                """
                c[i, j, k] = (a[i,j,k] | 1) + (b[i,j,k] & 1)
                e[i, k] = (g[i,k] ^ k)*(~h[i,k+1]) + (g[i, k] << (h[i,k] >> k))
                """
            ],
            name="bitwise", assumptions="n,m,l >= 1")

    knl = lp.add_and_infer_dtypes(
            knl, dict(
                a=np.int32, b=np.int32,
                g=np.int64, h=np.int64))
    regs = estimate_regs_per_thread(knl)
    assert regs == 6


test_HK_example()
test_HK_sepia()
test_HK_blackscholes()
test_HK_linear()
test_HK_SVM()
test_reg_counter_basic()
'''
if __name__ == "__main__":
    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        from py.test.cmdline import main
        main([__file__])
'''

