#!/usr/bin/python3

import datetime
import os
import pymysql
import re
import shutil
import sys
import telnetlib
import threading
from time import sleep

import ftplib

# Type of device
devices = ("gepon", "mikrotik")

if (len(sys.argv) == 2 and sys.argv[1] in devices):
    device = sys.argv[1]
else:
    print ("Enter the correct device!")
    sys.exit(1)

# MySQL server data
mserver = "IP server"
muser   = "User"
mpass   = "Password"
mdb     = "db"

# Backup server data
bserver = "IP server"
buser   = "User"
bpass   = "Password"

# RDP server data
rserver = "IP server"
ruser   = "User"
rpass   = "Password"
rpath   = "/backup/files/" + device + "/"

# Date
timestamp = datetime.datetime.now()
date      = timestamp.strftime("%Y_%m_%d")

# Folders
tftp_dir   = "/var/www/tftp"
backup_dir = "/" + device + "/" + date
path       = tftp_dir + backup_dir
archive_type = "zip"
archive    = path + "." + archive_type


# Telnet send command
def sender(data):
    return (data.encode("UTF-8") + b"\r\n")


# Check backup exist
def checker(bpath, hostname):
    if (os.path.isfile(bpath) == False):
        print (hostname, "backup doesn`t exist!")
    return


# Clean old backups
def cleaner(storage_time):
    path_to_clean = tftp_dir + "/" + device + "/"
    for backup_date in os.listdir(path_to_clean):
        backup_path = path_to_clean + backup_date
        backup_create = datetime.datetime.fromtimestamp(os.path.getmtime(backup_path))

        if (datetime.datetime.now() - backup_create > datetime.timedelta(days=storage_time)):
            shutil.rmtree(backup_path)
            print ("Removed", backup_path)


# Create archive from today backups
def create_archive_by_date():
    try:
        return shutil.make_archive(path, archive_type, path)

    except Exception as msg:
        print (msg)


# Upload archive to FTP on RDP
def upload_archive_to_rdp():
    try:
        session = ftplib.FTP(rserver,ruser,rpass)
        session.cwd (rpath)
        file = open(archive, "rb")
        session.storbinary("STOR " + date + "." + archive_type, file)
        file.close()
        session.quit()
        os.remove(archive)

    except Exception as msg:
        print (msg)
        os.remove(archive)


# Select device data and start threads
def main():
    try:
        print ("\n=== Backup from", date, "=== \n")

        os.mkdir(path)
        os.chmod(path, 0o777)

        query   = "SELECT `host_name`, `host_address`, `host_activate` FROM `host` WHERE BINARY `host_name` LIKE '" + device + "\_%'"
        connect = pymysql.connect(mserver, muser, mpass, mdb)
        cursor  = connect.cursor()

        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()

        for entry in data:
            hostname = entry[0]
            ip       = entry[1]
            active   = entry[2]

            if (active == "0"):
                continue

            if (device == "gepon"):
                worker = threading.Thread(target=get_backup_olt, args=(hostname, ip))
            elif (device == "mikrotik"):
                worker = threading.Thread(name=hostname, target=get_backup_mikrotik, args=(hostname, ip))
            else:
                continue

            worker.start()

        while threading.active_count() != 1:
            sleep(1)
            #print(threading.enumerate(),"\n")        

        cleaner(14)

        create_archive_by_date()        
        upload_archive_to_rdp()

    except Exception as msg:
        print (msg)
        return


def get_backup_mikrotik(hostname, ip):
    src        = hostname + ".backup"
    dst        = backup_dir + "/" + src
    cmd_backup = "/system backup save name=" + hostname
    cmd_upload = "/tool fetch mode=ftp address=" + bserver + " user=" + buser + " password=" + bpass + " src-path=" + src + " dst-path=" + dst + " upload=yes"

    try:
        tn = telnetlib.Telnet(ip)
    except Exception as msg:
        print (msg, hostname, ip)
        return

    tn.expect([re.compile(b"Login:"), ], 5)
    tn.write(sender(buser))

    tn.expect([re.compile(b"Password:"), ], 5)
    tn.write(sender(bpass))

    bad_login = tn.expect([re.compile(b"Login failed, incorrect username or password"), ], 5)

    if (bad_login[0] != -1):
        print ("Login failed - ", hostname, ip)
        return

    data = b""
    while data.find(b"backup_user") == -1:
        data = tn.read_very_eager()

    data = b""
    tn.write(sender(cmd_backup))

    while data.find(b"Configuration backup saved") == -1:
        data = tn.read_very_eager()

    data = b""
    tn.write(sender(cmd_upload))

    sleep(15)

    tn.close()
    checker(path + "/" + src, hostname)


def get_backup_olt(hostname, ip):
    dst      = backup_dir + "/" + hostname
    cmd_ena  = "enable"
    cmd_copy = "copy startup-config tftp:" + dst + " " + bserver

    try:
        tn = telnetlib.Telnet(ip)
    except Exception as msg:
        print (msg, hostname, ip)
        return

    tn.expect([re.compile(b"Username:"), ], 5)
    tn.write(sender(buser))

    tn.expect([re.compile(b"Password:"), ], 5)
    tn.write(sender(bpass))

    login = tn.expect([re.compile(b">"), ], 5)

    if (login[0] == -1):
        print ("Login failed - ", hostname, ip)
        return

    tn.write(sender(cmd_ena))

    tn.expect([re.compile(b"#"), ], 5)
    tn.write(sender(cmd_copy))

    tn.expect([re.compile(b"TFTP:successfully"), ], 5)

    tn.close()
    checker(path + "/" + hostname, hostname)


if __name__ == "__main__":
    main()
