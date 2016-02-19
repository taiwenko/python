#!/usr/bin/python

import glob
import os
import re
import sys
from subprocess import *

kDataDir = "./data"
kDataExt = ".data"
kWorkDir = "/tmp/thermal_monitor_work"

class LogData():
    data_sets = dict()
    min_ts = 0

    def __init__(self, fd, name):
        self.name = name
        self.fields = dict()

        lines = fd.read().split("\n")

        for line in lines:
            if re.match("^([^,=]+=[^,=]+)(,([^,=]+=[^,=]+))*$", line) is None:
                continue

            data = dict([ x.split('=') for x in line.split(',') ])
            if ('mstart' in data) and ('mstop' in data) and ('ser_no' in data):
                mstart = int(data['mstart'])
                mstop = int(data['mstop'])
                del data['ser_no']
                del data['mstart']
                del data['mstop']
                ts = (mstart + mstop) / 2

                if (LogData.min_ts == 0) or (ts < LogData.min_ts):
                    LogData.min_ts = ts

                for (k, v) in data.items():
                    f = self.fields.setdefault(k, list())
                    f.append((ts, v))

        for i in self.fields.values():
            i.sort(key=lambda x: x[0])

    @staticmethod
    def transform_ts(ts):
        return (ts - LogData.min_ts) / 1000000.0

    @staticmethod
    def parse(name):
        fd = open(name, "r")
        if fd is not None:
            m = re.match("^.*/([^.]+)%s$" % (kDataExt, ), name)
            if m is not None:
                name = m.group(1)
                print "Parsing %s" % (name, )
                LogData.data_sets[name] = LogData(fd, name)
            fd.close()

    @staticmethod
    def get_with_fields(fields):
        ret = list()

        for d in LogData.data_sets.values():
            if set(fields).issubset(d.fields.keys()):
                ret.append(d)

        return ret

def main():
    fields = sys.argv[1:]
    if len(fields) == 0:
        print 'Must specify at least one field to graph'
        sys.exit(0)

    file_list = glob.glob('%s/*%s' % (kDataDir,kDataExt) )
    for f in file_list:
        LogData.parse(f)

    data_sets = LogData.get_with_fields(fields)
    if len(data_sets) == 0:
        print 'No data sets found with the fields %s' % (str(fields), )
        sys.exit(0)

    if not os.path.exists(kWorkDir):
        os.makedirs(kWorkDir)
    cleanup_files = glob.glob(os.path.join(kWorkDir, '*'))
    for f in cleanup_files:
        os.unlink(os.path.join(kWorkDir, f))

    cmdfile = open(os.path.join(kWorkDir, 'plot.cmd'), "w")
    leader = "plot"
    for d in data_sets:
        for f in fields:
            data = d.fields[f]
            series_name = '%s.%s' % (d.name, f)
            fname = os.path.join(kWorkDir, 'series.%s' % (series_name, ))
            fd = open(fname, "w")
            multiseries = 0
            for x in data:
                if x[1].find('R') != -1:
                    fd.write("%f, " % LogData.transform_ts(x[0]))
                    fd.write("%s, " % x[1].split('R')[0])
                    fd.write("%s, " % x[1].split('R')[1].split('s')[0])
                    fd.write("%s\n" % x[1].split('R')[1].split('s')[1])
                    multiseries = 1
                else:
                    fd.write("%f, %s\n" % (LogData.transform_ts(x[0]), x[1]))
            cmdfile.write("%s \"%s\" using 1:2 title '%s' with lines\n" % ( leader, fname, series_name ) )
            if multiseries:
                cmdfile.write("%s \"%s\" using 1:3 title '%s' with lines\n" % ( 'replot', fname, "ref" ) )
                cmdfile.write("%s \"%s\" using 1:4 title '%s' with lines\n" % ( 'replot', fname, "state" ) ) 
            fd.close()
            leader = ","
    cmdfile.write("\n")
    cmdfile.close()

    print cmdfile.name
    p = Popen(['gnuplot', '-persist', cmdfile.name], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    p.communicate()

if __name__ == "__main__":
    main()

