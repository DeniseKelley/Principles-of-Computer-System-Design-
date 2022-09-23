import pickle, logging


#from macpath import dirname 

##### File system constants


# Core parameters
# Total number of blocks in raw strorage
TOTAL_NUM_BLOCKS = 256
# Block size (in Bytes)
BLOCK_SIZE = 128
# Maximum number of inodes
MAX_NUM_INODES = 16
# Size of an inode (in Bytes)
INODE_SIZE = 16
# Maximum file name (in characters)
MAX_FILENAME = 12
# Number of Bytes to store an inode number in directory entry
INODE_NUMBER_DIRENTRY_SIZE = 4

# Derived parameters
# Number of inodes that fit in a block
INODES_PER_BLOCK = BLOCK_SIZE // INODE_SIZE

# To be consistent with book, block 0 is root block, 1 superblock
# Bitmap of free blocks starts at offset 2
FREEBITMAP_BLOCK_OFFSET = 2

# Number of blocks needed for free bitmap
# For simplicity, we assume each entry in the bitmap is a Byte in length
# This allows us to avoid bit-wise operations
FREEBITMAP_NUM_BLOCKS = TOTAL_NUM_BLOCKS // BLOCK_SIZE

# inode table starts at offset 2 + FREEBITMAP_NUM_BLOCKS
INODE_BLOCK_OFFSET = 2 + FREEBITMAP_NUM_BLOCKS

# inode table size
INODE_NUM_BLOCKS = (MAX_NUM_INODES * INODE_SIZE) // BLOCK_SIZE

# maximum number of blocks indexed by inode
# This implementation hardcodes:
#   4 bytes for size
#   2 bytes for type
#   2 bytes for refcnt
#   4 bytes per block number index
# In total, 4+2+2=8 bytes are used for size+type+refcnt, remaining bytes for block numbers
MAX_INODE_BLOCK_NUMBERS = (INODE_SIZE - 8) // 4

# maximum size of a file
# maximum number of entries in an inode's block_numbers[], times block size
MAX_FILE_SIZE = MAX_INODE_BLOCK_NUMBERS*BLOCK_SIZE

# Data blocks start at INODE_BLOCK_OFFSET + INODE_NUM_BLOCKS
DATA_BLOCKS_OFFSET = INODE_BLOCK_OFFSET + INODE_NUM_BLOCKS

# Number of data blocks
DATA_NUM_BLOCKS = TOTAL_NUM_BLOCKS - DATA_BLOCKS_OFFSET

# Size of a directory entry: file name plus inode size
FILE_NAME_DIRENTRY_SIZE = MAX_FILENAME + INODE_NUMBER_DIRENTRY_SIZE

# Number of filename+inode entries that can be stored in a single block
FILE_ENTRIES_PER_DATA_BLOCK = BLOCK_SIZE // FILE_NAME_DIRENTRY_SIZE


# Supported inode types
INODE_TYPE_INVALID = 0
INODE_TYPE_FILE = 1
INODE_TYPE_DIR = 2
INODE_TYPE_SYM = 3

#### BLOCK LAYER 

class DiskBlocks():
  def __init__(self, args):

    self.HandleFSConstants(args)
    # This class stores the raw block array
    self.block = []                                            
    # Initialize raw blocks 
    for i in range (0, TOTAL_NUM_BLOCKS):  #TOTAL_NUM_BLOCKS 256
      putdata = bytearray(BLOCK_SIZE)      #BLOCK_SIZE       128
      self.block.insert(i,putdata)

  #HandleFSConstants: Modify the FS constants if provided in command line argument

  def HandleFSConstants(self, args):

    if args.total_num_blocks:
      global TOTAL_NUM_BLOCKS
      TOTAL_NUM_BLOCKS = args.total_num_blocks

    if args.block_size:
      global BLOCK_SIZE
      BLOCK_SIZE = args.block_size

    if args.max_num_inodes:
      global MAX_NUM_INODES
      MAX_NUM_INODES = args.max_num_inodes

    if args.inode_size:
      global INODE_SIZE
      INODE_SIZE = args.inode_size


    # Modify Derived parameters
    global INODES_PER_BLOCK, FREEBITMAP_BLOCK_OFFSET, FREEBITMAP_NUM_BLOCKS, \
      INODE_BLOCK_OFFSET, MAX_INODE_BLOCK_NUMBERS, MAX_FILE_SIZE, DATA_BLOCKS_OFFSET, \
      DATA_NUM_BLOCKS, FILE_NAME_DIRENTRY_SIZE, FILE_ENTRIES_PER_DATA_BLOCK, INODE_NUM_BLOCKS

    # Number of inodes that fit in a block
    INODES_PER_BLOCK = BLOCK_SIZE // INODE_SIZE   #128/16 = 8

    FREEBITMAP_NUM_BLOCKS = TOTAL_NUM_BLOCKS // BLOCK_SIZE  #256/128 = 2 

    # inode table starts at offset 2 + FREEBITMAP_NUM_BLOCKS
    INODE_BLOCK_OFFSET = 2 + FREEBITMAP_NUM_BLOCKS          #2+2 = 4

    # inode table size
    INODE_NUM_BLOCKS = (MAX_NUM_INODES * INODE_SIZE) // BLOCK_SIZE     # 16*16//128 = 2

    MAX_INODE_BLOCK_NUMBERS = (INODE_SIZE - 8) // 4                    #16-8 // 4 = 14

    MAX_FILE_SIZE = MAX_INODE_BLOCK_NUMBERS * BLOCK_SIZE               #14 *128 = 1792

    # Data blocks start at INODE_BLOCK_OFFSET + INODE_NUM_BLOCKS
    DATA_BLOCKS_OFFSET = INODE_BLOCK_OFFSET + INODE_NUM_BLOCKS          #4+2 = 6

    # Number of data blocks
    DATA_NUM_BLOCKS = TOTAL_NUM_BLOCKS - DATA_BLOCKS_OFFSET

    # Size of a directory entry: file name plus inode size
    FILE_NAME_DIRENTRY_SIZE = MAX_FILENAME + INODE_NUMBER_DIRENTRY_SIZE

    # Number of filename+inode entries that can be stored in a single block
    FILE_ENTRIES_PER_DATA_BLOCK = BLOCK_SIZE // FILE_NAME_DIRENTRY_SIZE

  ## Put: interface to write a raw block of data to the block indexed by block number
## Blocks are padded with zeroes up to BLOCK_SIZE

  def Put(self, block_number, block_data):

   

    logging.debug ('Put: block number ' + str(block_number) + ' len ' + str(len(block_data)) + '\n' + str(block_data.hex()))
    if len(block_data) > BLOCK_SIZE:
      logging.error('Put: Block larger than BLOCK_SIZE: ' + str(len(block_data)))
      quit()

    if block_number in range(0,TOTAL_NUM_BLOCKS): 
      # ljust does the padding with zeros
      putdata = bytearray(block_data.ljust(BLOCK_SIZE,b'\x00'))
      # Write block
      self.block[block_number] = putdata
      return 0
    else:
      logging.error('Put: Block out of range: ' + str(block_number))
      quit()


## Get: interface to read a raw block of data from block indexed by block number
## Equivalent to the textbook's BLOCK_NUMBER_TO_BLOCK(b)

  def Get(self, block_number):
    

    logging.debug ('Get: ' + str(block_number))
    if block_number in range(0,TOTAL_NUM_BLOCKS):
      # logging.debug ('\n' + str((self.block[block_number]).hex()))
      return self.block[block_number]

    logging.error('Get: Block number larger than TOTAL_NUM_BLOCKS: ' + str(block_number))
    quit()


## Serializes and saves block[] data structure to a disk file

  def DumpToDisk(self, filename):

    logging.info("Dumping pickled blocks to file " + filename)
    file = open(filename,'wb')
    file_system_constants = "BS_" + str(BLOCK_SIZE) + "_NB_" + str(TOTAL_NUM_BLOCKS) + "_IS_" + str(INODE_SIZE) \
                            + "_MI_" + str(MAX_NUM_INODES) + "_MF_" + str(MAX_FILENAME) + "_IDS_" + str(INODE_NUMBER_DIRENTRY_SIZE)
    pickle.dump(file_system_constants, file)
    pickle.dump(self.block, file)

    file.close()


## Loads block[] data structure from a disk file

  def LoadFromDisk(self, filename):

    logging.info("Reading blocks from pickled file " + filename)
    file = open(filename,'rb')
    file_system_constants = "BS_" + str(BLOCK_SIZE) + "_NB_" + str(TOTAL_NUM_BLOCKS) + "_IS_" + str(INODE_SIZE) \
                            + "_MI_" + str(MAX_NUM_INODES) + "_MF_" + str(MAX_FILENAME) + "_IDS_" + str(
      INODE_NUMBER_DIRENTRY_SIZE)

    try:
      read_file_system_constants = pickle.load(file)

      if file_system_constants != read_file_system_constants:
        print('Error: File System constants of File :' + read_file_system_constants
            + ' do not match with current file system constants :' + file_system_constants)
        return -1

      block = pickle.load(file)
      for i in range(0, TOTAL_NUM_BLOCKS):
        self.Put(i,block[i])
      return 0
    except TypeError:
      print("Error: File not in proper format, encountered type error ")
      return -1
    except EOFError:
      print("Error: File not in proper format, encountered EOFError error ")
      return -1
    finally:
      file.close()


## Initialize blocks, either from a clean slate (cleanslate == True), or from a pickled dump file with prefix
    
  def InitializeBlocks(self, prefix):

    # Block 0: No real boot code here, just write the given prefix
    self.Put(0,prefix)

    # Block 1: Superblock contains basic file system constants
    # First, we write it as a list
    superblock = [TOTAL_NUM_BLOCKS, BLOCK_SIZE, MAX_NUM_INODES, INODE_SIZE]
    # Now we serialize it into a byte array
    self.Put(1,pickle.dumps(superblock))

    # Blocks 2-TOTAL_NUM_BLOCKS are initialized with zeroes
    #   Free block bitmap: All blocks start free, so safe to initialize with zeroes
    #   Inode table: zero indicates an invalid inode, so also safe to initialize with zeroes
    #   Data blocks: safe to init with zeroes
    zeroblock = bytearray(BLOCK_SIZE)
    for i in range(FREEBITMAP_BLOCK_OFFSET, TOTAL_NUM_BLOCKS):
      self.Put(i, zeroblock)


## Prints out file system information

  def PrintFSInfo(self):
    logging.info ('#### File system information:')
    logging.info ('Number of blocks          : ' + str(TOTAL_NUM_BLOCKS))
    logging.info ('Block size (Bytes)        : ' + str(BLOCK_SIZE))
    logging.info ('Number of inodes          : ' + str(MAX_NUM_INODES))
    logging.info ('inode size (Bytes)        : ' + str(INODE_SIZE))
    logging.info ('inodes per block          : ' + str(INODES_PER_BLOCK))
    logging.info ('Free bitmap offset        : ' + str(FREEBITMAP_BLOCK_OFFSET))
    logging.info ('Free bitmap size (blocks) : ' + str(FREEBITMAP_NUM_BLOCKS))
    logging.info ('Inode table offset        : ' + str(INODE_BLOCK_OFFSET))
    logging.info ('Inode table size (blocks) : ' + str(INODE_NUM_BLOCKS))
    logging.info ('Max blocks per file       : ' + str(MAX_INODE_BLOCK_NUMBERS))
    logging.info ('Data blocks offset        : ' + str(DATA_BLOCKS_OFFSET))
    logging.info ('Data block size (blocks)  : ' + str(DATA_NUM_BLOCKS))
    logging.info ('Raw block layer layout: (B: boot, S: superblock, F: free bitmap, I: inode, D: data')
    Layout = "BS"
    Id = "01"
    IdCount = 2
    for i in range(0,FREEBITMAP_NUM_BLOCKS):
      Layout += "F"
      Id += str(IdCount)
      IdCount = (IdCount + 1) % 10
    for i in range(0,INODE_NUM_BLOCKS):
      Layout += "I"
      Id += str(IdCount)
      IdCount = (IdCount + 1) % 10
    for i in range(0,DATA_NUM_BLOCKS):
      Layout += "D"
      Id += str(IdCount)
      IdCount = (IdCount + 1) % 10
    logging.info (Id)
    logging.info (Layout)


## Prints to screen block contents, from min to max

  def PrintBlocks(self,tag,min,max):
    logging.info ('#### Raw disk blocks: ' + tag)
    for i in range(min,max):
      logging.info ('Block [' + str(i) + '] : ' + str((self.Get(i)).hex()))



#### INODE LAYER 


# This class holds an inode object in memory and provides methods to modify inodes
# The pattern here is:
#  0. Initialize the object
#  1. Read an Inode object from a byte array read from raw block storage (InodeFromBytearray)
#     An inode is stored in a raw block as a byte array:
#       size (bytes 0..3), type (bytes 4..5), refcnt (bytes 6..7), block_numbers (bytes 8..)
#  2. Update inode (e.g. size, refcnt, block numbers) depending on file system operation
#     Using various Set() methods
#  3. Serialize and write Inode object back to raw block storage (InodeToBytearray)

class Inode():
  def __init__(self):

    # inode is initialized empty
    self.type = INODE_TYPE_INVALID
    self.size = 0
    self.refcnt = 0

    # We store inode block_numbers as a list
    self.block_numbers = []

    # initialize list with zeroes
    for i in range(0,MAX_INODE_BLOCK_NUMBERS):
      self.block_numbers.append(0)


## Set inode object values from a raw bytearray
## This is used when we read an inode from raw block storage to the inode data structure

  def InodeFromBytearray(self,b):

    if len(b) > INODE_SIZE:
      logging.error ('InodeFromBytearray: exceeds inode size ' + str(b))
      quit()

    # slice the raw bytes for the different fields
    # size is 4 bytes, type 2 bytes, refcnt 2 bytes
    size_slice = b[0:4]
    type_slice = b[4:6]
    refcnt_slice = b[6:8]

    # converts from raw bytes to integers using big-endian 
    # store scalars 
    self.size = int.from_bytes(size_slice, byteorder='big') 
    self.type = int.from_bytes(type_slice, byteorder='big') 
    self.refcnt = int.from_bytes(refcnt_slice, byteorder='big')

    # each block number entry is 4 bytes, big-endian
    for i in range(0,MAX_INODE_BLOCK_NUMBERS):
      start = 8 + i*4
      blocknumber_slice = b[start:start+4]
      self.block_numbers[i] = int.from_bytes(blocknumber_slice, byteorder='big') 


## Create a raw byte array, serializing Inode object values to prepare to write
## This is used when we write an inode to raw block storage

  def InodeToBytearray(self):

    # Temporary bytearray - we'll load it with the different inode fields
    temparray = bytearray(INODE_SIZE)

    # We assume size is 4 bytes, and we store it in Big Endian format
    intsize = self.size
    temparray[0:4] = intsize.to_bytes(4, 'big')

    # We assume type is 2 bytes, and we store it in Big Endian format
    inttype = self.type
    temparray[4:6] = inttype.to_bytes(2, 'big')

    # We assume refcnt is 2 bytes, and we store it in Big Endian format
    intrefcnt = self.refcnt
    temparray[6:8] = intrefcnt.to_bytes(2, 'big')

    # We assume each block number is 4 bytes, and we store each in Big Endian format
    for i in range(0,MAX_INODE_BLOCK_NUMBERS):
      start = 8 + i*4
      intbn = self.block_numbers[i]
      temparray[start:start+4] = intbn.to_bytes(4, 'big')

    # Return the byte array
    return temparray


## Prints out this inode object's information to the log

  def Print(self):
    logging.info ('Inode size   : ' + str(self.size))
    logging.info ('Inode type   : ' + str(self.type))
    logging.info ('Inode refcnt : ' + str(self.refcnt))
    logging.info ('Block numbers: ')
    s = ""
    for i in range(0,MAX_INODE_BLOCK_NUMBERS):
      s += str(self.block_numbers[i])
      s += ","
    logging.info (s)


#### Inode number layer


class InodeNumber():
  def __init__(self, RawBlocks, number):

    # This object stores the inode data structure
    self.inode = Inode()

    # This stores the inode number
    if number > MAX_NUM_INODES:
      logging.error ('InodeNumber: inode number exceeds limit: ' + str(number))
      quit()
    self.inode_number = number

    # Raw block storage
    self.RawBlocks = RawBlocks


## Load inode data structure from raw storage, indexed by inode number
## The inode data structure loaded from raw storage goes in the self.inode object

  def InodeNumberToInode(self):

    logging.debug('InodeNumberToInode: ' + str(self.inode_number))

    # locate which block has the inode we want
    raw_block_number = INODE_BLOCK_OFFSET + ((self.inode_number * INODE_SIZE) // BLOCK_SIZE)
    
    

    # Get the entire block containing inode from raw storage
    tempblock = self.RawBlocks.Get(raw_block_number)

    # Find the slice of the block for this inode_number
    start = (self.inode_number * INODE_SIZE) % BLOCK_SIZE
    end = start + INODE_SIZE

    # extract byte array for this inode
    tempinode = tempblock[start:end]

    # load inode from byte array 
    self.inode.InodeFromBytearray(tempinode)

    logging.debug ('InodeNumberToInode : inode_number ' + str(self.inode_number) + ' raw_block_number: ' + str(raw_block_number) + ' slice start: ' + str(start) + ' end: ' + str(end))
    logging.debug ('tempinode: ' + str(tempinode.hex()))


## Stores (Put) this inode into raw storage
## Since an inode is a slice of a block, we first Get() the block, update the slice, and Put()

  def StoreInode(self):

    logging.debug('StoreInode: ' + str(self.inode_number))

    # locate which block has the inode we want
    raw_block_number = INODE_BLOCK_OFFSET + ((self.inode_number * INODE_SIZE) // BLOCK_SIZE)
    logging.debug('StoreInode: raw_block_number ' + str(raw_block_number))

    # Get the entire block containing inode from raw storage
    tempblock = self.RawBlocks.Get(raw_block_number)
    logging.debug('StoreInode: tempblock:\n' + str(tempblock.hex()))

    # Find the slice of the block for this inode_number
    start = (self.inode_number * INODE_SIZE) % BLOCK_SIZE
    end = start + INODE_SIZE
    logging.debug('StoreInode: start: ' + str(start) + ', end: ' + str(end))

    # serialize inode into byte array
    inode_bytearray = self.inode.InodeToBytearray()

    # Update slice of block with this inode's bytearray
    tempblock[start:end] = inode_bytearray     
    logging.debug('StoreInode: tempblock:\n' + str(tempblock.hex()))

    # Update raw storage with new inode
    self.RawBlocks.Put(raw_block_number, tempblock)


## Returns a block of data from raw storage, given its offset
## Equivalent to textbook's INODE_NUMBER_TO_BLOCK

  def InodeNumberToBlock(self, offset):

    logging.debug ('InodeNumberToBlock: ' + str(offset))

    # Load object's inode 
    self.InodeNumberToInode()

    # Calculate offset
    o = offset // BLOCK_SIZE

    # Retrieve block indexed by offset
    # as in the textbook's INDEX_TO_BLOCK_NUMBER
    b = self.inode.block_numbers[o] 
    block = self.RawBlocks.Get(b)
    return block


#### File name layer


## This class implements methods for the file name layer

class FileName():
  def __init__(self, RawBlocks):
    self.RawBlocks = RawBlocks


## This helper function extracts a file name string from a directory data block
## The index selects which file name entry to extract within the block - e.g. index 0 is the first file name, 1 second file name

  def HelperGetFilenameString(self, block, index):

    logging.debug ('HelperGetFilenameString: ' + str(block.hex()) + ', ' + str(index))

    # Locate bytes that store string - first MAX_FILENAME characters aligned by MAX_FILENAME + INODE_NUMBER_DIRENTRY_SIZE
    string_start = index * FILE_NAME_DIRENTRY_SIZE
    string_end = string_start + MAX_FILENAME

    return block[string_start:string_end]


## This helper function extracts an inode number from a directory data block
## The index selects which entry to extract within the block - e.g. index 0 is the inode for the first file name, 1 second file name

  def HelperGetFilenameInodeNumber(self, block, index):

    logging.debug ('HelperGetFilenameInodeNumber: ' + str(block.hex()) + ', ' + str(index))

    # Locate bytes that store inode
    inode_start = (index * FILE_NAME_DIRENTRY_SIZE) + MAX_FILENAME
    inode_end = inode_start + INODE_NUMBER_DIRENTRY_SIZE
    inodenumber_slice = block[inode_start:inode_end]

    return int.from_bytes(inodenumber_slice, byteorder='big')


## This inserts a (filename,inodenumber) entry into the tail end of the table in a directory data block of insert_into InodeNumber()
## Used when adding an entry to a directory
## insert_into is an InodeNumber() object; filename is a string; inodenumber is an integer

  def InsertFilenameInodeNumber(self, insert_to, filename, inodenumber):



    logging.debug ('InsertFilenameInodeNumber: ' + str(filename) + ', ' + str(inodenumber))

    if len(filename) > MAX_FILENAME:
      logging.error ('InsertFilenameInodeNumber: file name exceeds maximum')
      quit()

    if insert_to.inode.type != INODE_TYPE_DIR:
      logging.error ('InsertFilenameInodeNumber: not a directory inode: ' + str(insert_to.inode.type))
      quit()

    # We insert a new entry at the end of the existing table, so determine its position based on inode's size
    index = insert_to.inode.size
    if index >= MAX_FILE_SIZE:
      logging.error ('InsertFilenameInodeNumber: no space for another entry in inode')
      quit()

    # Check if we need to allocate another data block for this inode
    # this happens when the index spills over to the next block; index == 0 is a special case as an inode is
    # initialized with one data block, so no need to allocate
    block_number_index = index // BLOCK_SIZE
    if index % BLOCK_SIZE == 0:
      if index != 0:
        # Allocate the block
        new_block = self.AllocateDataBlock()
        # update inode (it will be written to raw storage before the method returns)
        insert_to.inode.block_numbers[block_number_index] = new_block
      
    # Retrieve the data block where the new (filename,inodenumber) will be stored
    block_number = insert_to.inode.block_numbers[block_number_index]
    block = self.RawBlocks.Get(block_number)

    # Compute module of index to locate entry within block
    index_modulo = index % BLOCK_SIZE

    # Locate the byte slice holding the file name with MAX_FILENAME size
    string_start = index_modulo 
    string_end = string_start + MAX_FILENAME
    stringbyte = bytearray(filename,"utf-8")

    # Locate the byte slice holding the inode number with INODE_NUMBER_DIRENTRY_SIZE size
    inode_start = index_modulo + MAX_FILENAME
    inode_end = inode_start + INODE_NUMBER_DIRENTRY_SIZE

    logging.debug ('InsertFilenameInodeNumber: \n' + str(block.hex()))
    logging.debug ('InsertFilenameInodeNumber: inode_start ' + str(inode_start) + ', inode_end ' + str(inode_end))
    logging.debug ('InsertFilenameInodeNumber: string_start ' + str(string_start) + ', string_end ' + str(string_end))

    # Update and write data block with (filename,inode) mapping
    block[inode_start:inode_end] = inodenumber.to_bytes(INODE_NUMBER_DIRENTRY_SIZE, 'big')
    block[string_start:string_end] = bytearray(stringbyte.ljust(MAX_FILENAME,b'\x00'))
    self.RawBlocks.Put(block_number, block)

    # Increment size, and write inode
    insert_to.inode.size += FILE_NAME_DIRENTRY_SIZE
    insert_to.StoreInode()
    
  



## Lookup string filename in the context of inode dir - same as textbook's LOOKUP

  def Lookup(self, filename, dir):

    logging.debug ('Lookup: ' + str(filename) + ', ' + str(dir))

    # Initialize inode_number object from raw storage
    inode_number = InodeNumber(self.RawBlocks, dir)
    inode_number.InodeNumberToInode()

    if inode_number.inode.type != INODE_TYPE_DIR:
      logging.error ("Lookup: not a directory inode: " + str(dir) + " , " + str(inode_number.inode.type))
      return -1

    offset = 0
    scanned = 0

    # Iterate over all data blocks indexed by directory inode, until we reach inode's size
    while offset < inode_number.inode.size:

      # Retrieve directory data block given current offset
      b = inode_number.InodeNumberToBlock(offset)

      # A directory data block has multiple (filename,inode) entries 
      # Iterate over file entries to search for matches
      for i in range (0, FILE_ENTRIES_PER_DATA_BLOCK):

        # don't search beyond file size
        if inode_number.inode.size > scanned:

          scanned += FILE_NAME_DIRENTRY_SIZE
 
          # Extract padded MAX_FILENAME string as a bytearray from data block for comparison
          filestring = self.HelperGetFilenameString(b,i)

          logging.debug ("Lookup for " + filename + " in " + str(dir) + ": searching string " + str(filestring))

          # Pad filename with zeroes and make it a byte array
          padded_filename = bytearray(filename,"utf-8")
          padded_filename = bytearray(padded_filename.ljust(MAX_FILENAME,b'\x00'))

          # these are now two byte arrays of the same MAX_FILENAME size, ready for comparison 
          if filestring == padded_filename:

            # On a match, retrieve and return inode number
            fileinode = self.HelperGetFilenameInodeNumber(b,i)
            logging.debug ("Lookup successful: " + str(fileinode))
            return fileinode

      # Skip to the next block, back to while loop
      offset += BLOCK_SIZE

    logging.debug ("Lookup: file not found: " + str(filename) + " in " + str(dir))
    return -1


## Scans inode table to find an available entry

  def FindAvailableInode(self):

    logging.debug ('FindAvailableInode: ')

    for i in range (0, MAX_NUM_INODES):

      # Initialize inode_number object from raw storage
      inode_number = InodeNumber(self.RawBlocks, i)
      inode_number.InodeNumberToInode()

      if inode_number.inode.type == INODE_TYPE_INVALID:
        logging.debug ("FindAvailableInode: " + str(i))
        return i

    logging.debug ("FindAvailableInode: no available inodes")
    return -1


## Returns index to an available entry in directory data block

  
  def FindAvailableFileEntry(self, dir):
    

    logging.debug ('FindAvailableFileEntry: dir: ' + str(dir))

    # Initialize inode_number object from raw storage
    inode_number = InodeNumber(self.RawBlocks, dir)
    inode_number.InodeNumberToInode()

    # Check if there is still room for another (filename,inode) entry
    # the inode cannot exceed maximum size 
    if inode_number.inode.size >= MAX_FILE_SIZE:
      logging.debug ("FindAvailableFileEntry: no entries available")
      return -1

    logging.debug ("FindAvailableFileEntry: " + str(inode_number.inode.size))
    return inode_number.inode.size
  
## Allocate a data block, update free bitmap, and return its number

  def AllocateDataBlock(self):

    logging.debug ('AllocateDataBlock: ')

    # Scan through all available data blocks
    for block_number in range (DATA_BLOCKS_OFFSET, TOTAL_NUM_BLOCKS):

      # GET() raw block that stores the bitmap entry for block_number
      bitmap_block = FREEBITMAP_BLOCK_OFFSET + (block_number // BLOCK_SIZE)
      block = self.RawBlocks.Get(bitmap_block)

      # Locate proper byte within the block
      byte_bitmap = block[block_number % BLOCK_SIZE]

      # Data block block_number is free
      if byte_bitmap == 0:
        # Mark it as used in bitmap
        block[block_number % BLOCK_SIZE] = 1
        self.RawBlocks.Put(bitmap_block, block)
        logging.debug ('AllocateDataBlock: allocated ' + str(block_number))
        return block_number

    logging.debug ('AllocateDataBlock: no free data blocks available')
    quit()


## Initializes the root inode

  def InitRootInode(self):

    # Root inode has well-known value 0
    root_inode = InodeNumber(self.RawBlocks, 0)
    root_inode.InodeNumberToInode()
    root_inode.inode.type = INODE_TYPE_DIR
    root_inode.inode.size = 0
    root_inode.inode.refcnt = 1
    # Allocate one data block and set as first entry in block_numbers[]
    root_inode.inode.block_numbers[0] = self.AllocateDataBlock()
    # Add "." 
    self.InsertFilenameInodeNumber(root_inode, ".", 0)
    root_inode.inode.Print()
    root_inode.StoreInode()


## Create a file system object
## type determines the type of file system object to be created
## dir is the inode number of a directory to hold the object
## name is the object's name

  def Create(self, dir, name, type):

    

    logging.debug ("Create: dir: " + str(dir) + ", name: " + str(name) + ", type: " + str(type))

    # Ensure type is valid
    if not (type == INODE_TYPE_FILE or type == INODE_TYPE_DIR):
      logging.debug ("ERROR_CREATE_INVALID_TYPE " + str(type))
      return -1, "ERROR_CREATE_INVALID_TYPE"

    # Find if there is an available inode
    inode_position = self.FindAvailableInode()
    #print("inode_position ", inode_position)
    if inode_position == -1:
      logging.debug ("ERROR_CREATE_INODE_NOT_AVAILABLE")
      return -1, "ERROR_CREATE_INODE_NOT_AVAILABLE"

    # Obtain dir_inode_number_inode, ensure it is a directory
    dir_inode = InodeNumber(self.RawBlocks, dir)
    dir_inode.InodeNumberToInode()
    if dir_inode.inode.type != INODE_TYPE_DIR:
      logging.debug ("ERROR_CREATE_INVALID_DIR " + str(dir))
      return -1, "ERROR_CREATE_INVALID_DIR"

    # Find available slot in directory data block
    fileentry_position = self.FindAvailableFileEntry(dir)
    #print("fileentry_position ", fileentry_position)
    if fileentry_position == -1:
      logging.debug ("ERROR_CREATE_DATA_BLOCK_NOT_AVAILABLE")
      return -1, "ERROR_CREATE_DATA_BLOCK_NOT_AVAILABLE"

    # Ensure it's not a duplicate - if Lookup returns anything other than -1
    if self.Lookup(name, dir) != -1:
      logging.debug ("ERROR_CREATE_ALREADY_EXISTS " + str(name))
      return -1, "ERROR_CREATE_ALREADY_EXISTS"

    logging.debug ("Create: inode_position: " + str(inode_position) + ", fileentry_position: " + str(fileentry_position))

    if type == INODE_TYPE_DIR:
      # Store inode of new directory
      newdir_inode = InodeNumber(self.RawBlocks, inode_position)
      newdir_inode.InodeNumberToInode()
      newdir_inode.inode.type = INODE_TYPE_DIR
      newdir_inode.inode.size = 0
      newdir_inode.inode.refcnt = 1
      # Allocate one data block and set as first entry in block_numbers[]
      newdir_inode.inode.block_numbers[0] = self.AllocateDataBlock()
      newdir_inode.StoreInode()

      # Add to directory (filename,inode) table
      self.InsertFilenameInodeNumber(dir_inode, name, inode_position)

      # Add "." to new directory
      self.InsertFilenameInodeNumber(newdir_inode, ".", inode_position)

      # Add ".." to new directory
      self.InsertFilenameInodeNumber(newdir_inode, "..", dir)

      # Update directory inode
      # increment refcnt
      dir_inode.inode.refcnt += 1
      dir_inode.StoreInode()

    elif type == INODE_TYPE_FILE:
      newfile_inode = InodeNumber(self.RawBlocks, inode_position)
      newfile_inode.InodeNumberToInode()
      newfile_inode.inode.type = INODE_TYPE_FILE
      newfile_inode.inode.size = 0
      newfile_inode.inode.refcnt = 1
      # New files are not allocated any blocks; these are allocated on a Write()
      newfile_inode.StoreInode()

      # Add to parent's (filename,inode) table
      self.InsertFilenameInodeNumber(dir_inode, name, inode_position) 
    
      # Update directory inode
      # refcnt incremented by one
      dir_inode.inode.refcnt += 1
      dir_inode.StoreInode()

  

    # Return new object's inode number
    return inode_position, "SUCCESS"


## Writes data to a file, starting at offset
## offset must be less than or equal to the file's size
## data is a block array
## returns number of bytes written

  def Write(self, file_inode_number, offset, data):



    logging.debug ("Write: file_inode_number: " + str(file_inode_number) + ", offset: " + str(offset) + ", len(data): " + str(len(data)))
    # logging.debug (str(data))

    file_inode = InodeNumber(self.RawBlocks, file_inode_number)
    file_inode.InodeNumberToInode()

    if file_inode.inode.type != INODE_TYPE_FILE:
      logging.debug ("ERROR_WRITE_NOT_FILE " + str(file_inode_number))
      return -1, "ERROR_WRITE_NOT_FILE"

    if offset > file_inode.inode.size:
      logging.debug ("ERROR_WRITE_OFFSET_LARGER_THAN_SIZE " + str(offset))
      return -1, "ERROR_WRITE_OFFSET_LARGER_THAN_SIZE"

    if offset + len(data) > MAX_FILE_SIZE:
      logging.debug ("ERROR_WRITE_EXCEEDS_FILE_SIZE " + str(offset + len(data)))
      return -1, "ERROR_WRITE_EXCEEDS_FILE_SIZE"

    # initialize variables used in the while loop
    current_offset = offset
    bytes_written = 0

    # this loop iterates through one or more blocks, ending when all data is written
    while bytes_written < len(data):

      # block index corresponding to the current offset
      current_block_index = current_offset // BLOCK_SIZE

      # next block's boundary (in Bytes relative to file 0)
      next_block_boundary = (current_block_index + 1) * BLOCK_SIZE

      logging.debug ('Write: current_block_index: ' + str(current_block_index) + ' , next_block_boundary: ' + str(next_block_boundary))

      # byte position where the slice of data to write should start, within a block
      # the first time around in the loop, this may not be aligned with block boundary (i.e. 0) depending on offset
      # in subsequent iterations, it will be 0
      write_start = current_offset % BLOCK_SIZE

      # determine byte position where the writing ends
      # this may be BLOCK_SIZE if the data yet to be written spills over to the next block
      # or, it may be smaller than BLOCK_SIZE if the data ends in this block

      if (offset + len(data)) >= next_block_boundary:
        # the data length is such that it goes beyond this block, so we're writing this entire block
        write_end = BLOCK_SIZE
      else:
        # otherwise, the data is truncated within this block
        write_end = (offset + len(data)) % BLOCK_SIZE

      logging.debug ('Write: write_start: ' + str(write_start) + ' , write_end: ' + str(write_end))
        
      # retrieve index of block to be written from inode's list
      block_number = file_inode.inode.block_numbers[current_block_index]

      # if the block is not allocated, allocate
      if block_number == 0:
        new_block = self.AllocateDataBlock()
        # update inode (it will be written to raw storage before the method returns)
        file_inode.inode.block_numbers[current_block_index] = new_block
        block_number = new_block

      # first, we read the whole block from raw storage
      block = file_inode.RawBlocks.Get(block_number)

      # copy slice of data into the right position in the block
      block[write_start:write_end] = data[bytes_written:bytes_written+(write_end-write_start)]
            
      # now write modified block back to disk
      file_inode.RawBlocks.Put(block_number,block)

      # update offset, bytes written
      current_offset += write_end-write_start
      bytes_written += write_end-write_start

      logging.debug ('Write: current_offset: ' + str(current_offset) + ' , bytes_written: ' + str(bytes_written) + ' , len(data): ' + str(len(data)))

    # Update inode's metadata and write to storage
    file_inode.inode.size += bytes_written
    file_inode.StoreInode()

    return bytes_written, "SUCCESS"



  def Read(self, file_inode_number, offset, count):

    logging.debug ("Read: file_inode_number: " + str(file_inode_number) + ", offset: " + str(offset) + ", count: " + str(count))

    file_inode = InodeNumber(self.RawBlocks, file_inode_number)
    file_inode.InodeNumberToInode()

    if file_inode.inode.type != INODE_TYPE_FILE:
      logging.debug ("ERROR_READ_NOT_FILE " + str(file_inode_number))
      return -1, "ERROR_READ_NOT_FILE"

    if offset > file_inode.inode.size:
      logging.debug ("ERROR_READ_OFFSET_LARGER_THAN_SIZE " + str(offset))
      return -1, "ERROR_READ_OFFSET_LARGER_THAN_SIZE"

    # initialize variables used in the while loop
    current_offset = offset
    bytes_read = 0

    if offset + count > file_inode.inode.size:
      bytes_to_read = file_inode.inode.size - offset
    else:
      bytes_to_read = count

    read_block = bytearray(bytes_to_read)

    # this loop iterates through one or more blocks, ending when all data is read
    while bytes_read < bytes_to_read:

      # block index corresponding to the current offset
      current_block_index = current_offset // BLOCK_SIZE

      # next block's boundary (in Bytes relative to file 0)
      next_block_boundary = (current_block_index + 1) * BLOCK_SIZE

      logging.debug ('Read: current_block_index: ' + str(current_block_index) + ' , next_block_boundary: ' + str(next_block_boundary))

      read_start = current_offset % BLOCK_SIZE

      if (offset + bytes_to_read) >= next_block_boundary:
        # the data length is such that it goes beyond this block, so we're reading this entire block
        read_end = BLOCK_SIZE
      else:
        # otherwise, the data is truncated within this block
        read_end = (offset + bytes_to_read) % BLOCK_SIZE

      logging.debug ('Read: read_start: ' + str(read_start) + ' , read_end: ' + str(read_end))

      # retrieve index of block to be written from inode's list
      block_number = file_inode.inode.block_numbers[current_block_index]

      # first, we read the whole block from raw storage
      block = file_inode.RawBlocks.Get(block_number)

      # copy slice of data into the right position in the block
      read_block[bytes_read:bytes_read+(read_end-read_start)] = block[read_start:read_end]

      bytes_read += read_end-read_start
      current_offset += read_end-read_start

      logging.debug ('Read: current_offset: ' + str(current_offset) + ' , bytes_read: ' + str(bytes_read))

    return read_block, "SUCCESS"

  def Unlink(self, dir, name):

    #book page 92 Unlink(name) - Remove name from its directory. If name is the last name for a file, remove file.
    # page 100: unlink removes the binding of filename to its inode number from the directory that contains filename . 
    # The file system also puts filename ’s inode and the blocks of filename ’s inode on the free list if this 
    # binding is the last one containing the inode’s number. 

    #*************************************************************
    #dir = file_inode_number
    #*************************************************************
    
    
    # Obtain dir_inode_number_inode, ensure it is a directory
    #a) Ensure "dir" corresponds to a valid directory; if not, return an error ERROR_UNLINK_INVALID_DIR
    dir_inode = InodeNumber(self.RawBlocks, dir)
    dir_inode.InodeNumberToInode()
    
    
    if dir_inode.inode.type != INODE_TYPE_DIR:
      logging.debug ("ERROR_UNLINK_INVALID_DIR " + str(dir))
      #print("checking type")
      return -1, "ERROR_UNLINK_INVALID_DIR"
    

    #b) Ensure "name" exists in the directory; if not, return an error ERROR_UNLINK_DOESNOT_EXIST
    if self.Lookup(name, dir) == -1:
      #print("in lookup")
      logging.debug ("ERROR_UNLINK_DOESNOT_EXIST " + str(name))
      return -1, "ERROR_UNLINK_DOESNOT_EXIST"

    #i_num is the inode number for the file
    i_num = self.Lookup(name, dir)
    
    file_inode = InodeNumber(self.RawBlocks, i_num)
    file_inode.InodeNumberToInode()


    #c) Ensure "name" refers to a file of type INODE_TYPE_FILE; if not, return error ERROR_UNLINK_NOT_FILE
    if file_inode.inode.type != INODE_TYPE_FILE:
      logging.debug ("ERROR_UNLINK_NOT_FILE " + str(i_num))
      return -1, "ERROR_UNLINK_NOT_FILE"

    
    

    #e) Remove the (name,inode) binding for this file in dir

    #using indx_list to keep track of the index position (helper, might delete it later)
    indx_file_lis = []
    #using name_entries_lis to keep track of the last entry for replacement
    name_entries_lis = []


    #using block_number_lis to keep track of all the blocks
    block_number_lis = []




    #directory_block_numbers


    inobj = InodeNumber(file_inode.RawBlocks, dir)
    inobj.InodeNumberToInode()
    block_index = 0
    while block_index <= (inobj.inode.size // BLOCK_SIZE):
      #block is the raw block
      #block.hex() raw block in hex format
      block = file_inode.RawBlocks.Get(inobj.inode.block_numbers[block_index])
      #block number is the number of the directory where the file is located
      block_number = inobj.inode.block_numbers[block_index]
      #print("BLOCK NUMBERS ", block_number)
      block_number_lis.append(block_number)
      #print("block_index ", block_index)
      #print("inobj.inode.block_numbers[block_index]", inobj.inode.block_numbers[block_index])
      #print("block before the removal ", block.hex())
      if block_index == (inobj.inode.size // BLOCK_SIZE):
        
        end_position = inobj.inode.size % BLOCK_SIZE
        
      else:
        end_position = BLOCK_SIZE
      current_position = 0
      while current_position < end_position:
        entryname = block[current_position:current_position+MAX_FILENAME]
        entryinode = block[current_position+MAX_FILENAME:current_position+FILE_NAME_DIRENTRY_SIZE]
        entryinodenumber = int.from_bytes(entryinode, byteorder='big')
        inobj2 = InodeNumber(file_inode.RawBlocks, entryinodenumber)
        inobj2.InodeNumberToInode()
        if entryinodenumber == i_num:
          #print("i_num ", i_num)
          indx_file = current_position
          
          file_block_number = block_number
          #print("indx_file ", indx_file)

        if inobj2.inode.type == INODE_TYPE_DIR:
          #print ("[" + str(inobj2.inode.refcnt) + "]:" + entryname.decode() + "/")

          #entryname.decode is the name of the dir or a file
          #entryinodenumber is the name of the inodenumber for that file or dir
          name_entries_lis.append(entryname.decode())
          #print("entryinodenumber ", entryinodenumber)
        else:
          #print ("[" + str(inobj2.inode.refcnt) + "]:" + entryname.decode())
          name_entries_lis.append(entryname.decode())
          
          #print("entryinodenumber ", entryinodenumber)

        indx_file_lis.append(current_position)
        #print("current_position ", current_position)
        current_position += FILE_NAME_DIRENTRY_SIZE
        
      
      block_index += 1
    
    
     
    #lis[-1] - is the name of the last entry in the table
    last_obj = self.Lookup(name_entries_lis[-1], dir)
    

    last_inode = InodeNumber(self.RawBlocks, last_obj)
    last_inode.InodeNumberToInode()

    #print("last entry in the table lis[-1]", name_entries_lis[-1])
    #_________________________________

    
    
    #______________________________________
    # We store inode block_numbers as a list
    


    inode_block_numbers = file_inode.inode.block_numbers


    #print("number ", inode_block_numbers)
    #print("block_number_lis ", block_number_lis)
    #print("file_block_number " , file_block_number)

    


    for i in range(len(block_number_lis)):
      if block_number_lis[i] == file_block_number:
        first = i
    last = len(block_number_lis) -1
      

  
    block_to_replace = file_inode.RawBlocks.Get(inobj.inode.block_numbers[first])
    last_block_to_replace_with = file_inode.RawBlocks.Get(inobj.inode.block_numbers[last])


    #block[indx_file:indx_file+MAX_FILENAME]=block[indx_file_lis[-1]:indx_file_lis[-1]+MAX_FILENAME]
    #block[indx_file+MAX_FILENAME:indx_file+FILE_NAME_DIRENTRY_SIZE]=block[indx_file_lis[-1]+MAX_FILENAME:indx_file_lis[-1]+FILE_NAME_DIRENTRY_SIZE]
    
    #block[indx_file_lis[-1]:indx_file_lis[-1]+MAX_FILENAME] = [0 for i in range(indx_file_lis[-1] , indx_file_lis[-1]+MAX_FILENAME)]

    #block[indx_file_lis[-1]+MAX_FILENAME:indx_file_lis[-1]+FILE_NAME_DIRENTRY_SIZE] = [0 for i in range(indx_file_lis[-1]+MAX_FILENAME , indx_file_lis[-1]+FILE_NAME_DIRENTRY_SIZE)]

    block_to_replace[indx_file:indx_file+MAX_FILENAME]=last_block_to_replace_with[indx_file_lis[-1]:indx_file_lis[-1]+MAX_FILENAME]
    block_to_replace[indx_file+MAX_FILENAME:indx_file+FILE_NAME_DIRENTRY_SIZE]=last_block_to_replace_with[indx_file_lis[-1]+MAX_FILENAME:indx_file_lis[-1]+FILE_NAME_DIRENTRY_SIZE]
    
    last_block_to_replace_with[indx_file_lis[-1]:indx_file_lis[-1]+MAX_FILENAME] = [0 for i in range(indx_file_lis[-1] , indx_file_lis[-1]+MAX_FILENAME)]

    last_block_to_replace_with[indx_file_lis[-1]+MAX_FILENAME:indx_file_lis[-1]+FILE_NAME_DIRENTRY_SIZE] = [0 for i in range(indx_file_lis[-1]+MAX_FILENAME , indx_file_lis[-1]+FILE_NAME_DIRENTRY_SIZE)]


    #d) Decrement the refcnt of the file that is being unlinked

    file_inode.inode.refcnt -=1 
    file_inode.inode.type = INODE_TYPE_INVALID
    file_inode.inode.size = 0
    #print("file_inode.inode.refcnt ", file_inode.inode.refcnt)
    #print("file_inode.inode.type ", file_inode.inode.type)
    #print("file_inode.inode.size ", file_inode.inode.size)

    #__________________________________
    
    #f) Decrement the refcnt for the directory dir
    dir_inode.inode.refcnt -=1 
    dir_inode.inode.size -= FILE_NAME_DIRENTRY_SIZE
    

    #freeing the block of the file inode 
    for i in range(len(inode_block_numbers)):
      self.RawBlocks.Put(inode_block_numbers[i], int(0).to_bytes(len(inode_block_numbers), 'big'))
    
    for j in range(len(file_inode.inode.block_numbers)):
      file_inode.inode.block_numbers[j] = 0
    
    #removing the last entry in the directory from the table
    block[indx_file_lis[-1]:indx_file_lis[-1]+MAX_FILENAME] = [0 for i in range(indx_file_lis[-1] , indx_file_lis[-1]+MAX_FILENAME)]

    block[indx_file_lis[-1]+MAX_FILENAME:indx_file_lis[-1]+FILE_NAME_DIRENTRY_SIZE] = [0 for i in range(indx_file_lis[-1]+MAX_FILENAME , indx_file_lis[-1]+FILE_NAME_DIRENTRY_SIZE)]
    
    file_inode.StoreInode()
    dir_inode.StoreInode()
    

    #print("block after ", block.hex())

    #print("indx_lis ", indx_file_lis, len(indx_file_lis))
    #print("lis ", name_entries_lis, len(name_entries_lis))
    

    #print("last_obj",last_obj)


    #print(i_num)
    #print("block after the removal ", self.RawBlocks.hex())
    
    return  " "

    
   


    """ 

      Here, "dir" is the *inode number* of the current directory and "name" is the *file name* to be unlinked

      Similar to the book's description, this function should provide the following functionality:

      * NOTE: please ensure you return the error message EXACTLY AS SHOWN BELOW for smooth grading. Your aasignment *will* have points deducted for not following the naming convention*

     

      a) Ensure "dir" corresponds to a valid directory; if not, return an error ERROR_UNLINK_INVALID_DIR
      b) Ensure "name" exists in the directory; if not, return an error ERROR_UNLINK_DOESNOT_EXIST
      c) Ensure "name" refers to a file of type INODE_TYPE_FILE; if not, return error ERROR_UNLINK_NOT_FILE
      d) Decrement the refcnt of the file that is being unlinked
      e) Remove the (name,inode) binding for this file in dir
      f) Decrement the refcnt for the directory dir
      g) If the file's refcnt drops to zero:
        g.1) Free up the file's blocks (setting the proper byte(s) to 0 in the free block bitmap)
        g.2) Free up the inode (setting the inode to be INODE_TYPE_INVALID)

    """

    """
    print("indx_lis[-1 ]", indx_lis[-1])
    last_entry = block[indx_lis[-1]: indx_lis[-1]+ FILE_NAME_DIRENTRY_SIZE]
    print("last_entry ", last_entry)
    indx_file_entry = block[indx_file: indx_file+ FILE_NAME_DIRENTRY_SIZE]
    print("index_file_entry ", indx_file_entry)

    indx_file_entry = last_entry 
    file_inode.StoreInode()
    dir_inode.StoreInode()

    print("MAX_FILENAME + FILE_NAME_DIRENTRY_SIZE ", MAX_FILENAME , FILE_NAME_DIRENTRY_SIZE)

    #_________________________
     #FREEBITMAP_BLOCK_OFFSET = 2  
    #block_array_for_dir = dir_inode.RawBlocks.Get(dir_inode.inode.block_numbers[0])
    #print("THIS BLOCK IS", block)

    #bitmap_block = FREEBITMAP_BLOCK_OFFSET + (block_number // BLOCK_SIZE)
    #block = self.RawBlocks.Get(bitmap_block)

    #print("block ", block_array_for_dir)

    #print("file_inode.RawBlocks", file_inode.RawBlocks)



    """

    """
    #From CREATE
    newfile_inode = InodeNumber(self.RawBlocks, inode_position)
      newfile_inode.InodeNumberToInode()
      newfile_inode.inode.type = INODE_TYPE_FILE
      newfile_inode.inode.size = 0
      newfile_inode.inode.refcnt = 1
      # New files are not allocated any blocks; these are allocated on a Write()
      newfile_inode.StoreInode()

      # Add to parent's (filename,inode) table
      self.InsertFilenameInodeNumber(dir_inode, name, inode_position) 
    
      # Update directory inode
      # refcnt incremented by one
      dir_inode.inode.refcnt += 1
      dir_inode.StoreInode()

    """





    

