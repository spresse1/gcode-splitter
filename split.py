#! /usr/bin/env python3

def parseArgs(argv):
	import argparse

	parser = argparse.ArgumentParser(description="A short script for splitting one gcode file into parts along layer/height boundaries.  This is used to allow material-changes midprint.  See bottom of this help message for formatting details", epilog="""The input file can have special formatting to allow it to more easily be split.  The largest of these is automatic prefix/postfix location.  This follows the following rules.  Each rule should be located in its own line.  '; START_PREFIX' - indicates the start of the prefix, '; END_PREFIX' - indicates the end of the prefix, '; START_POSTFIX' - indicates the start of the postfix, '; END_POSTFIX' - indicates the end of the postfix

If the prefix and/or postfix are specified this way and no override is specified on the command line, they will be automatically located and put at the start and end of each part respectively.  If the prefix and postfix are not specified in this way, you will need to manually remove it from the input, or the file may be split incorrectly if your prefix or postfix includes z movement.""")
	parser.add_argument("--debug", "-d", help="Enable debug output", action="store_true")
	parser.add_argument("--output-file-name", "-o", help="The format for output files.  Use {input_file} to include the orginal filename, minus extension.  Use {input_file_full} to include the full name of the input file.  Use {part_number} to include the number of the part. Default: {input_file}-part{part_number}.gcode", default="{input_file}-part{part_number}.gcode")
	parser.add_argument("--prefix", help="Specifies prefix commands to be included at the start of each part.", default=None)
	parser.add_argument("--postfix", help="Specifies the postfix commands to be included at the end of each part", default=None)
	parser.add_argument("file", help="The base GCODE file you wish to split into multiple parts")
	parser.add_argument("split", help="The location at which to split the model.  Supported units: mm for milimeters, l for layers.  The split is performed so that the first layer in the new part is the first layer after the threshold.", nargs='+')
	parser.add_argument("--version", "-v", action='version', version='%(prog)s 1.0')

	return parser.parse_args(argv)

debugOn=False
def debug(msg):
	if debugOn:
		print(msg)

def parse_prefix(infile):
	import mmap #we'll map the file into memory so we can regex search
	import re
	
	fileStr = infile.read()
	
	infile.seek(0,0)
	
	pattern = re.compile("^; START_PREFIX$\n(.*$\n)+; END_PREFIX$\n", re.M | re.I)
	
	matches = pattern.search(fileStr)
	
	if matches:
		return matches.group(0)
	else:
		return None

def parse_postfix(infile):
	import mmap #we'll map the file into memory so we can regex search
	import re
	
	fileStr = infile.read()
	
	infile.seek(0,0)
	
	pattern = re.compile("^; START_POSTFIX$\n(.*$\n)+; END_POSTFIX$\n", re.M | re.I)
	
	matches = pattern.search(fileStr)
	
	if matches:
		return matches.group(0)
	else:
		return None

def make_outfile(outfile_name, part, infile_full_name):
	infile_name_match = re.search("^(.*)\.[\w\d]+", infile_full_name, re.I)
	if infile_name_match:
		debug("Input file name: Able to drop an extension")
		infile_name = infile_name_match.group(1)
	else:
		debug("Input file name: Unable to drop file extension")
		infile_name = infile_full_name
	debug("Infile name, without extension: %s" % infile_name)
	outfile_subed = outfile_name.format(input_file=infile_name,
		input_file_full=infile_full_name,
		part_number=part)
	debug("Outfile name: %s" % outfile_subed)
		
	return open(outfile_subed, 'w')

def do_file_change(outfile, outfile_name, part, infile_full_name, prefix, postfix):
	debug("Doing file changeover")
	if outfile and postfix:
		outfile.write(postfix)
	
	outfile = make_outfile(outfile_name, part, infile_full_name)
	if prefix:
		outfile.write(prefix)
	
	return outfile

def split_file(infile, prefix, postfix, splits, outfile_name, infile_name):
	# first going to separate splits by unit
	mm = []
	layer = []
	for item in splits:
		if 'mm' in item.lower():
			mm.append(float(item[:-2]))
		if 'l' in item.lower():
			layer.append(int(item[:-1]))
	
	mm.sort()
	layer.sort()
	
	in_body=not bool(prefix) #if non-empty and not None look for the ned of the prefix before writing.
	debug("Body stating value is %d" % in_body)
	part=0
	layers=0
	outfile = do_file_change(None, outfile_name, part, infile_name, prefix, postfix)
	for line in infile:
		prepostfix=re.search("^; END_PREFIX", line, re.I)
		
		if prepostfix:
			#if prepostfix.group(1) is '; END_PREFIX':
				in_body=True
				debug("Now reading body")
			#if prepostfix.group(1) is '; START_POSTFIX':
			#	in_body=False
			#	debug("exiting body")
			
		if in_body:
			match=re.search("^G[^Z;]+Z([\d\.]+).*$", line)
			if match:
				#debug("Matching line: %s" % match.group(0))
				layers+=1 #increment layer count
				if len(mm)>0 and float(match.group(1))>mm[0]:
					part+=1
					debug("Matching line: %s" % match.group(0))
					debug("splitting at mm %d, actual height %f (%s)" % (mm[0], float(match.group(1)), match.group(1)))
					outfile = do_file_change(outfile, outfile_name, part, infile_name, prefix, postfix)
					mm = mm[1:]
				if len(layer)>0 and layers > layer[0]:
					part+=1
					debug("Splitting at layer %d" % layers)
					outfile = do_file_change(outfile, outfile_name, part, infile_name, prefix, postfix)
					layer=layer[1:]
				
			outfile.write(line)
		
if __name__=='__main__':
	import sys, re
	args=parseArgs(sys.argv[1:])
	
	if args.debug:
		debugOn=True
		debug(args)
	
	try:
		infile = open(args.file, 'r')	
		
	except IOError:
		print("Couldn't open the input file! (%s)" % (args.file))
		sys.exit(1)
		
	if not args.prefix:
		debug("Parsing prefix from file")			
		prefix = parse_prefix(infile)
	else:
		debug("Prefix specified or default")
		prefix = args.prefix
	
	if args.debug:
		print("Prefix: %s" % prefix)
	
	if not args.postfix:
		postfix = parse_postfix(infile)
	else:
		postfix = args.postfix
		
	if args.debug:
		print("Postfix: %s" % postfix)
		
	split_file(infile, prefix, postfix, args.split, args.output_file_name, args.file)
