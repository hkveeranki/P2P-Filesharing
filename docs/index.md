
# P2P-Filesharing  
  
Minimal Terminal based P2P Filesharing server written in python . :)  
  
## Aim:  
  
To create an Application Level File Sharing Protocol with support for download and  
upload for files and indexed searching.  

## Specifications :  
  This system incorporates the following commands :
   
 - ### IndexGet flag (args) 
	  + can request the display of the shared files on the connected system.  
	  + the flag variable can be shortlist, longlist or regex .    
	    - shortlist :  
	      flag would mean that the client only wants to know the names of files between a specific set of timestamps. The sample query  
	      is as below.  
		   + $> `IndexGet shortlist <start time stamp> <end time stamp>`
		   + Output : should include ‘name’, ‘size’, ‘timestamp’ and ‘type’ of the files between the start and end time stamps.
	    - longlist : flag would mean that client wants to know the entire listing of the shared folder/directory including ‘name’, ‘size’, ‘timestamp’ and ‘type’ of the files.  
	       + $> `IndexGet longlist`   
		   + Output : similar to above, but with complete file listing.
	    - regex : regular expression matching  
	        + $> `IndexGet a*b`  
			+ Output : similar to shortlist.
  
 - ### FileHash flag (args) :  
    + this command indicates that the client wants to check if any of the files on the other end have been changed. The flag variable can take two values, verify and checkall  
      - verify : verify flag should check for the specific file name provided as command line argument and return its ‘checksum’ and ‘last modified’ timestamp.  
          + $> `FileHash verify <filename>`  
          + Output : checksum and last modified timestamp of the input file.  
      - checkall : checkall flag will perform what ‘verify’ does for all the files in the shared folder.  
          + $> `FileHash checkall`  
          + Output : filename, checksum and last modified timestamp of all the files in the shared directory.
  
 - ### FileDownload flag (args):  
    + as the name suggests, would be used to download files from the shared folder of connected user to our shared folder.  
    + the flag variable can take the value TCP or UDP depending on the users request.   
    + $> `FileDownload <flag> <filename>`  
    + Output : should contain the filename, filesize, last modified timestamp  
    and the MD5 hash of the requested file.

## Documentation
Docs can be found [here](/html/index.html)
