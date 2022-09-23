import pickle, logging
import argparse

from memoryfs import *
import os.path

## This class implements an interactive shell to navigate the file system

class FSShell():
  def __init__(self, file):
    # cwd stored the inode of the current working directory
    # we start in the root directory
    self.cwd = 0
    self.FileObject = file

  # implements cd (change directory)
  def cd(self, dir):
    i = self.FileObject.Lookup(dir,self.cwd)

    #dir = name of the directory
    #self.cwd = is the [cwd =  0] number
    #i is the number for the dir example: dir1 [2]
    #self.FileObject.RawBlocks  <memoryfs.DiskBlocks object at 0x7fb21baeb5e0>
    #inobj  <memoryfs.InodeNumber object at 0x7fb21bacd340> - > for dir
    #inobj  <memoryfs.InodeNumber object at 0x7fb21b974a30> -> for file
    #INODE_TYPE_DIR = 2
    # inobj.inode.type -> 2 - dir, 1 - file



    
    if i == -1:
      print ("Error: not found\n")
      return -1
    inobj = InodeNumber(self.FileObject.RawBlocks,i)

    


    inobj.InodeNumberToInode()

    


    if inobj.inode.type != INODE_TYPE_DIR:
      print ("Error: not a directory\n")
      return -1
    self.cwd = i

  # implements ls (lists files in directory)
  def ls(self):
    


    inobj = InodeNumber(self.FileObject.RawBlocks, self.cwd)
    inobj.InodeNumberToInode()
    block_index = 0
    while block_index <= (inobj.inode.size // BLOCK_SIZE):
      block = self.FileObject.RawBlocks.Get(inobj.inode.block_numbers[block_index])
      if block_index == (inobj.inode.size // BLOCK_SIZE):
        end_position = inobj.inode.size % BLOCK_SIZE
      else:
        end_position = BLOCK_SIZE
      current_position = 0
      while current_position < end_position:
        entryname = block[current_position:current_position+MAX_FILENAME]
        entryinode = block[current_position+MAX_FILENAME:current_position+FILE_NAME_DIRENTRY_SIZE]
        entryinodenumber = int.from_bytes(entryinode, byteorder='big')
        inobj2 = InodeNumber(self.FileObject.RawBlocks, entryinodenumber)
        inobj2.InodeNumberToInode()
        if inobj2.inode.type == INODE_TYPE_DIR:
          print ("[" + str(inobj2.inode.refcnt) + "]:" + entryname.decode() + "/")

          #entryname.decode is the name of the dir or a file
          #entryinodenumber is the name of the inodenumber for that file or dir
          
          #print("entryinodenumber ", entryinodenumber)
        else:
          print ("[" + str(inobj2.inode.refcnt) + "]:" + entryname.decode())
          
          #print("entryinodenumber ", entryinodenumber)

        current_position += FILE_NAME_DIRENTRY_SIZE
      block_index += 1
    return 0

  # implements cat (print file contents)
  def cat(self, filename):
    i = self.FileObject.Lookup(filename, self.cwd)
    if i == -1:
      print ("Error: not found\n")
      return -1
    inobj = InodeNumber(self.FileObject.RawBlocks,i)
    inobj.InodeNumberToInode()
    if inobj.inode.type != INODE_TYPE_FILE:
      print ("Error: not a file\n")
      return -1
    data, errorcode = self.FileObject.Read(i, 0, MAX_FILE_SIZE)
    if errorcode[0] == -1:
      print ("Error: " + errorcode[-1])
      return -1
    print (data.decode())
    return 0

  # implements showblock (log block n contents)
  def showblock(self, n):

    try:
      n = int(n)
    except ValueError:
      print('Error: ' + n + ' not a valid Integer')
      return -1

    if n < 0 or n >= TOTAL_NUM_BLOCKS:
      print('Error: block number ' + str(n) + ' not in valid range [0, ' + str(TOTAL_NUM_BLOCKS - 1) + ']')
      return -1
    logging.info('Block (strings in block) [' + str(n) + '] : \n' + str((self.FileObject.RawBlocks.Get(n).decode(encoding='UTF-8',errors='ignore'))))
    logging.info('Block (raw hex block) [' + str(n) + '] : \n' + str((self.FileObject.RawBlocks.Get(n).hex())))
    return 0

# implements showblockslice (log slice of block n contents)
  def showblockslice(self, n, start, end):

    try:
      n = int(n)
    except ValueError:
      print('Error: ' + n + ' not a valid Integer')
      return -1
    try:
      start = int(start)
    except ValueError:
      print('Error: ' + start + ' not a valid Integer')
      return -1
    try:
      end = int(end)
    except ValueError:
      print('Error: ' + end + ' not a valid Integer')
      return -1

    if n < 0 or n >= TOTAL_NUM_BLOCKS:
      print('Error: block number ' + str(n) + ' not in valid range [0, ' + str(TOTAL_NUM_BLOCKS - 1) + ']')
      return -1
    if start < 0 or start >= BLOCK_SIZE:
      print('Error: start ' + str(start) + 'not in valid range [0, ' + str(BLOCK_SIZE-1) + ']')
      return -1
    if end < 0 or end >= BLOCK_SIZE or end <= start:
      print('Error: end ' + str(end) + 'not in valid range [0, ' + str(BLOCK_SIZE-1) + ']')
      return -1

    wholeblock = self.FileObject.RawBlocks.Get(n)
#    logging.info('Block (strings in block) [' + str(n) + '] : \n' + str((wholeblock[start:end+1].decode(encoding='UTF-8',errors='ignore'))))
    logging.info('Block (raw hex block) [' + str(n) + '] : \n' + str((wholeblock[start:end+1].hex())))
    return 0


  # implements showinode (log inode i contents)
  def showinode(self, i):

    try:
      i = int(i)
    except ValueError:
      print('Error: ' + i + ' not a valid Integer')
      return -1

    if i < 0 or i >= MAX_NUM_INODES:
      print('Error: inode number ' + str(i) + ' not in valid range [0, ' + str(MAX_NUM_INODES - 1) + ']')
      return -1

    inobj = InodeNumber(self.FileObject.RawBlocks, i)
    inobj.InodeNumberToInode()
    inode = inobj.inode
    inode.Print()
    return 0

  # implements showfsconfig (log fs config contents)
  def showfsconfig(self):
    self.FileObject.RawBlocks.PrintFSInfo()
    return 0

  # implements load (load the specified dump file)
  def load(self, dumpfilename):
    if not os.path.isfile(dumpfilename):
      print("Error: Please provide valid file")
      return -1
    self.FileObject.RawBlocks.LoadFromDisk(dumpfilename)
    self.cwd = 0
    return 0

  # implements save (save the file system contents to specified dump file)
  def save(self, dumpfilename):
    self.FileObject.RawBlocks.DumpToDisk(dumpfilename)
    return 0

  def create(self, filename):
    #def FindAvailableInode(self):
    #def FindAvailableFileEntry(self, dir):
    

    #j = self.FileObject.FindAvailableInode() #finds a free inode number
    #print(j) 
    #k = self.FileObject.FindAvailableFileEntry(self.cwd)
    #print(k)
    #s = self.FileObject.AllocateDataBlock()
    #print(s)

    
    

    
    i = self.FileObject.Lookup(filename, self.cwd)
    if i == -1:
      #print("i = self.FileObject.Lookup(filename, self.cwd) ", i)
      error = self.FileObject.Create(self.cwd, filename, 1)
      #print ("will create a file\n")
      if error[0] == -1:
        print("Error: ", error[-1])
        return -1
      
    else:
      print("this file already exist")
      return -1
    
    return 0

  def mkdir(self, dirname):

    i = self.FileObject.Lookup(dirname, self.cwd)
    if i == -1:
      self.FileObject.Create(self.cwd, dirname, 2)
      #print ("will create a file\n")
      
    else:
      print("this file already exist")
      return -1
    
    return 0
  
  def append(self, filename, data):

    

    i = self.FileObject.Lookup(filename, self.cwd)
    if i == -1:
      print ("Error: not found\n")
      return -1
    inobj = InodeNumber(self.FileObject.RawBlocks,i)
    inobj.InodeNumberToInode()
    if inobj.inode.type != INODE_TYPE_FILE:
      print ("Error: not a file\n")
      return -1
    data_read, errorcode = self.FileObject.Read(i, 0, MAX_FILE_SIZE)
    #print ("i: ", i)
    #print("data_read len ", len(data_read))
    if data_read == -1:
      self.FileObject.Write(i, 0, data.encode())
      print("Successfully appended " + str(len(data)) + " bytes.")
      
    else:
      self.FileObject.Write(i,len(data_read), data.encode())

      print("Successfully appended " + str(len(data)) + " bytes.")
      
    

    return 0

  def rm(self, filename):
    #Here, "dir" is the *inode number* of the current directory and "name" is the *file name* to be unlinked

    



    error_code = self.FileObject.Unlink(self.cwd, filename)
    #print("Error: ", error_code[-1])
    if error_code[0] == -1:
      print("Error: ", error_code[-1])
    return 0
    

  def Interpreter(self):
    while (True):
      command = input("[cwd=" + str(self.cwd) + "]%")
      splitcmd = command.split()
      if len(splitcmd) == 0:
        continue
      elif splitcmd[0] == "cd":
        if len(splitcmd) != 2:
          print ("Error: cd requires one argument")
        else:
          self.cd(splitcmd[1])
      elif splitcmd[0] == "cat":
        if len(splitcmd) != 2:
          print ("Error: cat requires one argument")
        else:
          self.cat(splitcmd[1])
      elif splitcmd[0] == "ls":
        self.ls()
      elif splitcmd[0] == "showblock":
        if len(splitcmd) != 2:
          print ("Error: showblock requires one argument")
        else:
          self.showblock(splitcmd[1])
      elif splitcmd[0] == "showblockslice":
        if len(splitcmd) != 4:
          print ("Error: showblockslice requires three arguments")
        else:
          self.showblockslice(splitcmd[1],splitcmd[2],splitcmd[3])
      elif splitcmd[0] == "showinode":
        if len(splitcmd) != 2:
          print ("Error: showinode requires one argument")
        else:
          self.showinode(splitcmd[1])
      elif splitcmd[0] == "showfsconfig":
        if len(splitcmd) != 1:
          print ("Error: showfsconfig do not require argument")
        else:
          self.showfsconfig()
      elif splitcmd[0] == "load":
        if len(splitcmd) != 2:
          print ("Error: load requires 1 argument")
        else:
          self.load(splitcmd[1])
      elif splitcmd[0] == "save":
        if len(splitcmd) != 2:
          print ("Error: save requires 1 argument")
        else:
          self.save(splitcmd[1])
      elif splitcmd[0] == "exit":
        return
      elif splitcmd[0] == "create":
        if len(splitcmd) != 2:
          print("Error: create requires 1 argument")
        else:
          self.create(splitcmd[1])
      elif splitcmd[0] == "mkdir":
        if len(splitcmd) != 2:
          print("Error: mkdir requires 1 argument")
        else:
          self.mkdir(splitcmd[1])
      elif splitcmd[0] == "append":
        if len(splitcmd) != 3:
          print ("Error: append requires two arguments")
        else:
          self.append(splitcmd[1],splitcmd[2])
      elif splitcmd[0] == "rm":
        if len(splitcmd) != 2:
          print ("Error: rm requires one argument")
        else:
          self.rm(splitcmd[1])
      else:
        print ("command " + splitcmd[0] + " not valid.\n")


if __name__ == "__main__":

  # Initialize file for logging
  # Change logging level to INFO to remove debugging messages
  logging.basicConfig(filename='memoryfs.log', filemode='w', level=logging.DEBUG)


  # Construct the argument parser
  ap = argparse.ArgumentParser()

  ap.add_argument('-nb', '--total_num_blocks', type=int, help='an integer value')
  ap.add_argument('-bs', '--block_size', type=int, help='an integer value')
  ap.add_argument('-ni', '--max_num_inodes', type=int, help='an integer value')
  ap.add_argument('-is', '--inode_size', type=int, help='an integer value')

  # Other than FS args, consecutive args will be captured in by 'arg' as list
  ap.add_argument('arg', nargs='*')

  args = ap.parse_args()

  # Initialize empty file system data
  logging.info('Initializing data structures...')
  RawBlocks = DiskBlocks(args)
  boot_block = b'\x12\x34\x56\x78' # constant 12345678 stored as beginning of boot block; no need to change this
  RawBlocks.InitializeBlocks(boot_block)


  # Print file system information and contents of first few blocks to memoryfs.log
  RawBlocks.PrintFSInfo()
  RawBlocks.PrintBlocks("Initialized",0,16)

  # Initialize FileObject inode
  FileObject = FileName(RawBlocks)

  # reload the global variables (in case they changed due to command line inputs)
  from memoryfs import *

  # Initalize root inode
  FileObject.InitRootInode()

  # Redirect INFO logs to console as well
  console_handler = logging.StreamHandler()
  console_handler.setLevel(logging.INFO)
  logging.getLogger().addHandler(console_handler)

  # Run the interactive shell interpreter
  myshell = FSShell(FileObject)
  myshell.Interpreter()

