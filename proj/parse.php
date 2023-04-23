<?php
ini_set('display_errors', 'stderr');

#checks correctness of the given variable
#if the variable doesn't meet requirements returns code 23
function var_check($nonterminal, $argc) 
{
    if(preg_match("/^(LF|GF|TF)@[a-zA-Z_\-$&%*!?][a-zA-Z_\-$&%*!?0-9]*$/", $nonterminal))
    {
        $nonterminal = str_replace("&", "&amp;", $nonterminal);
        $nonterminal = str_replace("<", "&lt;", $nonterminal);
        $nonterminal = str_replace(">", "&gt;", $nonterminal);       
        echo("\t\t<arg$argc type=\"var\">$nonterminal</arg$argc>\n");
        return;
    }
    else
    {
        exit(23); 
    }
}

#checks correctness of the given label
#if the variable doesn't meet requirements returns code 23
function label_check($nonterminal, $argc)
{
    if(preg_match("/^[a-zA-Z_\-$&%*!?][a-zA-Z_\-$&%*!?0-9]*$/", $nonterminal))
    {
        echo("\t\t<arg$argc type=\"label\">$nonterminal</arg$argc>\n");
        return;
    }
    else
    {
        exit(23); 
    }
}

#checks correctness of the given symbol
#if the variable doesn't meet requirements returns code 23
function symb_check($nonterminal, $argc)
{
    if(preg_match("/^int@[\-+]?[0-9]+$/", $nonterminal)) #symbol is constant (int)
    {
        $const = substr($nonterminal, 4);
        echo("\t\t<arg$argc type=\"int\">$const</arg$argc>\n");
        return;
    }
    elseif(preg_match("/^bool@(true|false)$/", $nonterminal)) #symbol is constant (bool)
    {
        $const = trim($nonterminal, "bool@");
        echo("\t\t<arg$argc type=\"bool\">$const</arg$argc>\n");
        return;
    }
    elseif(preg_match("/^string@([^\\\\]*(\\\\[0-9]{3})*)*$/", $nonterminal)) #symbol is constant (string)
    {
        $nonterminal = str_replace("&", "&amp;", $nonterminal);
        $nonterminal = str_replace("<", "&lt;", $nonterminal);
        $nonterminal = str_replace(">", "&gt;", $nonterminal);
        $const = substr($nonterminal, 7);
        echo("\t\t<arg$argc type=\"string\">$const</arg$argc>\n");
        return;
    }
    elseif(preg_match("/^nil@nil$/", $nonterminal)) #symbol is constant (nil)
    {
        echo("\t\t<arg$argc type=\"nil\">nil</arg$argc>\n");
        return;
    }
    else #symbol is either variable or invalid
    {
        var_check($nonterminal, $argc);
    }
}

#checks correctness of the given type
#if the variable doesn't meet requirements returns code 23
function type_check ($nonterminal, $argc)
{
    if($nonterminal === "int")
    {
        echo("\t\t<arg$argc type=\"type\">int</arg$argc>\n");
        return;
    }
    elseif($nonterminal === "string")
    {
        echo("\t\t<arg$argc type=\"type\">string</arg$argc>\n");
        return;
    }
    elseif($nonterminal === "bool")
    {
        echo("\t\t<arg$argc type=\"type\">bool</arg$argc>\n");
        return;
    }
    else{
        exit(23); #invalid type
    }
}

if ($argc > 1){
    if ($argv[1] == "--help"){
        if($argc > 2){
            exit(10);
        }
        echo("Skript typu filter (parse.php v jazyku PHP 7.4) nacita zo standardneho vstupu zdrojovy kod v IPPcode21,\n");
        echo("skontroluje lexikalnu a syntakticku spravnost kodu a vypise na standardny vystup XML reprezentaciu programu\n");
        echo("\nChybove navratove kody:\n");
        echo("21 - chybna/chybajuca hlavicka v zdrojovom kode zapisanom v IPPcode21\n");
        echo("22 - neznamy/chybny operacny kod v zdrojovom kode zapisanom v IPPcode21\n");
        echo("23 - ina lexikalna/syntakticka chyba zdrojoveho kodu zapisaneho v IPPcode21\n");
        exit(0);
    }
    exit(10);
}

echo("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"); #obligatory header

$header = strtoupper($line = fgets(STDIN));
$header= preg_replace("/( #|#).*/", "", $header);
while(ctype_space($header))
{
    $header = strtoupper($line = fgets(STDIN));
    $header= preg_replace("/( #|#).*/", "", $header);
}
$header = trim($header, "\n");
$header = preg_replace('/\s+/', ' ', $header);
$header = trim($header, " \t\n");
if($header !== ".IPPCODE21"){
    exit(21); #missing header
}
echo("<program language=\"IPPcode21\">\n");

$instcount = 0;

while ($line = fgets(STDIN))
{
    $line = preg_replace("/( #|#).*/", "", $line);
    $line = preg_replace('/\s+/', ' ', $line);
    $separated = explode(" ", trim($line, " \t\n"));
    $wcount = count($separated);
    $opcode = strtoupper($separated[0]);
    
    switch(strtoupper($separated[0]))
    {
        case 'PUSHFRAME':
        case 'CREATEFRAME':
        case 'POPFRAME':
        case 'RETURN':
        case 'BREAK':
        {
            $instcount++;
            if ($wcount > 1)
            {
                exit(23);
            }
            echo("\t<instruction order=\"$instcount\" opcode=\"$opcode\"/>\n");
            break;
        }
        case 'DEFVAR':
        case 'POPS':
        {
            $instcount++;
            if ($wcount !== 2)
            {
                exit(23);
            }
            echo("\t<instruction order=\"$instcount\" opcode=\"$opcode\">\n");
            var_check($separated[1], 1);
            echo("\t</instruction>\n");
            break;
        }
        case 'LABEL':
        case 'JUMP':
        case 'CALL':
        {
            $instcount++;
            if ($wcount !== 2)
            {
                exit(23);
            }
            echo("\t<instruction order=\"$instcount\" opcode=\"$opcode\">\n");
            label_check($separated[1], 1);
            echo("\t</instruction>\n");
            break;
        }        
        case 'PUSHS':
        case 'WRITE':
        case 'EXIT':
        case 'DPRINT':
        {
            $instcount++;
            if ($wcount !== 2)
            {
                exit(23);
            }
            echo("\t<instruction order=\"$instcount\" opcode=\"$opcode\">\n");
            symb_check($separated[1], 1); 
            echo("\t</instruction>\n");
            break;
        }
        case 'MOVE':
        case 'INT2CHAR':
        case 'STRLEN':
        case 'TYPE':
        {
            $instcount++;
            if ($wcount !== 3)
            {
                exit(23);
            }
            echo("\t<instruction order=\"$instcount\" opcode=\"$opcode\">\n");
            var_check($separated[1], 1);
            symb_check($separated[2], 2); 
            echo("\t</instruction>\n");
            break;   
        }
        case 'NOT':
        {
            $instcount++;
            if ($wcount !== 3)
            {
                exit(23);
            }
            echo("\t<instruction order=\"$instcount\" opcode=\"$opcode\">\n");
            var_check($separated[1], 1);
            symb_check($separated[2], 2); 
            echo("\t</instruction>\n");
            break;   
        }
        case 'ADD':
        case 'SUB':
        case 'MUL':
        case 'IDIV':
        case 'LT':
        case 'GT':
        case 'EQ':
        case 'AND':
        case 'OR':
        case 'STRI2INT':
        case 'CONCAT':
        case 'GETCHAR':
        case 'SETCHAR':
        {
            $instcount++;
            if ($wcount !== 4)
            {
                exit(23);
            }
            echo("\t<instruction order=\"$instcount\" opcode=\"$opcode\">\n");
            var_check($separated[1], 1);
            symb_check($separated[2], 2);
            symb_check($separated[3], 3); 
            echo("\t</instruction>\n");
            break;   
        }
        case 'JUMPIFEQ':
        case 'JUMPIFNEQ':
        {
            $instcount++;
            if ($wcount !== 4)
            {
                exit(23);
            }
            echo("\t<instruction order=\"$instcount\" opcode=\"$opcode\">\n");
            label_check($separated[1], 1);
            symb_check($separated[2], 2);
            symb_check($separated[3], 3); 
            echo("\t</instruction>\n");
            break;   
        }
        case 'READ':
        {
            $instcount++;
            if ($wcount !== 3)
            {
                exit(23);
            }
            echo("\t<instruction order=\"$instcount\" opcode=\"$opcode\">\n");
            var_check($separated[1], 1);
            type_check($separated[2], 2);
            echo("\t</instruction>\n");
            break;  
        }
        default:
        {
            if($separated[0] !== "")
            {
                exit(22);
            }
        }
    }
}
echo("</program>\n");
exit(0);
?>