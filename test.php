<?php
    $intOnly = false;
    $intFileGiven = false;
    $intFile = "./interpret.py";

    $parseOnly = false;
    $parseFileGiven = false;
    $parseFile = "./parse.php";

    $recursive = false;
    $testDirGiven = false;
    $testDir = "./";

    $jexamxmlFileGiven = false;
    $jexamxmlFile = "/pub/courses/ipp/jexamxml/jexamxml.jar";
    $jexamxmlOptions = "/pub/courses/ipp/jexamxml/options";

    $testsCount = 0;
    $testsFailed = 0;

    // ### Errors
    $wrongParamErr = 10;
    $inputFileErr = 11;
    $outputFileErr = 12;
    // ##########

    /**
     * Prints the error message on stderr
     * @param $message: error message
     * @param $rc: exit code
     */
    function err_msg($message, $rc){
        fwrite(STDERR, "Error: $message\n");
        exit($rc);
    }

    /**
     * Goes through directories and search for the *.src files
     * @param $testDir tests directory
     * @return returns all of the *.src files in array
     */
    function rglob($testDir){
        $iterator = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($testDir));
        $testFiles = array();
        foreach ($iterator as $file) {
            if (preg_match("/.*\.src$/",$file)){
                $testFiles[] = $file->getPathname();
            }
        }
        return $testFiles;
    }

    /**
     * Deletes the temporary files, created by this script
     * @param $testName name of the test
     */
    function delete_tmp_files($testName){
        global $outputFileErr;

        if (file_exists("$testName.xml")){
            if(!unlink("$testName.xml"))    // Delete it, not needed anymore
                err_msg("The $testName.xml couldn't be deleted", $outputFileErr);
        }
        if (file_exists("$testName.diff")){
            if(!unlink("$testName.diff"))
                err_msg("The $testName.diff couldn't be deleted", $outputFileErr);
        }
    }

    /**
     * Run the test for only for the parser
     * @param $testName name of the test
     * @return returns test's output
     */
    function parse_only($testName){
        global $parseFile;
        global $jexamxmlOptions;
        global $jexamxmlFile;
        global $testsFailed;

        exec("php7.4 '$parseFile' < '$testName.src' > '$testName.xml'", $parseOut, $parseRC);
        
        if ($parseRC != 0){     // Parser ended with error

            delete_tmp_files($testName);

            $referenceRC = file_get_contents("$testName.rc");

            if ($referenceRC != $parseRC){     // Failed test
                $testsFailed++;
                $didPassed = false;
                
                $diffRC = "Reference RC = $referenceRC ... Parser RC = $parseRC";
                $resultArray = array("testName" => $testName, "passed" => $didPassed, "diff" => $diffRC);
            }
            else {      // Passed test
                $didPassed = true;
                $resultArray = array("testName" => $testName, "passed" => $didPassed);
            }
        }
        else {      // Parser succeded
            if (file_exists("$testName.out")){
                $diffOut = exec(
                    "java -jar '$jexamxmlFile' '$testName.out' '$testName.xml' '$testName.diff' -D '$jexamxmlOptions'",
                    $jexamxmlOutput,
                    $jexamxmlRC);
                }

                if ($jexamxmlRC == 0){
                    $didPassed = true;
                    $resultArray = array("testName" => $testName, "jexamxmlRC" => $jexamxmlRC, "passed" => $didPassed,
                        "errMsg" => $diffOut);
                }
                else {      // Something went wrong
                
                    $testsFailed++;
                    $didPassed = false;
                    if (file_exists("$testName.diff")){
                        $diffXml = file_get_contents("$testName.diff");
                    }

                    if ($jexamxmlRC == 1){
                        $diffXml = str_replace("Changed Element:old","Reference file:", $diffXml);
                        $diffXml = str_replace("Changed Element:new","Output file:", $diffXml);
                        $resultArray = array("testName" => $testName, "jexamxmlRC" => $jexamxmlRC, "passed" => $didPassed,
                            "errMsg" => $diffOut, "diff" => $diffXml);
                    }
                    else {      // JExamXML error
                        $resultArray = array("testName" => $testName, "jexamxmlRC" => $jexamxmlRC,
                            "passed" => $didPassed, "errMsg" => $diffOut);
                    }
                }
                delete_tmp_files($testName);
        }
        return $resultArray;
    }

    /**
     * Run the test for both the parser and the interpreter
     * @param $testName name of the test
     * @return returns test's output
     */
    function both($testName){
        global $parseFile;
        global $testsFailed;

        exec("php7.4 '$parseFile' < '$testName.src' > '$testName.xml'", $parseOut, $parseRC);

        if ($parseRC == 0){     // Parsed
            $resultArray = int_only("xml", $testName);
        }
        else {
            $referenceRC = file_get_contents("$testName.rc");

            if ($referenceRC == $parseRC){      // Passed test
                $didPassed = true;
                $resultArray = array("testName" => $testName, "result" => $didPassed);
            }
            else {      // Failed test
                $testsFailed++;
                $didPassed = false;
                
                $diffRC = "Reference RC = $referenceRC, Parse RC = $parseRC";
                $resultArray = array("testName" => $testName, "result" => $didPassed, "diff" => $diffRC);
            }
        }
        delete_tmp_files($testName);
        return $resultArray;
    }

    /**
     * Run the test only for the interpreter
     * @param $xmlOrSrc defines the postfix of the file, can be either "src" or "xml"
     * @param $testName name of the test
     * @return returns test's output
     */
    function int_only($xmlOrSrc, $testName){
        global $testsFailed;
        global $intFile;

        exec("python3.8 '$intFile' --source='$testName.$xmlOrSrc' < '$testName.in'", $intOut, $intRC);
        $intOut = implode("\n",$intOut);

        $referenceRC = file_get_contents("$testName.rc");
        $referenceOut = file_get_contents("$testName.out");

        if (($referenceRC == $intRC) && ($referenceOut == $intOut)){    // Everything's good
            $didPassed = true;
            $resultArray = array("testName" => $testName, "result" => $didPassed);
        }
        else {      // Failed test
            $testsFailed++;
            $didPassed = false;

            if ($referenceRC != $intRC)
                $diff = "Reference RC = $referenceRC, Interpret RC = $intRC\n";
            if ($referenceOut != $intOut)
                $diff .= "\n Reference Out: $referenceOut \n Interpret Out: $intOut";
            
            $resultArray = array("testName" => $testName, "result" => $didPassed, "diff" => $diff);
        }
        return $resultArray;
    }

    #############################################              MAIN           #########################################

    $longopts  = array(
        "help",    
        "directory:",   
        "recursive",       
        "parse-script:",          
        "int-script:",
        "parse-only",
        "int-only",
        "jexamxml:"
    );

    // Checking name of every argument
    foreach ($argv as $i => $arg){
        if ($i < 1) continue;   // Skip name of the script
        if (preg_match( '/--directory=.+/', $arg) );
        else if (preg_match( '/--help$/', $arg) );
        else if (preg_match( '/--recursive$/', $arg) );
        else if (preg_match( '/--parse-script=.+/', $arg) );
        else if (preg_match( '/--parse-only$/', $arg) );
        else if (preg_match( '/--int-script=.+/', $arg) );
        else if (preg_match( '/--int-only$/', $arg) );
        else if (preg_match( '/--jexamxml=.+/', $arg) );
        else {
            err_msg("Unknown option", $wrongParamErr);
        }
    }

    $myArgs = getopt("", $longopts);

    if (array_search("--help", $argv)){
        if (count($argv) == 2){
            echo "USAGE: php7.4 test.php [OPTIONS]\n\n";
            echo "DESCRIPTION:    ";
            echo "Test.php script is testing modules (default = interpret.py and parse.php)
                by running them with some src files, and comparing their results with
                referencing ones.
                When the comparison is done, the index.html is created as an output.\n";
            echo "OPTIONS:\n";
            echo "      --help               Prints short help for this script\n";
            echo "      --directory=<dir>    Directory where the reference test results are stored (If not given, ./ is used)\n";
            echo "      --recursive          Look for the test recursively inside of 'directory' file\n";
            echo "      --parse-script=<file>   Name of the parsing script (If not given, parse.php is used)\n";
            echo "      --int-script=<file>   Name of the interpret script (If not given, interpret.py is used)\n";
            echo "      --parse-only         Test only parsing script (If --int* opt is given with this one, it will end with error)\n";
            echo "      --int-only           Test only interpret script (If --parse* opt is given with this one, it will end with error)\n";
            echo "      --jexamxml=<file>    Name of the JAR file with A7Soft JExamXML. (Default /pub/courses/ipp/jexamxml/jexamxml.jar)\n";
            exit(0);
        }
        else {
            return err_msg("--help cannot take any more arguments.", $wrongParamErr);
        }
    }
    
    /* ############                CHECKING ARGUMENTS              ##############*/

    foreach ($argv as $i => $arg)
    {
        if ($i < 1) continue;   // Skip name of the script
        $option = explode('=',$arg)[0];
        switch ($option){
            case "--directory":
                $testDirGiven = true;
                $testDir = $myArgs["directory"];
                break;
            case "--recursive":
                $recursive = true;
                break;
            case "--parse-script":
                $parseFileGiven = true;
                $parseFile = $myArgs["parse-script"];
                break;
            case "--int-script":
                $intFileGiven = true;
                $intFile = $myArgs["int-script"];
                break;
            case "--parse-only":
                $parseOnly = true;
                break;
            case "--int-only":
                $intOnly = true;
                break;
            case "--jexamxlm":
                $jexamxmlFileGiven = true;
                $jexamxmlFile = $myArgs["jexamxml"];
                break;
            default:
                err_msg("Unknown option", $wrongParamErr);
        }
    }

    if ($intOnly && $parseOnly)
        err_msg("--int-only and --parse-only options can't be together", $wrongParamErr);

    if ($parseOnly && $intFileGiven)
        err_msg("--parse-only and --int-script options can't be together", $wrongParamErr);
    
    if ($intOnly && $parseFileGiven)
        err_msg("--int-only and --parse-script options can't be together", $wrongParamErr);
    

    if ($testDirGiven){
        $testDir = exec("realpath '$testDir'")."/";
        if (!is_dir($testDir))
            err_msg("--directory=<dir> is not a directory", $inputFileErr);
    }
    
    if ($parseFileGiven){
        $parseFile = exec("realpath '$parseFile'")."/";
        if (!is_file($parseFile))
            err_msg("--parse-script=<file> is not a file", $inputFileErr);
    }

    if ($intFileGiven){
        $intFile = exec("realpath '$intFile'")."/";
        if (!is_file($intFile))
            err_msg("--int-script=<file> is not a file", $inputFileErr);
    }

    /* ############               END OF CHECKING ARGUMENTS            ##############*/

    if($recursive){
        $testFiles = rglob($testDir);
    }
    else {
        $testFiles = glob($testDir . "*.src");
    }
    

    /* ############               CREATE MISSING .in/.out/.rc  FILES            ##############*/

    foreach ($testFiles as $testFile) {
        $testsCount++;

        $testName = str_replace(".src", "", $testFile);
    
        if (!file_exists("$testName.in")){
            if (file_put_contents("$testName.in", "") === false)
                err_msg("Couldn't create a file", $outputFileErr);
        }
        if (!file_exists("$testName.rc")){
            if (file_put_contents("$testName.rc", "0") === false)
                err_msg("Couldn't create a file", $outputFileErr);
        }
    
        if (!file_exists("$testName.out")){
            if (file_put_contents("$testName.out", "") === false)
                err_msg("Couldn't create a file", $outputFileErr);
        }
    
    /* ############               END OF CREATING FILES            ##############*/

        if ($parseOnly)
            $resultArray[] = parse_only($testName);
        else if ($intOnly)
            $resultArray[] = int_only("src", $testName);
        else
            $resultArray[] = both($testName);
    }
    
include "html-part.php";
?>