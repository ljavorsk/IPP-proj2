import os.path as path
import getopt
import sys
import xml.etree.ElementTree as xmlElementTree

WrongArgsErr = 10
InputFileErr = 11
WrongXMLFromatErr = 31
UnexpectedXMLStructureErr = 32

class XMLParse(object):
    def __init__(self, ippCode20):
        """
        Creating the list of instructions in IPPCode20.
        Transforming the XML source file content to xmlElementTree.

        """
        self.listOfinstructions = [
            "CREATEFRAME", "PUSHFRAME", "POPFRAME", "RETURN", "BREAK",
            
            "DEFVAR", "CALL", "PUSHS", "POPS", "WRITE", "LABEL", "JUMP", "EXIT", "DPRINT",

            "MOVE", "INT2CHAR", "READ", "STRLEN", "TYPE", "NOT",

            "ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "STRI2INT", "CONCAT",                     
            "GETCHAR", "SETCHAR", "JUMPIFEQ", "JUMPIFNEQ"]
        try:
            elementTree = xmlElementTree.fromstring(ippCode20)
        except xmlElementTree.ParseError:
            err_msg("The source XML file is not well-formed.", WrongXMLFromatErr)

        self.elementTree = elementTree
        self.program_tag_check()
        self.program_tree = self.make_program_tree()
    
    def program_tag_check(self):
        """
        Checks for the XML tag 'program' which is mandatory.
        Next it check for valid attribute 'language'.

        """
        if self.elementTree.tag == "program":
            try:
                self.elementTree.attrib["language"]
            except KeyError:
                err_msg("The 'language' atribute is missing in a source file", UnexpectedXMLStructureErr)

            if self.elementTree.attrib["language"] != "IPPcode20":
                err_msg("'language' attribute has wrong value (IPPCode20 is expected)", UnexpectedXMLStructureErr)
        else:       # Missing or wrong program tag
            err_msg("Source file have missing or wrong 'program' tag", UnexpectedXMLStructureErr)

    def make_program_tree(self):
        """
        Builds the program instructions tree from source file

        """

        program_tree = []
        for inst in self.elementTree:
            
            
            self.check_instruction_tag(inst)
            numOfInst = int(inst.attrib["order"])

            program_tree.insert(numOfInst - 1, inst)

        i = 1
        for orderedInst in program_tree:
            if orderedInst.attrib["order"] != i:
                err_msg("Some of the instructions had the same order number", UnexpectedXMLStructureErr)

        return program_tree

    
    def check_instruction_tag(self, inst):
        """
        Checks if everything is valid in every instruction inside of the source file
        Exit with error if the instruction is not defined by IPPCode20

        """
        
        if inst.tag != "instruction":
            err_msg("Wrong instruction tag in instruction {}".format(inst.attrib), UnexpectedXMLStructureErr)

        # Is there 'order' attribute?
        try:
            inst.attrib["order"]
        except KeyError:
            err_msg("Missing 'order' attribute in instruction {}".format(inst.attrib), UnexpectedXMLStructureErr)

        # Is there 'opcode' attribute?
        try:
            inst.attrib["opcode"]
        except KeyError:
            err_msg("Missing 'opcode' attribute in instruction {}".format(inst.attrib), UnexpectedXMLStructureErr)

        try:
            order = int(inst.attrib["order"])
        except ValueError:
            err_msg("The 'order' number is not a number in instruction {}".format(inst.attrib), UnexpectedXMLStructureErr)

        numOfInst = int(inst.attrib["order"])

        # Order attribute checks
        if numOfInst < 1:
            err_msg("Order attribute in instruction {} is lower than 1".format(inst.attrib), UnexpectedXMLStructureErr)
        if numOfInst > len(self.elementTree):
            err_msg("Order attribute in instruction {} is bigger than the number of instructions".format(inst.attrib), UnexpectedXMLStructureErr)

        if inst.attrib["opcode"].upper() not in self.listOfinstructions:
            err_msg("Operation code in {} is not valid in IPPCode20".format(inst.attrib), UnexpectedXMLStructureErr)

    def get_program_tree(self):
        return self.program_tree


def parse_and_check_args():
    """
    Parse the arguments from command line, and check if they are valid.
    If not, this function will end with coresponding error code + message.
    """

    sourceFile = inputFile = None
    try:
        options, args = getopt.getopt(sys.argv[1:],"",["help", "source=", "input="])
    except getopt.GetoptError:
        err_msg("Wrong arguments", WrongArgsErr)
    for option, filename in options:
        if (option == "--help" and len(options) < 2):
            print("Usage: python3.8 interpret.py {[--source=<file> [--input=<file>] | --input=<file> [--source=<file]]} [--help]")
            print("Description: Interpreter for the IPPCode20 represented in XML format.")
            print("             At least one of the arguments (source | input) have to be provided by user.")
            print("Options: ")
            print("     --help             Prints short help about script")
            print("     --source=<file>    Source file, that contains IPPCode20 instructions in XML format (if not passed, reading stdin)")
            print("     --input=<file>     Input file, that will be interpreted (if not passed, reading stdin)")
            sys.exit(0)
        elif (option == "--source"):
            sourceFile = filename
        elif (option == "--input"):
            inputFile = filename
        else:
            err_msg("Uknown arguments", WrongArgsErr)

    if (sourceFile is None and inputFile is None):
        err_msg("Source or input file have to be passed", WrongArgsErr)
    
    if (sourceFile is not None and path.isfile(sourceFile)):
        with open(sourceFile, 'r', encoding='utf-8') as srcFileDes:
                sourceFile = srcFileDes.read()
        if (inputFile is not None and path.isfile(inputFile)):      # Nothing from stdin
            with open(inputFile, 'r', encoding='utf-8') as inFileDes:
                inputFile = inFileDes.read()
        else:   # Input from stdin
            if (inputFile is None):
                inputFile = sys.stdin.read()
            else:
                err_msg("Wrong input file", WrongArgsErr)
    elif (inputFile is not None and path.isfile(inputFile)):    # Source from stdin
        with open(inputFile, 'r', encoding='utf-8') as inFileDes:
            inputFile = inFileDes.read()
        if (sourceFile is None):
            sourceFile = sys.stdin.read()
        else:
            err_msg("Wrong source file", WrongArgsErr)
    else:
        err_msg("Wrong file/files given",WrongArgsErr)
    return sourceFile, inputFile

            
def err_msg(message, errCode):
	""" 
	Print the error message, and end with error code.
	
	Parameters: 
	errCode (int): Error code
	message (str): Message, that will be printed to stderr
	"""	
	
	print("Error: " + message, file=sys.stderr)
	sys.exit(errCode)

if __name__ == '__main__':
    (sourceFile, inputFile) = parse_and_check_args()
    
    program_tree = XMLParse(sourceFile).get_program_tree()
    sys.exit(0)