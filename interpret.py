import os.path as path
import getopt
import sys
import xml.etree.ElementTree as xmlElementTree
import re

WrongArgsErr = 10
InputFileErr = 11
WrongXMLFromatErr = 31
UnexpectedXMLStructureErr = 32

SemanticErr = 52
WrongOperandTypeErr = 53
VariableDoesntExistsErr = 54
FrameDoesntExistsErr = 55
MissingValueErr = 56
WrongOperandValue = 57
StringOperationErr = 58

jumpingInst = ["RETURN", "CALL", "JUMP", "JUMPIFEQ", "JUMPIFNEQ"]
instructionsWithoutArgs = ["CREATEFRAME", "PUSHFRAME", "POPFRAME", "RETURN", "BREAK"]
instructionsWithOneArg = ["DEFVAR", "CALL", "PUSHS", "POPS", "WRITE", "LABEL", "JUMP", "EXIT", "DPRINT"]
instructionsWithTwoArg = ["MOVE", "INT2CHAR", "READ", "STRLEN", "TYPE", "NOT"]
instructionsWithThreeArg = ["ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "STRI2INT", "CONCAT",
                            "GETCHAR", "SETCHAR", "JUMPIFEQ", "JUMPIFNEQ"]
argumentTypes = ["int", "bool", "string", "nil", "label", "type", "var"]

class Interpret(object):
    def __init__(self, sourceProgram, inputFile):
        self.instructPointer = 0
        self.program = sourceProgram
        self.input = inputFile
        self.GF = {}
        self.LF = None
        self.TF = None
        self.labels = {}
        self.labels = UniqueDict(self.labels)

    def get_all_labels(self):
        for inst in self.program:
            if inst.attrib["opcode"].upper() == "LABEL":
                for arg in inst:
                    try:
                        self.labels[arg.text] = inst.attrib["order"]
                    except KeyError:
                        err_msg("Label '{}' in instruction {} is being redefined".format(arg.text, inst.attrib), SemanticErr)

    def interpret_the_language(self):
        self.get_all_labels()
        self.instructPointer = 0

        while self.instructPointer < len(self.program):

            # Is it a jump?
            if self.program[self.instructPointer].attrib["opcode"] in jumpingInst:
                self.instructPointer = self.do_instruction(self.program[self.instructPointer])
            else:
                self.do_instruction(self.program[self.instructPointer])

            self.instructPointer += 1
        
    def do_instruction(self, inst):

        def var_arg(inst, whatArg, is_symb=False):
            
            for arg in inst:
                if (arg.tag == whatArg):
                    if arg.text is None:
                        child.text = ""
                    if arg.attrib["type"] != "var":
                        if is_symb:
                            return None
                        err_msg("{} is not valid var name in instruction {}".format(arg.text, inst.attrib),UnexpectedXMLStructureErr)
                    if not re.match('^[L,T,G]F@[a-zA-Z_\-\$&%*!?][0-9a-zA-Z_\-\$&%*!?]*$', arg.text):
                        if is_symb:
                            return None
                        err_msg("{} is not valid var name in instruction {}".format(arg.text, inst.attrib),UnexpectedXMLStructureErr)
                    return arg
            return None

        def symb_arg(inst, whatArg):
            
            var = var_arg(inst, whatArg, is_symb=True)
            if var is not None:
                
                return "var", var
            for arg in inst:
                if (arg.tag == whatArg):
                    return arg.attrib["type"], arg

            # didn't fit any format
            err_msg("The <symb> value is not valid in {} argument".format(arg), UnexpectedXMLStructureErr)
        
        def search_in_frame(frameType, frameName):
            if frameType == "GF":
                try:
                    self.GF[frameName]
                except KeyError:
                    err_msg("Global frame with name '{}' doesn't exists", FrameDoesntExistsErr)
                return self.GF

            elif frameType == "LF":
                if self.LF is None:
                    err_msg("Local frame is not created yet", FrameDoesntExistsErr)

                try:
                    self.LF[frameName]
                except KeyError:
                    err_msg("Local frame with name '{}' doesn't exists", FrameDoesntExistsErr)
                return self.LF

            elif frameType == "TF":
                if self.TF is None:
                    err_msg("Temporary frame is not created yet", FrameDoesntExistsErr)

                try:
                    self.TF[frameName]
                except KeyError:
                    err_msg("Temporary frame with name '{}' doesn't exists", FrameDoesntExistsErr)
                return self.TF

        def get_var(arg):
            frame, name = get_frame_and_name(arg)
            varsFrame = search_in_frame(frame, name)

            argType = varsFrame[name]['type']
            argValue = varsFrame[name]['value']

            return argType, argValue

        def get_type_value(arg, typeOfArg):

            if typeOfArg == "var":
                typeOfArg, argValue = get_var(arg)
            else:
                argValue = arg.text

            return typeOfArg, argValue

        def get_frame_and_name(arg):
            arg_split = arg.text.split('@', 1)
            frame = arg_split[0]
            name = arg_split[1]

            return (frame, name)

        def aritmetic_operations():
            arg1 = var_arg(inst, "arg1")

            frame, name = get_frame_and_name(arg1)

            varsFrame = search_in_frame(frame, name)

            arg2Type, arg2Body = symb_arg(inst, "arg2")
            arg2Type, arg2Value = get_type_value(arg2Body, arg2Type)

            arg3Type, arg3Body = symb_arg(inst, "arg3")
            arg3Type, arg3Value = get_type_value(arg3Body, arg3Type)

            if arg2Type is None or arg3Type is None:
                err_msg("Value in one or more instruction arguments are not defined, Instruction: {}".format(inst.attrib), MissingValueErr)

            if arg2Type != "int" or arg3Type != "int":
                err_msg("Arguments have to be type of 'int' in instruction {}".format(inst.attrib), WrongOperandTypeErr)
            
            arg2Value = int(arg2Value)
            arg3Value = int(arg3Value)

            return (arg2Value, arg3Value, varsFrame, name)

        
        def convert_unicode_values_in_string(string):
            for unicode_sequence in re.findall('\\\\[0-9]{3}', string):
                string = string.replace(unicode_sequence, chr(int(unicode_sequence[1:])))
            return string

        def defvar():
            arg1 = var_arg(inst, "arg1")

            frame, name = get_frame_and_name(arg1)

            if frame == "GF":
                if name in self.GF.keys():
                    err_msg("Global frame {} is being redefined".format(name), SemanticErr)
                else:
                    self.GF[name] = {'type': None, 'value': None}
            elif frame == "LF":
                if type(self.LF) == dict:
                    if name in self.LF.keys():
                        err_msg("Local frame {} is being redefined".format(name), SemanticErr)
                    else:
                        self.LF[name] = {'type': None, 'value': None}
                else:
                    err_msg("Local frame with name '{}' is not created".format(name), FrameDoesntExistsErr)
            
            elif frame == "TF":
                if type(self.TF) == dict:
                    if name in self.TF.keys():
                        err_msg("Temporary frame {} is being redefined".format(name), SemanticErr)
                    else:
                        self.TF[name] = {'type': None, 'value': None}
                else:
                    err_msg("Temporary frame with name '{}' is not created".format(name), FrameDoesntExistsErr)

            return ('\nDoing {}.'.format(inst.attrib))

        def move():
            arg1 = var_arg(inst, "arg1")

            frame, name = get_frame_and_name(arg1)

            varsFrame = search_in_frame(frame, name)

            arg2Type, arg2Value = symb_arg(inst, "arg2")

            if arg2Value is None:
                err_msg("Value of arg2 is empty in instruction {}".format(inst.attrib), UnexpectedXMLStructureErr)

            if arg2Type == "int":
                arg2Struct = {'type': 'int', 'value': int(arg2Value.text)}
            elif arg2Type == "var":
                arg2Type, arg2Struct = get_var(arg2Value)
                arg2Struct = {'type': arg2Type, 'value': arg2Value}
            else:
                arg2Struct = {'type': arg2Type, 'value': arg2Value.text}

            varsFrame[name] = arg2Struct
            return f'\nDoing {inst.attrib}.'

        def add():
            arg2Value, arg3Value, varsFrame, name = aritmetic_operations()

            resultOfAdition = {'type': 'int', 'value': arg2Value + arg3Value}

            varsFrame[name] = resultOfAdition

            return f'\nDoing {inst.attrib}.'

        def mul():
            arg2Value, arg3Value, varsFrame, name = aritmetic_operations()

            resultOfAdition = {'type': 'int', 'value': arg2Value * arg3Value}

            varsFrame[name] = resultOfAdition

            return f'\nDoing {inst.attrib}.'

        def sub():
            arg2Value, arg3Value, varsFrame, name = aritmetic_operations()

            resultOfAdition = {'type': 'int', 'value': arg2Value - arg3Value}

            varsFrame[name] = resultOfAdition

            return f'\nDoing {inst.attrib}.'

        def idiv():
            arg2Value, arg3Value, varsFrame, name = aritmetic_operations()

            if (arg3Value == 0):
                err_msg("Zero division in {}".format(inst.attrib), WrongOperandValue)

            resultOfAdition = {'type': 'int', 'value': arg2Value // arg3Value}

            varsFrame[name] = resultOfAdition

            return f'\nDoing {inst.attrib}.'

        def write():
            arg1Type, arg1 = symb_arg(inst, "arg1")

            if arg1Type == "var":
                arg1Type, arg1Value = get_var(arg1)
                if arg1Type is None:
                    err_msg("Variable is uninitialized in instruction {}".format(inst.attrib), VariableDoesntExistsErr)
            else:
                arg1Value = arg1.text

            if arg1Value == "nil" and arg1Type == "nil":
                arg1Value = ""

            if arg1Type == "string":
                print(arg1Value, end='')
            elif type(arg1Value) == str:
                print(convert_unicode_values_in_string(arg1Value), end='')
            else:
                print(arg1Value, end='')

            return f'\nDoing {inst.attrib}.'

        ########            MAIN               ##########
        instructions = {
            # "CREATEFRAME": create_frame,
            # "PUSHFRAME": push_frame,
            # "POPFRAME": pop_frame,
            # "RETURN": _return,
            # "BREAK": _break,
            # # 1 arg
            "DEFVAR": defvar,
            # "CALL": call,
            # "PUSHS": pushs,
            # "POPS": pops,
            "WRITE": write,
            # "LABEL": label,
            # "JUMP": jump,
            # "EXIT": _exit,
            # "DPRINT": dprint,
            # # 2 args
            "MOVE": move,
            # "INT2CHAR": int2char,
            # "READ": read,
            # "STRLEN": strlen,
            # "TYPE": _type,
            # "NOT": _not,
            # # 3 args
            "ADD": add,
            "SUB": sub,
            "MUL": mul,
            "IDIV": idiv,
            # "LT": lt,
            # "GT": gt,
            # "EQ": eq,
            # "AND": _and,
            # "OR": _or,
            # "STRI2INT": stri2int,
            # "CONCAT": concat,
            # "GETCHAR": getchar,
            # "SETCHAR": setchar,
            # "JUMPIFEQ": jumpifeq,
            # "JUMPIFNEQ": jumpifneq,
        }
        
        result = instructions.get(inst.attrib["opcode"].upper(),
                                        lambda: err_msg("Invalid instruction '{}'".format(inst.attrib["opcode"].upper()), UnexpectedXMLStructureErr))
        return result()

class UniqueDict(dict):
    def __setitem__(self, key, value):
        if key not in self:
            dict.__setitem__(self, key, value)
        else:
            raise KeyError("Key already exists")

class XMLParse(object):
    def __init__(self, sourceXml):
        """
        Creating the list of instructions in IPPCode20.
        Transforming the XML source file content to xmlElementTree.

        Parameters:
        sourceXml (string): Xml source file
        """

        self.listOfinstructions = [
            "CREATEFRAME", "PUSHFRAME", "POPFRAME", "RETURN", "BREAK",
            
            "DEFVAR", "CALL", "PUSHS", "POPS", "WRITE", "LABEL", "JUMP", "EXIT", "DPRINT",

            "MOVE", "INT2CHAR", "READ", "STRLEN", "TYPE", "NOT",

            "ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "STRI2INT", "CONCAT",                     
            "GETCHAR", "SETCHAR", "JUMPIFEQ", "JUMPIFNEQ"]
        try:
            elementTree = xmlElementTree.fromstring(sourceXml)
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

        program_tree = [None] * len(self.elementTree)
        unique_order_arr = {}
        unique_order_arr = UniqueDict(unique_order_arr)

        index = 0
        for inst in self.elementTree:
            
            self.check_instruction(inst)

            try:
                unique_order_arr[int(inst.attrib["order"]) - 1] = inst
            except KeyError:
                err_msg("Order numbers are not unique", UnexpectedXMLStructureErr)

            try:
                program_tree[index] = inst
            except:
                err_msg("Some of the instructions had the same order number", UnexpectedXMLStructureErr)
            index += 1
        
        for element in unique_order_arr:
            print(element)

        return program_tree

    
    def check_instruction(self, inst):
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

        # Check arguments
        if (inst.attrib["opcode"].upper() in instructionsWithoutArgs and len(inst) != 0):
            err_msg("Instruction {} shouldn't have any arguments".format(inst.attrib["opcode"]), UnexpectedXMLStructureErr)
        else:
            # Check for number of arguments
            if (inst.attrib["opcode"].upper() in instructionsWithOneArg and len(inst) != 1):
                err_msg("Instruction {} should have exactly one argument".format(inst.attrib["opcode"]), UnexpectedXMLStructureErr)
            if (inst.attrib["opcode"].upper() in instructionsWithTwoArg and len(inst) != 2):
                err_msg("Instruction {} should have exactly two arguments".format(inst.attrib["opcode"]), UnexpectedXMLStructureErr)
            if (inst.attrib["opcode"].upper() in instructionsWithThreeArg and len(inst) != 3):
                err_msg("Instruction {} should have exactly three argument".format(inst.attrib["opcode"]), UnexpectedXMLStructureErr)

            argNumber = 1
            for arg in inst:
                argFormat = "arg" + str(argNumber)
                try:
                    arg.attrib["type"]
                except KeyError:
                    err_msg("Argument {} without 'type'".format(arg.attrib), UnexpectedXMLStructureErr)
                
                if (arg.tag != argFormat):
                    err_msg("Argument's tag in {} is not valid".format(arg.attrib), UnexpectedXMLStructureErr)
                
                if (arg.attrib["type"] not in argumentTypes):
                    err_msg("Argument type is not supported in {}".format(arg.attrib), UnexpectedXMLStructureErr)

                # Check text format of arguments
                if (arg.attrib["type"] == "int"):
                    if (not re.match('^(\+|-|)[0-9]+$', arg.text)):
                        err_msg("Integer with value '{}' is not supported".format(arg.text), UnexpectedXMLStructureErr)
                elif (arg.attrib["type"] == "bool"):
                    if (not re.match('^(true|false)$', arg.text)):
                        err_msg("Bool with value '{}' is not supported".format(arg.text), UnexpectedXMLStructureErr)
                elif (arg.attrib["type"] == "string"):
                    if (arg.text != None):
                        if (not re.match('^([^\\\\\#\s]|(\\\\\d{3}))*$', arg.text)):
                            err_msg("String with value '{}' is not supported".format(arg.text), UnexpectedXMLStructureErr)
                elif (arg.attrib["type"] == "label"):
                    if (not re.match('^[a-zA-Z_\-\$&%*!?][0-9a-zA-Z_\-\$&%*!?]*$', arg.text)):
                        err_msg("Label with value '{}' is not supported".format(arg.text), UnexpectedXMLStructureErr)
                elif (arg.attrib["type"] == "nil"):
                    if (not re.match('^nil$', arg.text)):
                        err_msg("Nil with value '{}' is not supported".format(arg.text), UnexpectedXMLStructureErr)

                argNumber += 1

        try:
            order = int(inst.attrib["order"])
        except ValueError:
            err_msg("The 'order' number is not a number in instruction {}".format(inst.attrib), UnexpectedXMLStructureErr)

        numOfInst = int(inst.attrib["order"])

        # Order attribute checks
        if numOfInst < 1:
            err_msg("Order attribute in instruction {} is lower than 1".format(inst.attrib), UnexpectedXMLStructureErr)

        if inst.attrib["opcode"].upper() not in self.listOfinstructions:
            err_msg("Operation code in {} is not valid in IPPCode20".format(inst.attrib), UnexpectedXMLStructureErr)

    def get_program_tree(self):
        """
        Returns the program_tree

        """

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
    Interpret(program_tree, inputFile).interpret_the_language()
    sys.exit(0)