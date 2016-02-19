import neo_cgi
import neo_util
import neo_cs

hdf = neo_util.HDF()
hdf.setValue("hdf.loadpaths.0", ".")
hdf.readFile("units.hdf")
hdf.readFile("slots.hdf")

cs = neo_cs.CS(hdf)
cs.parseFile("dhcpd.conf.cst")

print cs.render()
