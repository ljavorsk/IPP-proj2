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
InternalErr = 99

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
        self.LFTop = None
        self.LFStack = None
        self.TF = None
        self.labels = {}
        self.labels = UniqueDict(self.labels)
        self.varStack = []
        self.instPointerStack = None
        self.output = None

    def set_all_labels(self):
        """
        Checking all the label if they are valid and unique, and stores them to the label array
        """

        for inst in self.program:
            if (inst.attrib["opcode"].upper() == "LABEL"):
                for arg in inst:
                    try:
                        self.labels[arg.text] = inst.attrib["order"]
                    except KeyError:
                        err_msg("Label '{}' in instruction {} is being redefined".format(arg.text, inst.attrib), SemanticErr)

    def interpret_the_language(self):
        """
        Interprets the language
        """

        self.set_all_labels()
        self.instructPointer = 0

        while self.instructPointer < len(self.program):

            # Is it a jump?
            if (self.program[self.instructPointer].attrib["opcode"] in jumpingInst):
                self.instructPointer = self.do_instruction(self.program[self.instructPointer])
            else:
                self.do_instruction(self.program[self.instructPointer])

            self.instructPointer += 1
        
        # Write everything to stdout
        if (self.output != None):
            for out in self.output:
                print (out, end='')
        
    def do_instruction(self, inst):
        """
        Perform the instruction
        """

        def var_arg(inst, whatArg, is_symb=False):
            """
            Returns the type and value of the arg <var>
            """
            
            for arg in inst:
                if (arg.tag == whatArg):
                    if (arg.text is None):
                        arg.text = ""
                    if (arg.attrib["type"] != "var"):
                        if (is_symb):
                            return None
                        err_msg("{} is not valid var name in instruction {}".format(arg.text, inst.attrib),UnexpectedXMLStructureErr)
                    if (not re.match('^[L,T,G]F@[a-zA-Z_\-\$&%*!?][0-9a-zA-Z_\-\$&%*!?]*$', arg.text)):
                        if (is_symb):
                            return None
                        err_msg("{} is not valid var name in instruction {}".format(arg.text, inst.attrib),UnexpectedXMLStructureErr)
                    return arg
            return None

        def symb_arg(inst, whatArg):
            """
            Returns the type and value of the arg <symb>
            """
            
            var = var_arg(inst, whatArg, is_symb=True)
            if (var is not None):
                return "var", var
            for arg in inst:
                if (arg.tag == whatArg):
                    return arg.attrib["type"], arg

            # didn't fit any format
            err_msg("The <symb> value is not valid in {} argument".format(arg), UnexpectedXMLStructureErr)

        def label_arg(inst, whatArg):
            """
            Returns the valid label from arg <label>
            """

            for arg in inst:
                if whatArg == arg.tag:
                    if arg.attrib["type"] != "label":
                        err_msg("Argument is not a label type in instruction '{}'".format(inst.attrib), UnexpectedXMLStructureErr)

                    return arg.text
            return None
        
        def search_in_frame(frameType, frameName):
            """
            Looks for the variable in frames, and if it's found returns the frame
            """

            if (frameType == "GF"):
                try:
                    self.GF[frameName]
                except KeyError:
                    err_msg("Global frame with variable name '{}' doesn't exists", VariableDoesntExistsErr)
                return self.GF

            elif frameType == "LF":
                if (self.LFTop is None):
                    err_msg("Local frame is not created yet", FrameDoesntExistsErr)

                try:
                    self.LFTop[frameName]
                except KeyError:
                    err_msg("Local frame with variable name '{}' doesn't exists", VariableDoesntExistsErr)
                return self.LFTop

            elif frameType == "TF":
                if (self.TF is None):
                    err_msg("Temporary frame is not created yet", FrameDoesntExistsErr)

                try:
                    self.TF[frameName]
                except KeyError:
                    err_msg("Temporary frame with variable name '{}' doesn't exists", VariableDoesntExistsErr)
                return self.TF

        def get_var(arg, isType=False):
            """
            Returns the type and value of the arg <var>
            """

            frame, name = get_frame_and_name(arg)
            varsFrame = search_in_frame(frame, name)

            argType = varsFrame[name]['type']
            argValue = varsFrame[name]['value']

            if ((argValue is None or argType is None) and isType == False):
                err_msg("Uninitialized variable in arg: {}. In instruction: {}".format(arg.tag, inst.attrib), MissingValueErr)
            return argType, argValue

        def get_type_value(arg, typeOfArg, isType=False):
            """
            Returns the type and value of the argument <symb>
            """
            
            if (typeOfArg == "var"):
                typeOfArg, argValue = get_var(arg, isType)
            else:
                argValue = arg.text

            return typeOfArg, argValue

        def get_frame_and_name(arg):
            """
            Returns the frame and name of the argument
            """

            arg_split = arg.text.split('@', 1)
            frame = arg_split[0]
            name = arg_split[1]

            return (frame, name)

        def get_var_symb_symb():
            """
            Returns the crusial variables needed in <var><symb><symb> instructions
            """

            arg1 = var_arg(inst, "arg1")
            
            frame, name = get_frame_and_name(arg1)
            varsFrame = search_in_frame(frame, name)

            arg2Type, arg2Body = symb_arg(inst, "arg2")
            arg2Type, arg2Value = get_type_value(arg2Body, arg2Type)

            arg3Type, arg3Body = symb_arg(inst, "arg3")
            arg3Type, arg3Value = get_type_value(arg3Body, arg3Type)

            if (arg2Type is None or arg3Type is None):
                err_msg("Uninitialized variabel in arg2 or arg3 in instruction {}".format(inst.attrib),MissingValueErr)

            return name, varsFrame, arg2Type, arg2Value, arg3Type, arg3Value

        def aritmetic_operations():
            """
            Do setup for aritmetic operations
            """

            name, varsFrame, arg2Type, arg2Value, arg3Type, arg3Value = get_var_symb_symb()

            if (arg2Type is None or arg3Type is None):
                err_msg("Value in one or more instruction arguments are not defined, Instruction: {}".format(inst.attrib), MissingValueErr)

            if (arg2Type != "int" or arg3Type != "int"):
                err_msg("Arguments have to be type of 'int' in instruction {}".format(inst.attrib), WrongOperandTypeErr)
            
            try:
                arg2Value = int(arg2Value)
                arg3Value = int(arg3Value)
            except TypeError:
                err_msg("Cannot convert value to int type in instruction {}".format(inst.attrib), InternalErr)

            return (arg2Value, arg3Value, varsFrame, name)

        
        def convert_unicode_values_in_string(string):
            """
            Converts every unicode sequence in string to the coresponding character
            """

            for unicode_sequence in re.findall('\\\\[0-9]{3}', string):
                string = string.replace(unicode_sequence, chr(int(unicode_sequence[1:])))
            return string

        def defvar():
            """
            Defines the arg1 variable
            """

            arg1 = var_arg(inst, "arg1")

            frame, name = get_frame_and_name(arg1)

            if (frame == "GF"):
                if (name in self.GF.keys()):
                    err_msg("Global frame {} is being redefined".format(name), SemanticErr)
                else:
                    self.GF[name] = {'type': None, 'value': None}
            elif (frame == "LF"):
                if type(self.LFTop) == dict:
                    if (name in self.LFTop.keys()):
                        err_msg("Local frame {} is being redefined".format(name), SemanticErr)
                    else:
                        self.LFTop[name] = {'type': None, 'value': None}
                else:
                    err_msg("Local frame with name '{}' is not created".format(name), FrameDoesntExistsErr)
            
            elif (frame == "TF"):
                if (type(self.TF) == dict):
                    if (name in self.TF.keys()):
                        err_msg("Temporary frame {} is being redefined".format(name), SemanticErr)
                    else:
                        self.TF[name] = {'type': None, 'value': None}
                else:
                    err_msg("Temporary frame with name '{}' is not created".format(name), FrameDoesntExistsErr)

        def move():
            """
            Copies the arg2 value to the arg1 variable
            """

            arg1 = var_arg(inst, "arg1")

            frame, name = get_frame_and_name(arg1)
            varsFrame = search_in_frame(frame, name)

            arg2Type, arg2Body = symb_arg(inst, "arg2")

            if (arg2Body is None):
                err_msg("Value of arg2 is empty in instruction {}".format(inst.attrib), UnexpectedXMLStructureErr)

            if (arg2Type == "int"):
                argStruct = {'type': 'int', 'value': int(arg2Body.text)}
            elif (arg2Type == "var"):
                arg2Type, arg2Value = get_var(arg2Body)
                argStruct = {'type': arg2Type, 'value': arg2Value}
            else:
                argStruct = {'type': arg2Type, 'value': arg2Body.text}

            varsFrame[name] = argStruct

        def add():
            """
            Performs add on arg2 and arg3 values and stores it to arg1 variable
            """

            arg2Value, arg3Value, varsFrame, name = aritmetic_operations()

            resultOfAdition = {'type': 'int', 'value': arg2Value + arg3Value}

            varsFrame[name] = resultOfAdition

        def mul():
            """
            Performs mul on arg2 and arg3 values and stores it to arg1 variable
            """

            arg2Value, arg3Value, varsFrame, name = aritmetic_operations()

            resultOfAdition = {'type': 'int', 'value': arg2Value * arg3Value}

            varsFrame[name] = resultOfAdition

        def sub():
            """
            Performs sub on arg2 and arg3 values and stores it to arg1 variable
            """

            arg2Value, arg3Value, varsFrame, name = aritmetic_operations()

            resultOfAdition = {'type': 'int', 'value': arg2Value - arg3Value}

            varsFrame[name] = resultOfAdition

        def idiv():
            """
            Performs idiv on arg2 and arg3 values and stores it to arg1 variable
            """

            arg2Value, arg3Value, varsFrame, name = aritmetic_operations()

            if (arg3Value == 0):
                err_msg("Zero division in {}".format(inst.attrib), WrongOperandValue)

            resultOfAdition = {'type': 'int', 'value': arg2Value // arg3Value}

            varsFrame[name] = resultOfAdition

        def write():
            """
            Writes the arg1 value to the output array, which is printed at the end
            """

            arg1Type, arg1 = symb_arg(inst, "arg1")

            if (arg1Type == "var"):
                arg1Type, arg1Value = get_var(arg1)
                if (arg1Type is None):
                    err_msg("Variable is uninitialized in instruction {}".format(inst.attrib), VariableDoesntExistsErr)
            else:
                arg1Value = arg1.text

            if (arg1Value == "nil" and arg1Type == "nil"):
                arg1Value = ""

            if (self.output == None):
                self.output = []

            if (type(arg1Value) == str):
                self.output.append(convert_unicode_values_in_string(arg1Value))
            else:
                self.output.append(arg1Value)


        def _read():
            """
            Reads from input and stores it if
            1) the arg2 type is same as readed
            Stores it to the arg1 variable
            If anything went wrong nil@nil is stored
            """

            arg1 = var_arg(inst, "arg1")

            frame, name = get_frame_and_name(arg1)
            varsFrame = search_in_frame(frame, name)

            readType = None

            if (self.input is None):
                try:
                    readValue = input()
                except EOFError:  
                    readValue = None
            else:
                if type(self.input) != list:
                    self.input = self.input.splitlines()

                if type(self.input) == list:
                    if len(self.input) == 0:
                        readValue = None
                    else:
                        readValue = self.input.pop(0)
            for arg in inst:
                if (arg.tag == "arg2"):
                    defaultValue = "nil"
                    defaultType = "nil"

                    if (arg.attrib["type"] != "type"):
                        err_msg("Argument type in argument {} have to be 'type'... Instruction: {}".format(arg.attrib, inst.attrib))
                    if (readValue is None):
                        readValue = defaultValue
                        readType = defaultType
                    elif (arg.text == "string"):
                        readType = "string"
                    elif(arg.text == "int"):
                        readType = "int"
                        if (not re.match('^(\+|-|)[0-9]+$', readValue)):        # Not supported int value
                            readValue = defaultValue
                            readType = defaultType
                    elif(arg.text == "bool"):
                        readType = "bool"
                        readValue = readValue.upper()
                        if (not re.match('^(TRUE)$', readValue)):
                            readValue = "false"
                        else:
                            readValue = "true"  
                    else:
                        readValue = defaultValue
                        readType = defaultType
            
            argStruct = {'type': readType, 'value': readValue}
            varsFrame[name] = argStruct

        def create_frame():
            """
            Creates the TF frame
            """

            self.TF = {}

        def push_frame():
            """
            Pushs the TF frame and stores it to the LF
            """

            if (self.TF is None):
                err_msg("The temporary frame doesn't exists", FrameDoesntExistsErr)

            if (self.LFStack is None):
                self.LFStack = []

            self.LFStack.append(self.TF)
            self.TF = None
            self.LFTop = self.LFStack[len(self.LFStack) -1]

        def pop_frame():
            """
            Pops the LF frame and stores it to the TF
            """

            if (self.LFStack is None):
                err_msg("There is no local frame left to be poped", FrameDoesntExistsErr)
            if (len(self.LFStack) > 0):
                self.TF = self.LFStack.pop()
                if (len(self.LFStack) > 0):
                    self.LFTop = self.LFStack[len(self.LFStack) -1]
                elif (len(self.LFStack) == 0):
                    self.LFTop = None
            else:
                err_msg("There is no local frame left to be poped", FrameDoesntExistsErr)

        def label():
            """
            Does nothing, because the label are already done at the beginning
            """

            # Already done in the beginnig
            return
        
        def jump():
            """
            Perform jump in instruction counter
            """

            jumpingOn = label_arg(inst, "arg1")

            if (jumpingOn in self.labels.keys()):
                try:
                    jumpingOn = int(self.labels[jumpingOn]) - 1
                except TypeError:
                    err_msg("Cannot convert value to int type in instruction {}".format(inst.attrib), InternalErr)
                return jumpingOn
            else:
                err_msg("Undefined label with name '{}'".format(jumpingOn), SemanticErr)

        def jumpifeq():
            """
            Perform jump in instruction counter if arg2 and arg3 are equal
            """

            jumpingOn = label_arg(inst, "arg1")

            if (jumpingOn in self.labels.keys()):
                try:
                    jumpingOn = int(self.labels[jumpingOn]) - 1
                except TypeError:
                    err_msg("Cannot convert value to int type in instruction {}".format(inst.attrib), InternalErr)
            else:
                err_msg("Undefined label with name '{}'".format(jumpingOn), SemanticErr)

            arg2Type, arg2Body = symb_arg(inst, "arg2")
            arg2Type, arg2Value = get_type_value(arg2Body, arg2Type)

            arg3Type, arg3Body = symb_arg(inst, "arg3")
            arg3Type, arg3Value = get_type_value(arg3Body, arg3Type)

            if (arg2Type is None or arg3Type is None):
                err_msg("Value in one or more instruction arguments are not defined, Instruction: {}".format(inst.attrib), MissingValueErr)

            # Convert
            if (arg2Type == "string" and arg3Type == "string"):
                arg2Value = convert_unicode_values_in_string(arg2Value)
                arg3Value = convert_unicode_values_in_string(arg3Value)
            elif (arg2Type == "int" and arg3Type == "int"):
                try:
                    arg2Value = int(arg2Value)
                    arg3Value = int(arg3Value)
                except TypeError:
                    err_msg("Cannot convert value to int type in instruction {}".format(inst.attrib), InternalErr)

            if (arg2Type != arg3Type and arg2Type != "nil" and arg3Type != "nil"):
                err_msg("Operands cannot be compared in instruction '{}'".format(inst.attrib), WrongOperandTypeErr)
            elif (arg2Type == "nil" and arg3Type == "nil"):
                doJump = True
            else:
                doJump = arg2Value == arg3Value

            if (doJump):
                return jumpingOn
            else:
                return self.instructPointer

        def jumpifneq():
            """
            Perform jump in instruction counter if arg2 and arg3 are not equal
            """

            jumpingOn = label_arg(inst, "arg1")
            doJump = jumpifeq()
            jumpingOn = int(self.labels[jumpingOn]) - 1

            # Invert jumpifeq
            if (doJump != self.instructPointer):    # EQ would jump
                return self.instructPointer     # NEQ won't
            else:
                return jumpingOn

        def _type():
            """
            Stores the type of the arg2 to the arg1 variable
            """

            arg1 = var_arg(inst, "arg1")    

            frame, name = get_frame_and_name(arg1)
            varsFrame = search_in_frame(frame, name)  

            arg2Type, arg2Body = symb_arg(inst, "arg2")
            arg2Type, arg2Value = get_type_value(arg2Body, arg2Type, isType=True)

            if arg2Type is None:
                arg2Type = ""

            argStruct = {'type': 'string', 'value': arg2Type}
            varsFrame[name] = argStruct

        def _exit():
            """
            Exits the program with arg1 exit code
            Prints the output which should be printed before exiting
            """

            arg1Type, arg1Body = symb_arg(inst, "arg1")
            arg1Type, arg1Value = get_type_value(arg1Body, arg1Type)

            if (arg1Type is None):
                err_msg("Uninitialized variable in {}".format(inst.attrib), MissingValueErr)

            if (arg1Type != "int"):
                err_msg("Exit value can be only 'int' type", WrongOperandTypeErr)

            try:
                exitCode = int(arg1Value)
            except TypeError:
                err_msg("Cannot convert value to int type in instruction {}".format(inst.attrib), InternalErr)

            if (0 <= exitCode <= 49):
                # Write if anything should be writen before exit
                if (self.output is not None):
                    for out in self.output:
                        print (out, end='')
                sys.exit(exitCode)
            else:
                err_msg("Exit code cannot be lower than 0 nor bigger than 49", WrongOperandValue)

        def pushs():
            """
            Push the arg1 <symb> to the varStack
            """

            arg1Type, arg1Body = symb_arg(inst, "arg1")
            arg1Type, arg1Value = get_type_value(arg1Body, arg1Type)

            if (arg1Type is None):
                err_msg("Uninitialized variable cannot be pushed... Instruction {}".format(inst.attrib), MissingValueErr)

            varToBePushed = {'type': arg1Type, 'value': arg1Value}
            self.varStack.append(varToBePushed)

        def pops():
            """
            Pops the arg1 <symb> from the varStack
            """

            if (len(self.varStack) < 1):
                err_msg("Empty stack cannot be poped in instruction {}".format(inst.attrib), MissingValueErr)
            arg1 = var_arg(inst, "arg1")

            frame, name = get_frame_and_name(arg1)
            varsFrame = search_in_frame(frame, name)

            varToBePoped = self.varStack.pop()
            varsFrame[name] = varToBePoped

        def int2char():
            """
            Convert the int from arg2 value to the string and stores it to the arg1 variable
            """

            arg1 = var_arg(inst, "arg1")

            frame, name = get_frame_and_name(arg1)
            varsFrame = search_in_frame(frame, name)

            arg2Type, arg2Body = symb_arg(inst, "arg2")
            arg2Type, arg2Value = get_type_value(arg2Body, arg2Type)

            if (arg2Value is None):
                err_msg("Uninitialized value of integer in instruction {}".format(inst.attrib), MissingValueErr)

            if (arg2Type != "int"):
                err_msg("arg2 value can be only 'int' type", WrongOperandTypeErr)
            
            try:
                arg2Value = int(arg2Value)
            except TypeError:
                err_msg("Cannot convert value to int type in instruction {}".format(inst.attrib), InternalErr)
            
            try:
                converted = chr(arg2Value)
            except ValueError:
                err_msg("The value in instruction cannot be converted... Instruction: {}".format(inst.attrib), StringOperationErr)

            argStruct = {'type': 'string', 'value': converted}
            varsFrame[name] = argStruct

        def stri2int():
            """
            Convert the string from arg2 value at arg3 index to the int and stores it to the arg1 variable
            """

            name, varsFrame, arg2Type, arg2Value, arg3Type, arg3Value = get_var_symb_symb()

            if (arg2Type == "string"):
                arg2Value = convert_unicode_values_in_string(arg2Value)
            else:
                err_msg("The second argument is not a string in {}".format(inst.attrib), WrongOperandTypeErr)

            if (arg3Type != "int"):
                err_msg("The third argument is not an int in {}".format(inst.attrib), WrongOperandTypeErr)

            try:
                arg3Value = int(arg3Value)
            except TypeError:
                err_msg("Cannot convert value to int type in instruction {}".format(inst.attrib), InternalErr)

            if (int(arg3Value) < 0):
                err_msg("Negative number in index in instruction {}".format(inst.attrib), StringOperationErr)
            
            try:
                argStruct = {'type': 'int', 'value': ord(arg2Value[arg3Value])}
            except:
                err_msg("Function ord() exception caught in instruction {}".format(inst.attrib), StringOperationErr)
            varsFrame[name] = argStruct

        def _return():
            """
            Returns to the previous CALL instruction
            """

            if (self.instPointerStack is None or len(self.instPointerStack) < 1):
                err_msg("Return called without previos CALL instruction", MissingValueErr)
            else:
                return self.instPointerStack.pop()

        def call():
            """
            Jumping on the arg1 label, and storing the instruction pointer of the CALL for RETURN inst
            """

            callingLabel = label_arg(inst, "arg1")

            if (callingLabel in self.labels.keys()):
                if (self.instPointerStack is None):
                    self.instPointerStack = []
                try:
                    int(inst.attrib["order"])
                except TypeError:
                    err_msg("Cannot convert value to int type in instruction {}".format(inst.attrib), InternalErr)

                self.instPointerStack.append(int(inst.attrib["order"]))
                return (int(self.labels[callingLabel]) -1)
            else:
                err_msg("Undefined label in CALL instruction... Instruction: {}".format(inst.attrib), SemanticErr)

        def _break():
            """
            Prints the current instruction, all frames and how many instructions were executed already
            """

            print("Break instruction executed as {}. in order".format(inst.attrib["order"]),file=sys.stderr)
            print("GF: {}".format(self.GF),file=sys.stderr)
            print("LF: {}".format(self.LFTop),file=sys.stderr)
            print("TF: {}".format(self.TF),file=sys.stderr)
            print("Instructions already executed: {}".format(inst.attrib["order"] - 1),file=sys.stderr)

        def dprint():
            """
            Prints the value of arg1 to the stderr
            """

            arg1Type, arg1Body = symb_arg(inst, "arg1")
            arg1Type, arg1Value = get_type_value(arg1Body, arg1Type)

            if (arg1Type == "nil" and arg1Value == "nil"):
                arg1Value = ""

            if (type(arg1Value) == str):
                print(convert_unicode_values_in_string(arg1Value), end='', file=sys.stderr)
            else:
                print(arg1Value, end='', file=sys.stderr)

        def strlen():
            """
            Stores the length of string in arg2 to the arg1 variable
            """

            arg1 = var_arg(inst, "arg1")

            frame, name = get_frame_and_name(arg1)
            varsFrame = search_in_frame(frame, name)

            arg2Type, arg2Body = symb_arg(inst, "arg2")
            arg2Type, arg2Value = get_type_value(arg2Body, arg2Type)

            if (arg2Type == "string"):
                arg2Value = convert_unicode_values_in_string(arg2Value)
            else:
                err_msg("The second argument is not a string in {}".format(inst.attrib), WrongOperandTypeErr)

            argStruct = {'type': 'int', 'value': len(arg2Value)}

            varsFrame[name] = argStruct

        def _not():
            """
            Performs NOT operation on arg2 bool value and stores it to arg1 variable
            """

            arg1 = var_arg(inst, "arg1")

            frame, name = get_frame_and_name(arg1)
            varsFrame = search_in_frame(frame, name)

            arg2Type, arg2Body = symb_arg(inst, "arg2")
            arg2Type, arg2Value = get_type_value(arg2Body, arg2Type)

            if (arg2Type != "bool"):
                err_msg("The second argument is not a bool in {}".format(inst.attrib), WrongOperandTypeErr)

            if (arg2Value == "true"):
                argStruct = {'type': 'bool', 'value': 'false'}
                varsFrame[name] = argStruct
            elif (arg2Value == "false"):
                argStruct = {'type': 'bool', 'value': 'true'}
                varsFrame[name] = argStruct

        def relation_operations_setup():
            """
            Makes a setup for relation operations
            """

            name, varsFrame, arg2Type, arg2Value, arg3Type, arg3Value = get_var_symb_symb()

            if (arg2Type == "int" and arg3Type == "int"):
                try:
                    arg2Value = int(arg2Value)
                    arg3Value = int(arg3Value)
                except TypeError:
                    err_msg("Cannot convert value to int type in instruction {}".format(inst.attrib), InternalErr)
            
            return name, varsFrame, arg2Type, arg2Value, arg3Type, arg3Value

        def make_correct_form_of_result(result):
            """
            Convert the bool result value to the string result
            """

            if (result):
                result = "true"
            else:
                result = "false"

            return result

        def lt():
            """
            Performs the 'less than' (<) operation between arg2 and arg3... stores the result to arg1 variable
            """
            
            name, varsFrame, arg2Type, arg2Value, arg3Type, arg3Value = relation_operations_setup()
            result = None

            if (arg2Type == "int" and arg3Type == "int"):
                result = arg2Value < arg3Value
            elif (arg2Type == "string" and  arg3Type == "string"):
                arg2Value = convert_unicode_values_in_string(arg2Value)
                arg3Value = convert_unicode_values_in_string(arg3Value)
                result = arg2Value < arg3Value
            elif (arg2Type == "bool" and arg3Type == "bool"):
                if arg2Value == "false" and arg3Value == "true":
                    result = True
                else:
                    result = False
            else:
                err_msg("Operand types are not supported in LT instruction", WrongOperandTypeErr)

            result = make_correct_form_of_result(result)
            argStruct = {'type': 'bool', 'value': result}
            varsFrame[name] = argStruct

        def gt():
            """
            Performs the 'greater than' (>) operation between arg2 and arg3... stores the result to arg1 variable
            """
            
            name, varsFrame, arg2Type, arg2Value, arg3Type, arg3Value = relation_operations_setup()
            result = None

            if (arg2Type == "int" and arg3Type == "int"):
                result = arg2Value > arg3Value
            elif (arg2Type == "string" and  arg3Type == "string"):
                arg2Value = convert_unicode_values_in_string(arg2Value)
                arg3Value = convert_unicode_values_in_string(arg3Value)
                result = arg2Value > arg3Value
            elif (arg2Type == "bool" and arg3Type == "bool"):
                if arg2Value == "true" and arg3Value == "false":
                    result = True
                else:
                    result = False
            else:
                err_msg("Operand types are not supported in GT instruction", WrongOperandTypeErr)

            result = make_correct_form_of_result(result)
            argStruct = {'type': 'bool', 'value': result}
            varsFrame[name] = argStruct

        def eq():
            """
            Performs the 'equal' (==) operation between arg2 and arg3... stores the result to arg1 variable
            """
            
            name, varsFrame, arg2Type, arg2Value, arg3Type, arg3Value = relation_operations_setup()
            result = None

            if (arg2Type == "int" and arg3Type == "int"):
                result = arg2Value == arg3Value
            elif (arg2Type == "string" and  arg3Type == "string"):
                arg2Value = convert_unicode_values_in_string(arg2Value)
                arg3Value = convert_unicode_values_in_string(arg3Value)
                result = arg2Value == arg3Value
            elif (arg2Type == "bool" and arg3Type == "bool"):
                if arg2Value == "true" and arg3Value == "true":
                    result = True
                elif arg2Value == "false" and arg3Value == "false":
                    result = True
                else:
                    result = False
            elif (arg2Type == "nil" or arg3Type == "nil"):
                if (arg2Type == "nil" and arg3Type == "nil"):
                    result = True
                else:
                    result = False
            else:
                err_msg("Operand types are not supported in EQ instruction", WrongOperandTypeErr)

            result = make_correct_form_of_result(result)
            argStruct = {'type': 'bool', 'value': result}
            varsFrame[name] = argStruct

        def _and():
            """
            Performs the 'logical AND' (&&) operation between arg2 and arg3... stores the result to arg1 variable
            """

            name, varsFrame, arg2Type, arg2Value, arg3Type, arg3Value = get_var_symb_symb()
            result = None

            if (arg2Type != "bool" or arg3Type != "bool"):
                err_msg("One of the operands are not bool in instruction {}".format(inst.attrib), WrongOperandTypeErr)

            if (arg2Value == "true" and arg3Value == "true"):
                result = True
            else:
                result = False

            result = make_correct_form_of_result(result)
            argStruct = {'type': 'bool', 'value': result}
            varsFrame[name] = argStruct

        def _or():
            """
            Performs the 'logical OR' (||) operation between arg2 and arg3... stores the result to arg1 variable
            """

            name, varsFrame, arg2Type, arg2Value, arg3Type, arg3Value = get_var_symb_symb()
            result = None

            if (arg2Type != "bool" or arg3Type != "bool"):
                err_msg("One of the operands are not bool in instruction {}".format(inst.attrib), WrongOperandTypeErr)

            if (arg2Value == "true" or arg3Value == "true"):
                result = True
            else:
                result = False

            result = make_correct_form_of_result(result)
            argStruct = {'type': 'bool', 'value': result}
            varsFrame[name] = argStruct

        def concat():
            """
            Concatenate the arg2 and arg3 strings and stores the result to arg1 variable
            """

            name, varsFrame, arg2Type, arg2Value, arg3Type, arg3Value = get_var_symb_symb()

            if (arg2Type == "string"):
                arg2Value = convert_unicode_values_in_string(arg2Value)
            else:
                err_msg("The second argument is not a string in {}".format(inst.attrib), WrongOperandTypeErr)

            if (arg3Type == "string"):
                arg3Value = convert_unicode_values_in_string(arg3Value)
            else:
                err_msg("The third argument is not a string in {}".format(inst.attrib), WrongOperandTypeErr)

            argStruct = {'type': 'string', 'value': arg2Value + arg3Value}
            varsFrame[name] = argStruct

        def getchar():
            """
            Get char from arg2 string on arg3 index and stores it to arg1 variable
            """

            name, varsFrame, arg2Type, arg2Value, arg3Type, arg3Value = get_var_symb_symb()

            if (arg2Type == "string"):
                arg2Value = convert_unicode_values_in_string(arg2Value)
            else:
                err_msg("The second argument is not a string in {}".format(inst.attrib), WrongOperandTypeErr)

            if (arg3Type != "int"):
                err_msg("The third argument is not an int in {}".format(inst.attrib), WrongOperandTypeErr)
            if (int(arg3Value) < 0):
                err_msg("Negative number in index in instruction {}".format(inst.attrib), StringOperationErr)
            try:
                argStruct = {'type': 'string', 'value': arg2Value[int(arg3Value)]}
            except IndexError:
                err_msg("GETCHAR is out of the string index in instruction {}".format(inst.attrib), StringOperationErr)
            varsFrame[name] = argStruct

        def setchar():
            """
            Set char to agr1 string from arg3 on arg2 index
            """

            name, varsFrame, arg2Type, arg2Value, arg3Type, arg3Value = get_var_symb_symb()

            arg1Type = varsFrame[name]["type"]
            arg1Value = varsFrame[name]["value"]

            if (arg1Type is None or arg1Value is None):
                err_msg("Uninitialized variadble in arg: arg1. In instruction: {}".format(inst.attrib), MissingValueErr)

            if (arg1Type == "string"):
                arg1Value = convert_unicode_values_in_string(arg1Value)
            else:
                err_msg("The first argument is not a string in {}".format(inst.attrib), WrongOperandTypeErr)

            if (arg2Type != "int"):
                err_msg("The second argument is not an int in {}".format(inst.attrib), WrongOperandTypeErr)
            if (int(arg2Value) < 0):
                err_msg("Negative number in index in instruction {}".format(inst.attrib), StringOperationErr)

            if (arg3Type == "string"):
                arg3Value = convert_unicode_values_in_string(arg3Value)
            else:
                err_msg("The third argument is not a string in {}".format(inst.attrib), WrongOperandTypeErr)

            if(len(arg3Value) < 1):
                err_msg("You want to set something into empty string in {}".format(inst.attrib), StringOperationErr)

            string_list = list(arg1Value)
            try:
                string_list[int(arg2Value)] = arg3Value[0]
            except:
                err_msg("IndexError during SETCHAR instruction in {}".format(inst.attrib), StringOperationErr)

            value = "".join(string_list)
            argStruct = {'type': 'string', 'value': value}
            varsFrame[name] = argStruct


        ########            MAIN               ##########
        instructions = {
            "CREATEFRAME": create_frame,
            "PUSHFRAME": push_frame,
            "POPFRAME": pop_frame,
            "RETURN": _return,
            "BREAK": _break,
            # 1 argument
            "DEFVAR": defvar,
            "CALL": call,
            "PUSHS": pushs,
            "POPS": pops,
            "WRITE": write,
            "LABEL": label,
            "JUMP": jump,
            "EXIT": _exit,
            "DPRINT": dprint,
            # 2 arguments
            "MOVE": move,
            "INT2CHAR": int2char,
            "READ": _read,
            "STRLEN": strlen,
            "TYPE": _type,
            "NOT": _not,
            # 3 arguments
            "ADD": add,
            "SUB": sub,
            "MUL": mul,
            "IDIV": idiv,
            "LT": lt,
            "GT": gt,
            "EQ": eq,
            "AND": _and,
            "OR": _or,
            "STRI2INT": stri2int,
            "CONCAT": concat,
            "GETCHAR": getchar,
            "SETCHAR": setchar,
            "JUMPIFEQ": jumpifeq,
            "JUMPIFNEQ": jumpifneq,
        }
        
        result = instructions.get(inst.attrib["opcode"].upper(),
                                        lambda: err_msg("Invalid instruction '{}'".format(inst.attrib["opcode"].upper()), UnexpectedXMLStructureErr))
        return result()

class UniqueDict(dict):
    def __setitem__(self, key, value):
        if (key not in self):
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

        if (self.elementTree.tag == "program"):
            try:
                self.elementTree.attrib["language"]
            except KeyError:
                err_msg("The 'language' atribute is missing in a source file", UnexpectedXMLStructureErr)

            if (self.elementTree.attrib["language"] != "IPPcode20"):
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

        for inst in self.elementTree:
            
            self.check_instruction(inst)

            try:
                unique_order_arr[int(inst.attrib["order"]) - 1] = inst
            except KeyError:
                err_msg("Order numbers are not unique", UnexpectedXMLStructureErr)
        
        orders = []
        for element in unique_order_arr:
            orders.append(element)
        orders.sort()

        index = 0
        for order in orders:
            try:
                program_tree[index] = unique_order_arr[order]
                program_tree[index].attrib["order"] = index
            except:
                err_msg("Some of the instructions had the same order number", UnexpectedXMLStructureErr)
            
            index += 1

        return program_tree

    
    def check_instruction(self, inst):
        """
        Checks if everything is valid in every instruction inside of the source file
        Exit with error if the instruction is not defined by IPPCode20
        """
        
        if (inst.tag != "instruction"):
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

            for arg in inst:
                try:
                    arg.attrib["type"]
                except KeyError:
                    err_msg("Argument {} without 'type'".format(arg.attrib), UnexpectedXMLStructureErr)
                 
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

        try:
            order = int(inst.attrib["order"])
        except ValueError:
            err_msg("The 'order' number is not a number in instruction {}".format(inst.attrib), UnexpectedXMLStructureErr)

        numOfInst = int(inst.attrib["order"])

        # Order attribute checks
        if (numOfInst < 1):
            err_msg("Order attribute in instruction {} is lower than 1".format(inst.attrib), UnexpectedXMLStructureErr)

        if (inst.attrib["opcode"].upper() not in self.listOfinstructions):
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