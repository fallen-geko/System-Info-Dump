# Written by Romeo Dabok
# References: got some help from:
#   - https://www.thepythoncode.com/article/get-hardware-system-information-python
#   - https://www.programcreek.com/python/example/53873/psutil.boot_time
#   - https://docs.python.org/3/library/time.html

import psutil
import platform
import csv
import os
import time

dtime = lambda s: time.strftime("%a, %d %b %Y %H:%M:%S", s)
def getSize(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

def getSysInfo():
    uname = platform.uname()
    stab = {}
    stab["system"]=uname.system
    stab["release"]=uname.release
    stab["version"]=uname.version
    stab["nodeName"]=uname.node
    stab["machine"]=uname.machine
    stab["processor"]=uname.processor
    return stab

def getDiskInfo():
    dinf = {"partitions":{}}
    #Partitions
    partitions = psutil.disk_partitions()
    for partition in partitions:
        dname = partition.device
        dinf["partitions"][dname]={}
        dinf["partitions"][dname]["mountPoint"]=partition.mountpoint
        dinf["partitions"][dname]["fileSystemType"]=partition.fstype
        try:
            partition_usage = psutil.disk_usage(partition.mountpoint)
        except PermissionError:
            # Partition cant be accessed
            dinf["partitions"][dname]["totalSize"]="Unknown"
            dinf["partitions"][dname]["used"]="Unknown"
            dinf["partitions"][dname]["free"]="Unknown"
            dinf["partitions"][dname]["percentageUsed"]="Unknown"
        else:
            dinf["partitions"][dname]["totalSize"]=getSize(partition_usage.total)
            dinf["partitions"][dname]["used"]=getSize(partition_usage.used)
            dinf["partitions"][dname]["free"]=getSize(partition_usage.free)
            dinf["partitions"][dname]["percentageUsed"]=partition_usage.percent
    # IO stats since boot
    disk_io = psutil.disk_io_counters()
    dinf["totalIORead"]=getSize(disk_io.read_bytes)
    dinf["totalIOWrite"]=getSize(disk_io.write_bytes)
    return dinf
def getNetworkInfo():
    # Get all network interfaces
    netty={"interfaces":{}}
    if_addrs = psutil.net_if_addrs()
    for interface_name, interface_addresses in if_addrs.items():
        for address in interface_addresses:
            netty["interfaces"][interface_name]={}
            sf=str(address.family)
            if sf.find('AddressFamily.AF_INET')!=-1:
                netty["interfaces"][interface_name]["IPAddress"]=address.address
                netty["interfaces"][interface_name]["netMask"]=address.netmask
                netty["interfaces"][interface_name]["broadcastIP"]=address.broadcast
            elif sf.find('AddressFamily.AF_PACKET')!=-1:
                netty["interfaces"][interface_name]["MACAddress"]=address.address
                netty["interfaces"][interface_name]["netMask"]=address.netmask
                netty["interfaces"][interface_name]["broadcastMac"]=address.broadcast
    # IO stats since boot
    net_io = psutil.net_io_counters()
    netty["totalBytesSent"]=getSize(net_io.bytes_sent)
    netty["totalBytesRecieved"]=getSize(net_io.bytes_recv)
    return netty

bootTime=psutil.boot_time()
otime=time.localtime(bootTime)
tta=dtime(otime)
def dumpToCSV(filename,dsys=True,ddisk=True,dnet=True):
    sys = getSysInfo()
    disk=getDiskInfo()
    nets = getNetworkInfo()
    try:
        with open(filename+'.csv', 'w', newline="") as csvfile:
            filewriter = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            if dsys == True:
                filewriter.writerow(["SYSTEM INFORMATION"])
                filewriter.writerow(['System', sys["system"]])
                filewriter.writerow(['Release', sys["release"]])
                filewriter.writerow(['Version', sys["version"]])
                filewriter.writerow(['Node name', sys["nodeName"]])
                filewriter.writerow(['Machine', sys["machine"]])
                filewriter.writerow(['Processor', sys["processor"]])
                filewriter.writerow(['Boot Time', tta])
                filewriter.writerow([''])
            if ddisk == True:
                filewriter.writerow(["DISK INFORMATION"])
                filewriter.writerow(['Read operations since boot', disk["totalIORead"]])
                filewriter.writerow(['Write operations since boot', disk["totalIOWrite"]])
                filewriter.writerow(["Partitions"])
                filewriter.writerow(["Partition","Mount Point","File System Type","Total Size","Used","Free","Percentage Used"])
                dpart=disk["partitions"]
                for p in dpart:
                    dp=dpart[p]
                    tt=["","","",""]
                    try:
                        tt[0] = dp["totalSize"]
                        tt[1] = dp["used"]
                        tt[2] = dp["free"]
                        tt[3] = dp["percentageUsed"]
                    except KeyError:
                        tt=["Unavailable","Unavailable","Unavailable","Unavailable"]
                    filewriter.writerow([p,dp["mountPoint"],dp["fileSystemType"],tt[0],tt[1],tt[2],tt[3]])
                filewriter.writerow(['Node name', sys["nodeName"]])
                filewriter.writerow(['Machine', sys["machine"]])
                filewriter.writerow(['Processor', sys["processor"]])
                filewriter.writerow([''])
            if dnet == True:
                filewriter.writerow(["NETWORK INFORMATION"])
                filewriter.writerow(['Total bytes  sent since boot', nets["totalBytesSent"]])
                filewriter.writerow(['Total bytes recieved since boot', nets["totalBytesRecieved"]])
                filewriter.writerow(["Interfaces"])
                filewriter.writerow(["Interface","IP/MAC Address","Net Mask","Broadcast IP/MAC"])
                nints = nets["interfaces"]
                for i in nints:
                    iin = nints[i]
                    si = ["NULL","NULL","NULL"]
                    for a in iin:
                        if a == "IPAddress" or a == "MACAddress":
                            si[0]=iin[a]
                        elif a == 'netMask':
                            si[1]=iin[a]
                        elif a == "broadcastIP" or a == "broadcastMac":
                            si[2]=iin[a]
                    filewriter.writerow([i,si[0],si[1],si[2]])
    except PermissionError:
        print("Writing to .csv failed!")
        print("Please try again using a different filename.")
        return False
    else:
        wd = os.getcwd()
        print("Writing to .csv successful!")
        print(filename+".csv saved in "+wd)
        return True
