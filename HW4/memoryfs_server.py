import pickle, logging
import argparse
import time
import dbm
import os.path
import re 


# For locks: RSM_UNLOCKED=0 , RSM_LOCKED=1 
RSM_UNLOCKED = bytearray(b'\x00') * 1
RSM_LOCKED = bytearray(b'\x01') * 1

from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
  rpc_paths = ('/RPC2',)

class DiskBlocks():
  def __init__(self, total_num_blocks, block_size):
    # This class stores the raw block array
    self.block = []                                            
    # Initialize raw blocks 
    for i in range (0, total_num_blocks):
      putdata = bytearray(block_size)
      self.block.insert(i,putdata)

if __name__ == "__main__":

  # Construct the argument parser
  ap = argparse.ArgumentParser()

  ap.add_argument('-nb', '--total_num_blocks', type=int, help='an integer value')
  ap.add_argument('-bs', '--block_size', type=int, help='an integer value')
  ap.add_argument('-port', '--port', type=int, help='an integer value')
  #-delayat COUNT
  ap.add_argument('-delayat', '--COUNT', type=int, help='an integer value')
  """
  To this end, modify the server to support two additional command-line arguments: 
  -initdbm : an integer flag; 1 initializes the database with zero blocks, 0 does not initialize 
  the database 
  -dbmfile : a string that names the file used by dbm in disk 

  If the -dbmfile argument is given, you should use the named file as storage. 
  Then, if -initdbm is 1, initialize all blocks with zeroes; otherwise, don't initialize - simply 
  use its contents.

  - dbm only supports strings or bytes for keys and values. You can convert the 
  key (block number)  - to a string with str(). You can convert from 
  bytearray to bytes with bytes(), and from bytes to bytearray with bytearray().

  with dbm.open('my_store', 'c') as db:
  db['key'] = 'value'
  print(db.keys()) # ['key']
  print(db['key']) # 'value'
  print('key' in db) # True
  """
  ap.add_argument('-initdbm', '--FLAG', type=int, help='an integer value')
  ap.add_argument('-dbmfile', '--FILE_NAME', type=str, help='a string value')

  args = ap.parse_args()



  

  if args.total_num_blocks:
    TOTAL_NUM_BLOCKS = args.total_num_blocks
  else:
    print('Must specify total number of blocks') 
    quit()

  if args.block_size:
    BLOCK_SIZE = args.block_size
  else:
    print('Must specify block size')
    quit()

  if args.port:
    PORT = args.port
  else:
    print('Must specify port number')
    quit()

  if args.COUNT:
    COUNT = args.COUNT 
    init_count = args.COUNT 

  #if args.FLAG == 1:
    # initialize blocks
  #  FLAG = args.FLAG
  print("INITIALIZE BLOCKS TO 0 BELOW")
  RawBlocks = DiskBlocks(TOTAL_NUM_BLOCKS, BLOCK_SIZE)
  
  
  #######################
  """
  for i in range (0, TOTAL_NUM_BLOCKS):
    print("i ", i)
    dat = RawBlocks.block[i]
    print("dat ", bytearray(dat))
  """
  print("PUT VALUES INTO RAWBLOCKS BELOW")
  ######################
  if args.FILE_NAME :
    FILE_NAME = args.FILE_NAME
    
    with dbm.open(FILE_NAME, 'c') as db:
      #RawBlocks.block[block_number] = bytearray(db[str(block_number)])
      
      for  key in db.keys():
        print("key ", key)


        convert_key = key.decode()
        converted_key = int((convert_key))
        RawBlocks.block[converted_key] = bytearray(db[str(converted_key)])
               
        #print("converted_key ", converted_key)
        #print("bytearray(db[str(converted_key)]) ", bytearray(db[str(converted_key)]))
        #convert_key = key.decode()
        #convert_key = re.sub('[\W_]+', '', convert_key)
      
    db.close()

  """with dbm.open(FILE_NAME, 'c') as db:
      #RawBlocks.block[block_number] = bytearray(db[str(block_number)])
      for  key in db.keys():
        val = db[key]
        print("value ", val)
        print("key ", key)
  db.close()"""
  
  #print("PRINTING RAWBLOCKS")
  for i in range (0, 13):
    #print("block # ", i)
    dat = RawBlocks.block[i]
    #print("dat ", (bytearray(dat)))
  
  # Create server
  server = SimpleXMLRPCServer(("127.0.0.1", PORT), requestHandler=RequestHandler) 

  def Get(block_number):
    
    result = RawBlocks.block[block_number]
    #print("in my get block number and result ", block_number, bytearray(result))
    


    global COUNT
    COUNT= COUNT - 1
    if COUNT < 0 :
      time.sleep(10)
      COUNT = init_count
    #print("count", COUNT) 
    
    return result


  server.register_function(Get)

  def Put(block_number, data):
    #print("!!!!!!!IN PUT block number ", block_number)
    RawBlocks.block[block_number] = data.data


    with dbm.open(FILE_NAME, 'c') as db:
      db[str(block_number)] = bytes(data.data)
      #print("db[str(block_number)] ", db[str(block_number)])
      #print("bytes(data.data) ", bytes(data.data))
      db.close()

    

    global COUNT
    COUNT= COUNT - 1
    if COUNT < 0 :
      time.sleep(10)
      COUNT = init_count
    #print("count", COUNT) 

    return 0

  server.register_function(Put)

  def RSM(block_number):
    result = RawBlocks.block[block_number]
    #print("block number and result in RSM ",block_number, result )
    #print("!!!!!!!!!!IN RSM block number ", block_number)
    # RawBlocks.block[block_number] = RSM_LOCKED
    RawBlocks.block[block_number] = bytearray(RSM_LOCKED.ljust(BLOCK_SIZE,b'\x01'))

    return result

  server.register_function(RSM)

  # Run the server's main loop
  print ("Running block server with nb=" + str(TOTAL_NUM_BLOCKS) + ", bs=" + str(BLOCK_SIZE) + " on port " + str(PORT))
  server.serve_forever()




"""
1) Implement artificial delay in memoryfs_server.py to model a server/network slow to respond

Modify memoryfs_server.py to support a new command-line argument -delayat COUNT, where COUNT
is an integer. Then, in your server code, modify the Get() and Put() implementations such that 
for every Nth request (N is the COUNT), the server artificially delays by "sleeping" for 10 
seconds.

- Python supports a time.sleep() method
import datetime
import time
"""

