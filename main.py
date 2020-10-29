import os, argparse, sys, subprocess

parser = argparse.ArgumentParser()
parser.add_argument("logcat", help="Path to logcat file, you can drag a logcat file to the cmd window", type=str)
parser.add_argument("dump", help="Path to the dump you want to push the missing files from", type=str)
args = parser.parse_args()

def findMissing():
    count = 0
    missingFiles = []
    paths = []
    binaries = []
    for line in matching_lines:
        a = line.split("library ",1)[1]
        b = a.split(" not",1)[0]
#        print(b)
        try:
            a2 = line.split("EXECUTABLE ",1)[1]
            b2 = a2.split(":",1)[0]
            c2 = b2.split("/")[-1]
            d2 = b2.replace(c2, "")
            a3 = b2.split("/")[-1].replace('"', "")
        except IndexError:
            a2 = line.split("load ",1)[1]
            b2 = a2.split(":",1)[0]
            c2 = b2.split("/")[-1]
            d2 = b2.replace(c2, "")
            a3 = b2.split("/")[-1].replace('"', "")

        if b.replace('"', "") in missingFiles:
            pass
        else:
            missingFiles.insert(count, b.replace('"', ""))
            print(d2)
            paths.insert(count, d2.replace('"', ""))
            binaries.insert(count, a3)
            count += 1
    if missingFiles == []:
        print("No missing files found! exiting...")
        sys.exit(0)
    return(missingFiles, paths, binaries)

def pushFile():
    count = 0
    for missingLib in missingFiles:
        a = paths[count].replace('"', '')
        b = a.split("/")[-2]
        c = a.replace(b + "/", "")
        d = c + "lib" + archs[count] + "/"
        if os.name == 'nt':
               a2 = c.replace('/', '\\')
               b2 = a2 + 'lib' + archs[count] + '\\' 
        else:
            b2 = c + 'lib' + archs[count] + '/'
        if os.name == 'nt':
            stream = subprocess.Popen("adb push {}{} {}".format(args.dump + b2, missingLib, d), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            stream = subprocess.Popen("adb push {}{} {}".format(args.dump + b2, missingLib, d), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = stream.communicate()
        if "No such file or directory" in output[0].decode("utf-8"):
            print("Verify dump path!")
            print("ERROR: " + output[0].decode("utf-8").strip())
            sys.exit(0)
        print("OUTPUT: " + output[0].decode("UTF-8"))
        if b"Read" in output[0]:
            print("Your device is mounted as READ-ONLY, please remount it")
            sys.exit(0)
            count += 1

def determineFileArch():
    archs = []
    count = 0
    for binary in binaries:
        if os.name == 'nt':
            stream = subprocess.Popen("adb shell file {}/{}".format(paths[count], binary), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            stream = subprocess.Popen("adb shell file {}/{}".format(paths[count], binary), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = stream.communicate()
        if b"devices" in output[1]:
            print("No devices connected...")
            sys.exit(0)
        if b"64-bit" in output[0]:
            arch = "64"
        elif b"32-bit" in output[0]:
            arch = ""
        else:
            print("Something went wrong determining file architectures")
            print("Trying another way")
            if os.name == 'nt':
                stream = subprocess.Popen("adb shell toybox file {}/{}".format(paths[count], binary), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                stream = subprocess.Popen("adb shell toybox file {}/{}".format(paths[count], binary), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = stream.communicate()
            if b"64-bit" in output[0]:
                arch = "64"
            elif b"32-bit" in output[0]:
                arch = ""
            else:
                for line in output:
                    if "No such file or directory" in output[0].decode("utf-8"):
                        print("Verify dump path!")
                        print("ERROR: adb reports: " + str(line).strip())
                        sys.exit(0)
                    print("ERROR: " + str(line).strip())
                sys.exit(0)
        archs.insert(count, arch)
        count += 1
    return(archs)

logcat = open(args.logcat, 'r', encoding="utf-16", errors="ignore")
try:
    logcatLines = logcat.readlines()
except:
    logcat = open(args.logcat, 'r', encoding="utf-8", errors="ignore")
    logcatLines = logcat.readlines()
matching_lines = [line for line in logcatLines if ": library" in line]

missingFiles = findMissing()[0]
paths = findMissing()[1]
binaries = findMissing()[2]
archs = determineFileArch()
pushFile()

input("All done! Press enter to quit...")
