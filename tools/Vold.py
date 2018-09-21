import os, sys
import pvl
import glob
import json
import argparse
import urllib.request
import http.client

def load_pvl(pvl_file_path):
    with open(pvl_file_path, 'r') as f:
        f.readline()
        data = f.read()
    voldesc = pvl.loads(data)
    return voldesc

class Args:
    def __init__(self):
        pass

    def parse_args(self):
        parser = argparse.ArgumentParser(prog='sys.argv')
        #how to make other optional
        parser.add_argument('--textfile','-f',help='Input text file path .txt')
        parser.add_argument('--output','-o',help='Output file path .json')
        args = parser.parse_args()
        self.textfile = args.textfile
        self.output = args.output

def main():
    args = Args()
    args.parse_args()
    if type(args.textfile) == str:
        filePath = open(args.textfile,'r')
        lines = filePath.readlines()
        length = len(lines)
        vol_val = {}
        for n in range(length):
            #voldesc = load_pvl(lines[n].rstrip())

            #trying to make URLs work
            voldesc = urllib.request.urlreadf(lines[n])
            voldescPvl = pvl.dumps(http.client.HTTPResponse.read(voldesc))
            dataset_id = voldescPvl['VOLUME']['DATA_SET_ID']
            volume_name = voldescPvl['VOLUME']['VOLUME_NAME']
            if isinstance(dataset_id, (list, tuple, set)):
                vol_val[volume_name] = len(dataset_id)
            else:
                vol_val[volume_name]= 1
    else:
        #make urls possible
        filePath = open(str(sys.argv[1]), 'r')
        vol_val = {}
        voldesc = load_pvl(str(sys.argv[1]))
        dataset_id = voldesc['VOLUME']['DATA_SET_ID']
        volume_name = voldesc['VOLUME']['VOLUME_NAME']
        if isinstance(dataset_id, (list, tuple, set)):
            vol_val[volume_name] = len(dataset_id)
        else:
            vol_val[volume_name]= 1

    
    if type(args.output) == str:
        f = open(args.output,'w')
        f.write(str(json.dumps(vol_val)))
    else:
        print(json.dumps(vol_val))

if __name__ == '__main__':
    main()