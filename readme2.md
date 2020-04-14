Implementační dokumentace k 2. úloze do IPP 2019/2020  
Jméno a příjmení: Lukas Javorsky  
Login: xjavor20  

# Interpret.py

The `interpret.py` script interprets the IPPCode20 (xml format) which is read from either `--source=` file 
or (when the `source` option is not given) from the `stdin`.  
If the `READ` instruction is part of the source code, reading is done from either `--input=` file 
or (when the `input` option is not given) from the `stdin`.  
At least one of the options (`source | input`) have to be given, for interpret to work.  

## Options

As mentioned above, there are some options that `interpret.py` can process.  
There is `--help` option that prints short manual, that should help the user to run the script.  
Script also have two option which specifies the source and input files.  
At least one of these options is mandatory.  
`--source=file` specifies the source file, which contains the instructions.  
`--input=file` specifies the input file, that is read during READ instruction.  
If one of them is not given, the content is read from stdin

## Interpretation

### Reading XML source file

Firstly the script does need to check if the xml source file is `well-formed`.  
Next the lexical and syntactic correction of the source is checked.  
If everything goes well, the `program_tree` structure is created with all instructions.  
The script also sorts the instruction in program_tree by their `order` value.  

### Interpreting every instruction

The instruction are interpreted one by one, and divided into few steps.  

#### Label defining

First thing that needs to be done is to define all `labels` in the code.  
It needs to be done before every other instruction, because if there was an instruction,
that somehow working with `instruction_pointer`, it needs to know where should it go (jump).  
Also every label is stored in `UniqueDict` structure and checked for it's unique name.  

#### Instruction execution

When the labels are defined, the interpret can execute the `instructions` one by one.
Every instruction is checked if it's semantically correct.  
The semantic is defined in `IPPCode20` language.  

#### Output

The output of the interpret, is stored in `output array`.  
Only `WRITE` instruction can store to this array.  
If the interpret fails, and the `output array` is not empty, it is thrown away.  
If the `EXIT` instruction is executed, or the program has reached the end, the `output array` is printed on `stdout`.

### Error cases

If any error during the interpretation have been raised, the script ends with `corresponding exit code`,
and with `error message`.  
Most of the error messages contains the instruction which caused this error.


# Test.php

`test.php` is testing script for `parse.php` and `interpret.py`, which prints the `html output` on `stdout`.  
Test is testing the `output files` and `return codes` of the component that is tested.  
It needs the testing directory which contains at least `.src` file.

## Options

Script comes with lot of option, affects the output, the testing component or the testing directory.  
`--help` prints the basic help for user.  
`--directory=dir` Specifies the directory which contains the tests. Default value is `./` if not given.  
`--recursive` Makes the script to look for the tests recursively.  
`--parse-script=file` Specifies the name of the parse script. Default value is `./parse.php` if not given.  
`--parse-only` Makes the script to test only parse script. Cannot be combined with `--int*` options.  
`--int-script=file` Specifies the name of the interpret script. Default value is `./interpret.py` if not given.  
`--int-only` Makes the script to test only interpret script. Cannot be combined with `--parse*` options.  
`--jexamxml=file` Specifies the JAR file, which is used to compare parse output. Default value is `./pub/courses/ipp/jexamxml/jexamxml.jar` if not given. 

Also the `option` file for `jexamxml` have to be located at `/pub/courses/ipp/jexamxml/options`. 

## Internal setup

Test does some setup, to make the testing possible.  
If the `.out`, `.rc` or `.in` files are missing inside of the tests directory, the `test.php` creates them with default values.  
Default value for `.out` file is `''` ; for `.rc` is `0` ; for `.in` is `''`.  

## What component to test?

There are 3 possibilities, that test can perform.  

### Parse-only

Only the `parser` is tested. The `--parse-only` option must be given.  
The `return codes` are compared and if something differ, the test result is `fail`.  
If the `rc=0`, script creates the `.xml` file from parser's output, and compares it with `reference .xml` file.  
The comparison is done by JAR file with A7Soft JExamXML.  

### Int-only

Only the `interpreter` is tested. The `--int-only` option must be given.  
Test `diffs` the interpret's `output` and `return codes` with reference ones.  
If something differs, the test is labeled as `failed`.

### Both

Test is run for the `parser` first and then, if everything was successful, it sends
the output to the `interpreter` and diffs the `output` and `rc`.  

## Output

Output of the test is stored in `html` format and printed on `stdout`.  
The format of the file is specified in `./test_src/html-part.php`.  
The `header` of the test contains how many tests failed, how many passed and percentage of successfulness.  
If the test passed, it's labeled as `passed` and is coloured `green`.  
If the test failed, it's labeled as `failed`, is coloured `red` and the diff can be showed when `Show diff` is pressed.  