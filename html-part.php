<!DOCTYPE html>
<html>
<head> <title> IPPCode20 </title>
    <meta content="text/html; charset=UTF-8">
    <style>
        body {
            background: white;
            font-family: Helvetica;
        }
        .my-container {
            max-width: 1100px;
            margin-right: auto;
            margin-left: auto;
            flex-basis: auto;

            display: flex;
            flex-wrap: wrap;
        }

        .my-container > * {
            padding: 10px;
        }

        .res-box {
            text-align: center;
            background: #3269a8;
            border-radius: 0px 0px 15px 15px;
            margin-bottom: 20px;
            padding-top: 10px;
            padding-bottom: 10px;
            font-size: 25px;
            font-weight: bold;
        }

        .head-box {
            text-align: center;
            background: #3269a8;
            font-size: 25px;
            margin-bottom: 10px;
            padding: 5px;
        }

        h3 {
            padding: 5px;
            margin-bottom: 0px;
        }

        p {
            margin: 5px;
        }
        .res {
        color: black;
        font-weight: bold;
        font-family: Helvetica;
        }

        .res em {
        color: #ed2b2b;
        font-style: normal;
        }


        .flexed {
            flex-basis: 100%;
        }

        .test {
            text-align: center;
            background: #42a4f5;
            border-radius: 15px 15px 0px 0px;
            font-size: 18px;
            padding-top: 15px;
            padding-bottom: 15px;
        }
        
        .fail {
            background: tomato;
            border: 5px solid red;
        }
        
        .pass {
            background-color: #80e27e;
            border: 5px solid green;
        }

        button {
            border: 0;
            font-weight: bold;
            background-color: #000;
            padding: 15px 20px;
            color: #fff;
            transition: all 0.2s;
        }

        button:hover {
            background-color: #424040;
        }

        textarea {
            background-color: #ba2222;
            border: 2px solid darkred;
            font-size: 16px;
            width: auto;
            height: auto;
            min-width: 70%;
            min-height: 200px;
        }
        
    </style>
</head>
<body>
<div class="my-container" style="max-width: 1500px;">
    <header class="head-box flexed">
    <h3> Results from test.php </h3>
    <p class="res" style="margin-top: 10px;"> Total tests: <?=$testsCount?></p>
    <?php if ($testsFailed > 0): ?>
        <p class="res"> Failed: <em><?= $testsFailed?></em>/<?=$testsCount?></p> 
    <?php else: ?>
        <p class="res"> Failed: <?= $testsFailed?>/<?=$testsCount?></p> 
    <?php endif ?>
    <?php if ($testsCount - $testsFailed > 0): ?>
        <p class="res" style="margin-bottom: 15px;"> Passed: <em style="color: #3dd447;"><?= $testsCount - $testsFailed?></em>/<?=$testsCount?></p>
    <?php else: ?>
        <p class="res" style="margin-bottom: 15px;"> Passed: <?= $testsCount - $testsFailed?>/<?=$testsCount?></p> 
    <?php endif ?>
    </header>
</div>
<div class="my-container">

    <?php
    foreach ($resultArray as $result):
    ?>

    <article class="test flexed"><?=$result["testName"]?></article>
    <article class="res-box flexed <?=($result["passed"]) ? "pass" : "fail"?>">
        <p> RESULT: <?=($result["passed"]) ? "PASSED" : "FAILED"?></p>

        <?php
        if (isset($result["diff"])):
        ?>
            <button onclick="showDiff(event)">Show diff</button>
            <div style="display: none;">
                <textarea readonly><?=$result["diff"]?></textarea>
            </div>
        <?php
        elseif($result["passed"] === false):
        ?>
            <p style="font-size: 16px;"><?="Error: ".$result["errMsg"]?></p>

        <?php
        endif;
        ?>
    </article>
    <?php
    endforeach;
    ?>

</div>

<script>
    function showDiff(event) {
        var tmp = event.target.nextElementSibling;
        if (tmp.style.display === "none") {
            tmp.style.display = "block";
        } else {
            tmp.style.display = "none";
        }
    }
</script>
</body>
</html>


