import socket
import os
from datetime import datetime
import hashlib


def close_server():
    timel = datetime.now().strftime("%I:%M%p %B %d, %Y")
    log.write("------- Connection Closed at " + timel + " -------\n")
    log.close()
    s.close()
    exit(0)


def file_download(args, filename, flag):
    s.send(args)
    data = s.recv(1024)
    if flag != "UDP" and flag != "TCP":
        print "Wrong Arguments"
        print "Format FileDownload <TCP/UDP> <file_name>"
        return
    if data != "recieved":
        print data
        return
    if flag == "UDP":
        nport = int(s.recv(1024))
        ncs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        addr = (host, nport)
        ncs.sendto("recieved", addr)
        try:
            f = open(filename, "wb+")
        except:
            print "Insufficient Privileges or Space"
            return
        while True:
            data, addr = ncs.recvfrom(1024)
            if data == "done":
                break
            f.write(data)
            ncs.sendto("recieved", addr)
        f.close()
        ncs.close()
    elif flag == "TCP":
        try:
            f = open(filename, "wb+")
        except:
            print "Insufficient Privileges or Space"
            return
        while True:
            data = s.recv(1024)
            if data == "done":
                break
            f.write(data)
            s.send("recieved")
        f.close()
    hash1 = s.recv(1024)
    f = open(filename, 'rb')
    orig_hash = hashlib.md5(f.read()).hexdigest()
    if hash1 != orig_hash:
        # print hash,orig_hash
        print "File Sent Failed"
    else:
        s.send("sendme")
        data = s.recv(1024)
        print
        print data
        print "md5hash: ", hash1
        print "Successfulluy Downloaded"


def recieve_data(inp):
    try:
        s.send(inp)
    except:
        print "Error in Connection"
        return
    while True:
        try:
            data = s.recv(1024)
        except:
            print "Error in Connection"
            close_server()
            break
        if data == "done":
            break
        try:
            s.send("recieved")
        except:
            print "Connection Error"
            close_server()
        print data
    return


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = raw_input("Host ip: ")
port = input("PORT: ")
down = raw_input("Download Folder: ")
if not os.path.exists(down):
    print "No Such Folder"
    exit(0)
elif not os.access(down, os.W_OK):
    print "No Privilleges"
    exit(0)
else:
    os.chdir(down)
try:
    log = open("client_log.log", "a+")
except:
    print "Cannot Open Log file"
    exit(0)
try:
    s.connect((host, port))
except:
    print "No available server found on given address"
    s.close()
    exit(0)
cnt = 0
print "Connection Established"
time = datetime.now().strftime("%I:%M%p %B %d, %Y")
log.write("------- Connected to " + host + " at " + time + " -------\nCommands Sent:\n")
while True:
    cnt += 1
    args = raw_input("Enter Command: ")
    inp = args.split()
    log.write(str(cnt) + ". " + args + "\n")
    if len(inp) == 0 or inp[0] == "close":
        s.send(args)
        print "Bye"
        close_server()
    elif inp[0] == "IndexGet" or inp[0] == "FileHash":
        recieve_data(args)
    elif inp[0] == "FileDownload":
        file_download(args, " ".join(inp[2:]), inp[1])
    else:
        print "Invalid Command"
s.close()
