#! /usr/bin/env python3

def parseArgs(argv):
	"""Uses the argparse module to gather information from the user"""
	import argparse

	parser = argparse.ArgumentParser(description="A short script for splitting one gcode file into parts along layer/height boundaries.  This is used to allow material-changes midprint.  See bottom of this help message for formatting details", epilog="""The input file can have special formatting to allow it to more easily be split.  The largest of these is automatic prefix/postfix location.  This follows the following rules.  Each rule should be located in its own line.  '; START_PREFIX' - indicates the start of the prefix, '; END_PREFIX' - indicates the end of the prefix, '; START_POSTFIX' - indicates the start of the postfix, '; END_POSTFIX' - indicates the end of the postfix

If the prefix and/or postfix are specified this way and no override is specified on the command line, they will be automatically located and put at the start and end of each part respectively.  If the prefix and postfix are not specified in this way, you will need to manually remove it from the input, or the file may be split incorrectly if your prefix or postfix includes z movement.""")
	parser.add_argument("--debug", "-d", help="Enable debug output", action="store_true")
	parser.add_argument("--output-file-name", "-o", help="The format for output files.  Use {input_file} to include the orginal filename, minus extension and prefix path (basename).  Use {input_file_full} to include the full name of the input file without the path (basename only).  Use {part_number} to include the number of the part. Default: {input_file}-part{part_number}.gcode", default="{input_file}-part{part_number}.gcode")
	parser.add_argument("--prefix", help="Specifies prefix commands to be included at the start of each part.", default=None)
	parser.add_argument("--postfix", help="Specifies the postfix commands to be included at the end of each part", default=None)
	parser.add_argument("file", help="The base GCODE file you wish to split into multiple parts")
	parser.add_argument("split", help="The location at which to split the model.  Supported units: mm for milimeters, l for layers.  The split is performed so that the first layer in the new part is the first layer after the threshold.", nargs='+')
	parser.add_argument("--version", "-v", action='version', version='%(prog)s 1.0')

	return parser.parse_args(argv)

"""Global variable that covers whether or not debug messages should be printed.  Usually set using the -d or --debug inputs, but exposed here in case it has utility in use as a module"""
debugOn=False

def debug(msg):
	"""Prints debug messages, if they are enabled.  Exposed so anyone using htis as a module has the option of printing through the same methodology.
This will probably be changed to use python's logging module if this tool recieves significant additional work."""
	if debugOn:
		print(msg)

def parse_prefix(infile):
	"""Extracts the annotated prefix from the input file, if one is present.  Returns None otherwise."""
	import re
	
	fileStr = infile.read() #ineffeciently read the file into memory.  TODO: more efficent
	
	infile.seek(0,0) #reset for other users of the file.
	
	# This grabs all text (including the annotations) between annotations in the file.
	# This way if only one is present, we do not mark the whole file as prefix.
	pattern = re.compile("^; START_PREFIX$\n(.*$\n)+; END_PREFIX$\n", re.M | re.I)
	
	matches = pattern.search(fileStr) # do the search...
	
	# And return an appropriate value.  None indicates no prefix was found.
	if matches:
		return matches.group(0)
	else:
		return None

def parse_postfix(infile):
	"""Extracts the annotated postfix from the input file if any.  Returns None if none is located."""
	import re
	
	fileStr = infile.read() # Read whole file into memory. TODO: be more efficient.
	
	infile.seek(0,0) #rest for others
	
	#Grab all postfix text between annotations.  No not find anything if either tag is missing.
	pattern = re.compile("^; START_POSTFIX$\n(.*$\n)+; END_POSTFIX$\n", re.M | re.I)
	
	matches = pattern.search(fileStr) #search...
	
	# Return as appropriate
	if matches:
		return matches.group(0)
	else:
		return None

def make_outfile(outfile_name, part, infile_full_name):
	"""Set up a file object to write output to.  This ttransforms the output file name as specified by the --output-file-name argument into a string that can be used to open it.
Takes: outfile_name, the unsubstituted string from arguments
part: the number of the part of the file, to be able to substitute
infile_full_name: the name of the inout file, with extension"""
	from os.path import basename
	# attempts to take as much of the imput file name as possible without including the final period or anything after.
	infile_name_match = re.search("^(.*)\.[\w\d]+", infile_full_name, re.I) 
	
	#set the infile_name, which is input without extenstion
	if infile_name_match:
		debug("Input file name: Able to drop an extension")
		infile_name = infile_name_match.group(1)
	else:
		debug("Input file name: Unable to drop file extension")
		infile_name = infile_full_name
	
	#Chop paths off the file names	
	infile_name = basename(infile_name)
	infile_full_name = basename(infile_full_name)
	
	debug("Infile name, without extension: %s" % infile_name)
	
	#Do the formatting to have the substitutions done
	outfile_subed = outfile_name.format(input_file=infile_name,
		input_file_full=infile_full_name,
		part_number=part)
	debug("Outfile name: %s" % outfile_subed)
		
	return outfile_subed

def do_file_change(outfile, outfile_name, part, infile_full_name, prefix, postfix):
	"""Closes the old output file object and returns the new one if any.
Takes:
outfile: the file object of the current output file, if any.
outfile_name: The unmodified output file name as passed by the user
part: the number of previously written output files (for the {part} expression).
infile_full_name: the entire name, including extension, of the input file
prefix: the gcode prefix to put at the start of each file
postfix: the gcode postfix to put at the end of each file"""
	debug("Doing file changeover")
	
	#If we have a postfix and an open file, write the postfix to it
	if outfile and postfix:
		outfile.write(postfix)
	
	# get the name for the new file
	outfile_name = make_outfile(outfile_name, part, infile_full_name)
	outfile = open(outfile_name, 'w') #open it...
	
	#and write a prefix, if we have one
	if prefix:
		outfile.write(prefix)
	
	return outfile #return the file object

def split_file(infile, prefix, postfix, splits, outfile_name, infile_name):
	"""Main body of functionality.  Spilts gcode file based on number of layers or height"""
	# first going to separate splits by unit
	mm = []
	layer = []
	for item in splits: #turn each input item into just a pure number without units
		if 'mm' in item.lower():
			mm.append(float(item[:-2])) #item minus mm
		if 'l' in item.lower():
			layer.append(int(item[:-1])) #item minus l
	
	# Sort into order asending so we can just check the first one.
	mm.sort()
	layer.sort()
	
	in_body=not bool(prefix) #if non-empty and not None look for the ned of the prefix before writing.
	debug("Body stating value is %d" % in_body)
	part=0
	layers=0
	
	#Open up our starting file
	outfile = do_file_change(None, outfile_name, part, infile_name, prefix, postfix)
	
	for line in infile:
		prefixre=re.search("^; END_PREFIX", line, re.I) #look for the end of the prefix
		postfixre=re.search("^; START_POSTFIX", line, re.I) #look for the start of the postfix
		
		if prefixre:
			in_body=True
			debug("Now reading body")
		if postfixre:
			in_body=False
			debug("Now exiting body")
			
		if in_body:
			# chek if the line has a z movement
			match=re.search("^G[^Z;]+Z([\d\.]+).*$", line)
			if match:
				layers+=1 #increment layer count
				
				#check if the z height is greater than our threshold
				if len(mm)>0 and float(match.group(1))>mm[0]:
					part+=1
					debug("Matching line: %s" % match.group(0))
					debug("splitting at mm %d, actual height %f (%s)" % (mm[0], float(match.group(1)), match.group(1)))
					outfile = do_file_change(outfile, outfile_name, part, infile_name, prefix, postfix)
					mm = mm[1:] #cut the first entry,we've used it up
					
				#or if we've passed the layer count
				if len(layer)>0 and layers > layer[0]:
					part+=1
					debug("Splitting at layer %d" % layers)
					outfile = do_file_change(outfile, outfile_name, part, infile_name, prefix, postfix)
					#cut the first layer entry because we're done with it
					layer=layer[1:]
				
			#whatever the line was, its body and we need to write it out
			outfile.write(line)
		
if __name__=='__main__':
	import sys, re
	args=parseArgs(sys.argv[1:])
	
	#should we turn on debugging output?
	if args.debug:
		debugOn=True
		debug(args)
	
	#try to open the input file
	try:
		infile = open(args.file, 'r')
	except IOError:
		#oops
		print("Couldn't open the input file! (%s)" % (args.file))
		sys.exit(1)
	
	#if we got a command line prefix, we don't care about searching.
	#otherwise, try
	if not args.prefix:
		debug("Parsing prefix from file")			
		prefix = parse_prefix(infile)
	else:
		debug("Prefix specified or default")
		prefix = args.prefix
	
	if args.debug:
		print("Prefix: %s" % prefix)
	
	# If we got a command line postfix, just use that
	if not args.postfix:
		postfix = parse_postfix(infile)
	else:
		postfix = args.postfix
		
	if args.debug:
		print("Postfix: %s" % postfix)
		
	#do the big work.
	split_file(infile, prefix, postfix, args.split, args.output_file_name, args.file)
