HW2

- a brief description of your design and implementation
- a description of how you tested your design

First all the commands mkdir, create, append, and rm were added to the interpreter.

mkdir dirname
Uses Lookup function to check if the directory already exist if not it creates a directory with the help of Create function.

create filename
Uses Lookup function to check if the file already exist if not it creates a file in the existent directory.

append filename string
Uses Lookup function to check if the file already exist. This commands allows to append only to a file by checking the Inode type to make sure it’s a file. It then writes to a file by using Write with the index depending on the content of the file. If the file has any content it would start from the end of that content, otherwise it will write from index 0.

rm filename
Uses Unlink method by passing current working directory and a file name to the method. It also returns any errors detected by Unlink.

Unlink method
First the information passed is checked to detect any errors:

- Ensure it corresponds to the working directory
- Ensure the name of the file exist in the working directory
- Ensure the type of the object we are trying to remove is File

To remove the file the information from the RawBlocks is being obtained by looping through each block in the Inode of the current directory. Information on the block and its contact is being collected with arrays that keep track of an index of the File that should be removed and its block number, and later the block’s index number is recorded as well. Additionally, the same information is collected on the last entry in the block whether it is a File or a Directory. Then the last entry replaces the file that is being removed by directly accessing the RawBlocks. File’s Inode’s reference count is being reduced, the Inode Type set to invalid and the size is reduced to 0 so Inode could be reused in the future. Additionally, the information on the current working directory is being adjusted appropriately. The blocks that were used by the File’s Inode are set to 0, and the last entry in the RawBlocks is set to 0. File Inode and Directory Inode objects are then being stored.

To check my implementation I first made sure that all error codes working appropriately, then I checked that the file could be replaced by an entry from the same block. Then I made sure that if last entry located in the different block it still can locate the block of the file I’m trying to remove and replace it. Using command showinode I checked that Inode’s size, reference count set to zero and that Inode’s type set to unused. I checked that the File’s Inode is not being assigned any blocks. With command showblock I checked each block that Inode previously used to make sure there is no information stored. I used cat command to access the file that was removed to check if it still accessible. I used command showblock to check the Raw Blow of the directory where the file was located to make sure that the last entry replaced the entry of the file. I used ls command to check if it reflects the content of the Raw Blocks. I used create command to add maximum amount of files to the system to check if I would get any errors overloading it.

When command “create file” that utilizes Create method is implemented it uses method Get approximately 15 times and method Put 4 times. When command “rm file” that utilizes the Unlink method is implemented it uses method Get approximately 20 times and method Put 4 times. For example Create method uses InsertFileInodeNumber() function 4 times in a row and each time this function is called a Get method used two times and Put method is used 3 times. In addition Create method uses StoreInode() function and each time the Inode is stored the Put method is used. If both functions would be used one time in the end of the Create method instead of several time the speed of the program should increase.
