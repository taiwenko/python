import subprocess
import time
import os

for x in range(1,51):
    mid_value = "adb -s alt" + str(x) + ':4321 shell "echo 0 > /d/localtime-vcxo/value"'
    os.system(mid_value)
    time.sleep(8)
    mid_factory = "adb -s alt" + str(x) + ':4321 shell "echo 1 > /d/localtime-vcxo/factory_test"'
    os.system(mid_factory)
    mid_output = subprocess.Popen(['adb', '-s', 'alt' + str(x) + ':4321', 'shell', 'cat', '/d/localtime-vcxo/factory_test'], stdout=subprocess.PIPE)
    mid_string = mid_output.communicate()[0]
    mid_lines = mid_string.split('\r')
    uresults1 = mid_lines[1]
    uresults2 = mid_lines[2]
    uresults3 = mid_lines[3]
    mid_results1 = uresults1[1:]
    mid_results2 = uresults2[1:]
    mid_results3 = uresults3[1:]
    results32m = mid_results1.split('=')
    results38p4m = mid_results2.split('=')
    resultsppmmid = mid_results3.split('=')
    results1 = results32m[1]
    results2 = results38p4m[1]
    results3 = resultsppmmid[1]
    final_32m = results1[1:]
    final_38p4m = results2[1:]
    final_ppmmid = results3[1:]
    print final_32m
    print final_38p4m
    print final_ppmmid



    low_value = "adb -s alt" + str(x) + ':4321 shell "echo -32767 > /d/localtime-vcxo/value"'
    os.system(low_value)
    time.sleep(8)
    low_factory = "adb -s alt" + str(x) + ':4321 shell "echo 1 > /d/localtime-vcxo/factory_test"'
    os.system(low_factory)
    low_output = subprocess.Popen(['adb', '-s', 'alt' + str(x) + ':4321', 'shell', 'cat', '/d/localtime-vcxo/factory_test'], stdout=subprocess.PIPE)
    low_string = low_output.communicate()[0]
    low_lines = low_string.split('\r')
    uresults1 = low_lines[1]
    uresults2 = low_lines[2]
    uresults3 = low_lines[3]
    low_results1 = uresults1[1:]
    low_results2 = uresults2[1:]
    low_results3 = uresults3[1:]
    results32l = low_results1.split('=')
    results38p4l = low_results2.split('=')
    resultsppmlow = low_results3.split('=')
    results1 = results32l[1]
    results2 = results38p4l[1]
    results3 = resultsppmlow[1]
    final_32l = results1[1:]
    final_38p4l = results2[1:]
    final_ppmlow = results3[1:]
    print final_32l
    print final_38p4l
    print final_ppmlow



    high_value = "adb -s alt" + str(x) + ':4321 shell "echo 32767 > /d/localtime-vcxo/value"'
    os.system(high_value)
    time.sleep(8)
    high_factory = "adb -s alt" + str(x) + ':4321 shell "echo 1 > /d/localtime-vcxo/factory_test"'
    os.system(high_factory)
    high_output = subprocess.Popen(['adb', '-s', 'alt' + str(x) + ':4321', 'shell', 'cat', '/d/localtime-vcxo/factory_test'], stdout=subprocess.PIPE)
    high_string = high_output.communicate()[0]
    high_lines = high_string.split('\r')
    uresults1 = high_lines[1]
    uresults2 = high_lines[2]
    uresults3 = high_lines[3]
    high_results1 = uresults1[1:]
    high_results2 = uresults2[1:]
    high_results3 = uresults3[1:]
    results32h = high_results1.split('=')
    results38p4h = high_results2.split('=')
    resultsppmhigh = high_results3.split('=')
    results1 = results32h[1]
    results2 = results38p4h[1]
    results3 = resultsppmhigh[1]
    final_32h = results1[1:]
    final_38p4h = results2[1:]
    final_ppmhigh = results3[1:]
    print final_32h
    print final_38p4h
    print final_ppmhigh



    s = subprocess.Popen(['adb', '-s', 'alt' + str(x) + ':4321', 'shell', 'getprop', 'ro.serialno'], stdout=subprocess.PIPE)
    serialnum = s.communicate()[0]
    final_serialnum = serialnum[:-2]
    print final_serialnum



    # csv = final_serialnum + ',' + final_32m + ',' + final_38p4m + ',' + final_ppmmid + ',' + final_32l + ',' + final_38p4l + ',' + final_ppmlow + ',' + final_32h + ',' + final_38p4h + ',' + final_ppmhigh
    csv = final_serialnum + ',' + final_ppmmid + ',' + final_ppmlow + ',' + final_ppmhigh
    print csv
    csvfile = "vcxo_results_alt.csv"
    f = open(csvfile, "a")
    f.write(csv)
    f.write("\n")
