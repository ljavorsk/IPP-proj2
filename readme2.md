Implementační dokumentace k 2. úloze do IPP 2019/2020  
Jméno a příjmení: Lukas Javorsky  
Login: xjavor20  

# Interpret.py

The `interpret.py` script interprets the IPPCode20 (xml format) which is read from either `--source=` file 
or (when the `source` option is not given) from `stdin`.  
If the `READ` instruction is part of the source code, reading is done from either `--input=` file 
or (when the `input` option is not given) from the `stdin`.  

## Options

As mentioned above, there are some options that `interpret.py` can process.  
There is `--help` option that prints short manual, that should help the user to run the script.  
Script also have two option which specifies the source and input files.  
At least one of the options (`source | input`) have to be given for interpret to work.  
`--source=file` specifies the source file, which contains the instructions.  
`--input=file` specifies the input file, that is read during READ instruction.  
If only one of them is not given, the content is read from stdin

## Interpretation

### Reading XML source file

First, the script does need to check if the xml source file is "well-formed".  
Next, the script checks the lexical and syntactic correctness of source file.  
If everything goes well, the script creates the `program_tree` structure with all instructions.  
The script also sorts the instructions in program_tree by their `order` value.  

### Interpreting every instruction

The script interprets the instructions one by one using the following process:   

#### Label defining

The script's first task is to define all `labels` in the code.  
This must be done first because, if there was an instruction
that somehow works with `instruction_pointer`, it needs to know where it should go (jump).  
Every label is then stored inside of the `UniqueDict` structure and it is checked for its unique name.  

#### Instruction execution

When the labels are defined, the interpret can execute the `instructions` one by one.
Every instruction is checked if it's semantically correct.  
The semantic is defined in `IPPCode20` language.  

#### Output

The output of the interpret is stored in `output array`.  
Only `WRITE` instruction can store something in this array.  
If the interpret fails and the `output array` is not empty, the content is thrown away.  
If the `EXIT` instruction is executed, or the program has reached the end, `output array` is printed on `stdout`.

### Error cases

If any error during the interpretation has been raised, the script terminates with `corresponding exit code`,
and with following `error message`.  
Most of the error messages contain the instruction which caused this error.


# Test.php

`test.php` is a testing script for `parse.php` and `interpret.py` which prints the `html output` on `stdout`.  
The script tests the `output files` and `return codes` of the selected component.  
In order to run, it needs a testing directory which contains `.src` files of the tests, and possibly `.out .rc .in` files too.

## Options

Script comes with a lot of options, that affects the output, the testing component or the testing directory.  
`--help` Prints the basic help for the user.  
`--directory=dir` Specifies the directory which contains the tests. Default value is `./` if not given.  
`--recursive` Makes the script look for the tests recursively.  
`--parse-script=file` Specifies the name of the parse script. Default value is `./parse.php` if not given.  
`--parse-only` Makes the script test only parse script. Cannot be combined with `--int*` options.  
`--int-script=file` Specifies the name of the interpret script. Default value is `./interpret.py` if not given.  
`--int-only` Makes the script test only interpret script. Cannot be combined with `--parse*` options.  
`--jexamxml=file` Specifies the JAR file, which is used to compare parse output. Default value is `./pub/courses/ipp/jexamxml/jexamxml.jar` if not given. 

Also the `option` file for `jexamxml` have to be located at `/pub/courses/ipp/jexamxml/options`. 

## Internal setup

Test does some setup in order to make the testing possible.  
If the `.out`, `.rc`, or `.in` files are missing inside of the tests directory, the script creates them with default values.  
Default values:  
for `.out` = `''`
for `.rc`  = `0`  
for `.in`  = `''`.  

## What component to test?

There are 3 possibilities that test can perform:  

### Parse-only

Test only `parser`. The `--parse-only` option must be given.  
The `return codes` are compared with the reference, and if something differs, the test `failed`.  
If the parser `rc=0`, script creates an `.xml` file from parser's output, and compares it with `reference .xml` file.  
The comparison is done by JAR file with A7Soft JExamXML.  

### Int-only

Test only `parser`. The `--int-only` option must be given.  
Test diffs the interpret's `output` and `return codes` with reference ones.  
If something differs, the test is labeled as `failed`.

### Both

Test checks the `parser` first. If everything was successful, it sends
the parser's output to `interpret's` stdin and checks it with the reference file.  

## Output

The test's output is stored in `html` format and printed on `stdout`.  
The format of the html is specified in `./test_src/html-part.php`.  
The `header` contains how many tests failed, how many passed and percentage of successfulness.  
If the test passed, it is labeled as `passed`, and coloured `green`.  
If the test failed, it is labeled as `failed`, coloured `red` and the diff is showed when `Show diff` is pressed.  