# ----------------------------
# Autor: Zuzana Hrkľová, xhrklo00
# Datum: 12.4.2022
# Popis: Interpreter pre IPPcode22
# ----------------------------

import argparse
import sys
import xml.etree.ElementTree as ET
import re 

# definicia konstant
attrib_type = ["int", "bool", "string", "nil", "label", "type", "var"]
instruction_list = ["MOVE", 
                    "CREATEFRAME", 
                    "PUSHFRAME", 
                    "POPFRAME", 
                    "DEFVAR", 
                    "CALL", 
                    "RETURN", 
                    "PUSHS", 
                    "POPS", 
                    "ADD", 
                    "SUB", 
                    "MUL", 
                    "IDIV", 
                    "LT", 
                    "GT", 
                    "EQ", 
                    "AND", 
                    "OR", 
                    "NOT", 
                    "INT2CHAR", 
                    "STRI2INT", 
                    "READ", 
                    "WRITE", 
                    "CONCAT", 
                    "STRLEN", 
                    "GETCHAR", 
                    "SETCHAR", 
                    "TYPE", 
                    "LABEL", 
                    "JUMP", 
                    "JUMPIFEQ", 
                    "JUMPIFNEQ", 
                    "EXIT", 
                    "DPRINT", 
                    "BREAK"]
inst_order = []
instruction_dict = {}
frames = {}
frames["GF"]={}
# LF stack
frames["LF"] = []
datastack = []
callings_stack = []
labels = {}

# funkcia skontroluje a rozparsuje argumenty zo vstupu
def arg_parse():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--help", action="store_true", default=False)
    parser.add_argument("--source", dest="sourcefile")
    parser.add_argument("--input", dest="inputfile")

    try:
        args, unknown = parser.parse_known_args()
    except:
        sys.exit(10)
    if unknown:
        #nedefinovany argument na vstupe
        sys.exit(10)
    if args.help:
        # program spustany s parametrom --help
        if len(sys.argv) == 2:
            print("Skript nacita XML reprezentaciu programu IPPcode22 a prevedie jeho interpretaciu")
            print("    --source    | Vstupny subor s XML reprezentaciou zdrojoveho kodu IPPcode22")
            print("    --input     | Subor so vstupmi pre interpretaciu")
            sys.exit(0)
        else:
            exit(10)   
    if not(args.sourcefile) and not(args.inputfile):
        # program spusteny bez aspon jedneho suboru (nie je zadany ani --source ani --input)
        sys.exit(10)

    # ziskavanie obsahu zo vstupnych suborov
    inputfile = "" 
    if args.sourcefile:
        try:
            srcfile = open(args.sourcefile, "r")
        except:
            sys.exit(11)
    else:
        srcfile = sys.stdin
    if args.inputfile:
        try:
            inputfile = open(args.inputfile, "r")
        except:
            sys.exit(11)
    return(srcfile, inputfile)

# funkcia vytvori z xml vstupu stromovu strukturu a ulozi jej obsah do slovnika
def build_and_save_xmltree(srcfile):        
    # tvorenie stromu
    try:
        tree = ET.parse(srcfile)
        root = tree.getroot()
    except:
        # srcfile nie je dobre formatovany
        print("not well-formed")
        sys.exit(31)
            
    # kontrola korenoveho elementu
    if root.tag != "program":
        sys.exit(32)
    if len(root.attrib) < 1 or len(root.attrib) > 3:
        sys.exit(32)
    try:
        language = root.attrib["language"]
    except:
        sys.exit(32)
    if len(root.attrib) == 3:
        if "name" not in root.attrib or "description" not in root.attrib:
            sys.exit(32)
    if len(root.attrib) == 2:
        if "name" not in root.attrib and "description" not in root.attrib:
            sys.exit(32)
    if language.upper() != "IPPCODE22":
        sys.exit(32)    
    # kontrola ci vsetci priamy potomkovia elementu program su elementy instruction
    for child in root:
        if child.tag != "instruction":
            sys.exit(32)
    #kontrola elementu instruction 
    for instruction in root.iter('instruction'):
        if len(instruction.attrib) != 2:
            sys.exit(32)
        try:
            # kontrola ci element obsahuje atributy order a opcode
            order = instruction.attrib["order"]
            opcode = instruction.attrib["opcode"]
        except:
            sys.exit(32)
        # kontrola hodnoty atributu opcode
        if opcode.upper() not in instruction_list:
            sys.exit(32)
        # kontrola hodnoty atributu order
        try:
            int(order)
        except:
            sys.exit(32)
        if int(order) > 0 and int(order) not in inst_order:
            inst_order.append(int(order))
        else:
            # cislo v order je negativne alebo sa v programe nachadza viac ako raz
            sys.exit(32)
        # ukladanie instrukcie do slovnika spolu s jej atributmi
        instruction_dict["inst" + order] = {"order": int(order), "opcode": opcode.upper()}
        for arg in instruction:
            #kontrola ci elementy vo vnutri elementov instruction su arg elem.
            if re.match('^arg[123]$', arg.tag) == None:
                sys.exit(32)
            # kontrola arg atributov
            if len(arg.attrib) != 1:
                #print("wrong attrib number")
                sys.exit(32)
            try:
                type = arg.attrib["type"]
            except:
                sys.exit(32)
            #kontrola hodnoty v atribute type
            if type not in attrib_type:
                sys.exit(32)
            value = arg.text
            if value == None and type == "string":
                value = ""
            #zapis ziskanych dat do slovnika
            instruction_dict["inst" + order][arg.tag] = {"type": type, "value": value}

#funkcia skontroluje meno a ramec premennej a vrati slovnik s oddelenym menom premennej a typom ramca
def var_parse(var):
    variable = {}
    if var[:3] == "GF@":
        variable["frame"] = "GF"
    elif var[:3] == "LF@":
        variable["frame"] = "LF"
    elif var[:3] == "TF@":
        variable["frame"] = "TF"
    else:
        sys.exit(32)
    # kontrola mena premennej
    if re.match('^(LF|GF|TF)@[a-zA-Z_\-$&%*!?][a-zA-Z_\-$&%*!?0-9]*$', var):
        variable["name"] = var[3:]
    else:
        sys.exit(32)
    return(variable)

# kontrola ci hodnota typu argumentu je var
def var_type_check(type):
    if type != "var":
        sys.exit(53)
    return(True)
# funkcia skontroluje ci existuje dany ramec a ci je dana premenna definovana v zadanom ramci 
def var_check(var):
    if var["frame"] == "GF":
        if var["name"] not in frames["GF"]:
            # premenna nie je v danom ramci definovana
            sys.exit(54)
    elif var["frame"] == "LF":
        if len(frames["LF"]) < 1:
            # LF neexistuje
            sys.exit(55)
        if var["name"] not in frames["LF"][-1]:
            # premenna nie je v danom ramci definovana
            sys.exit(54)
    else:
        if "TF" not in frames:
            # Tf neexistuje
            sys.exit(55)
        if var["name"] not in frames["TF"]:
            # premenna nie je v danom ramci definovana
            sys.exit(54)
    return(True)
# ulozi do ramca (priradi) hodnotu premennej
def var_save(variable, type, value):
    if variable["frame"] == "LF":
        frames["LF"][-1][variable["name"]]["type"] = type
        frames["LF"][-1][variable["name"]]["value"] = value
    else:
        frames[variable["frame"]][variable["name"]]["type"] = type
        frames[variable["frame"]][variable["name"]]["value"] = value
        
# funkcia vezme symbol a vrati typ a hodnotu
def get_symbv_and_symbt(symb):
    if "frame" in symb:
        if symb["frame"] not in frames:
            # ramec nie je definovany
            sys.exit(55)
        try:
            if symb["frame"] == "LF":
                symb_t = frames["LF"][-1][symb["name"]]["type"]
                symb_v = frames["LF"][-1][symb["name"]]["value"]
            else:
                symb_t = frames[symb["frame"]][symb["name"]]["type"]
                symb_v = frames[symb["frame"]][symb["name"]]["value"]
        except:
            #vhodnota/typ nie su definovane
            sys.exit(56)
    else:
        symb_t = symb["type"]
        symb_v = symb["value"]
    return(symb_t, symb_v)

#kontrola symbolu vrati slovnik s hodnotou konstanty a jej typom alebo menom premennej a ramcom v ktorom sa nachadza
def symbol_check(symb):
    if symb["type"] == "int":
        if re.match('^([\-+]?[0-9]+|0[xX][0-9a-fA-F]+|0[oO]?[0-7]+)$', symb["value"]):
            if "X" in symb["value"] or "x" in symb["value"]:
                symb["value"] = int(symb["value"], 0)
            elif "O" in symb["value"] or "o" in symb["value"]:
                symb["value"] = int(symb["value"], 0)
            return (symb)
        # hodnota je ineho typu ako je  nadefinovane v xml
        sys.exit(32)
    elif symb["type"] == "string":
        if "\\" in symb["value"]:
            tmp = symb["value"].split("\\")
            cnt = 1
            result = [tmp[0]]
            while cnt < len(tmp):
                result.append(str(chr(int(tmp[cnt][:3]))))
                result.append(tmp[cnt][3:])
                cnt += 1
            symb["value"] = "".join(result)
        return(symb)
    elif symb["type"] == "bool":
        if re.match('^(true|false)$', symb["value"]):
            return(symb)
        # hodnota je ineho typu ako je  nadefinovane v xml
        sys.exit(32)
    elif symb["type"] == "nil":
        if symb["value"] == "nil":
            return(symb)
        # hodnota je ineho typu ako je  nadefinovane v xml
        sys.exit(32)
    elif symb["type"] == "var":
        symbol = var_parse(symb["value"])
        var_check(symbol)
        return(symbol)
    else:
        sys.exit(53)

#kontrola typu a mena label(nazvu navestia)
def label_check(label):
    if label["type"] != "label":
        sys.exit(53)
    if re.match('[a-zA-Z_\-$&%*!?][a-zA-Z_\-$&%*!?0-9]*$', label["value"]):
        return(True)
    else:
        sys.exit(32)

# instrukcie
def move(var, symb):
    var_type_check(var["type"])
    variable = var_parse(var["value"])
    symbol = symbol_check(symb)
    var_check(variable)
    if "frame" in symbol:
        # symbol je premenna nie konstanta
        var_check(symbol)
        get_symbv_and_symbt(symbol)
        if variable["frame"] == "LF":
            if symbol["frame"] == "LF":
                frames["LF"][-1][variable["name"]] = frames["LF"][-1][symbol["name"]]
            else:
                frames["LF"][-1][variable["name"]] = frames[symbol["frame"]][symbol["name"]] 
        else:
            if symbol["frame"] == "LF":
                frames[variable["frame"]][variable["name"]] = frames["LF"][-1][symbol["name"]]
            else:
                frames[variable["frame"]][variable["name"]] = frames[symbol["frame"]][symbol["name"]]
    else:
        # symbol je konstanta
        if variable["frame"] == "LF":
            frames["LF"][-1][variable["name"]] = {"type": symbol["type"], "value": symbol["value"]}
        else:
            frames[variable["frame"]][variable["name"]] = {"type": symbol["type"], "value": symbol["value"]}
def createframe():
    frames["TF"] = {}
def pushframe():
    try:
        frames["LF"].append(frames["TF"])
    except:
        #TF nie je definovany
        sys.exit(55)
    frames.pop("TF")
def popframe():
    try:
        tmp = frames["LF"].pop()
    except:
        # LF nie je definovany
        sys.exit(55)
    frames["TF"] = tmp    
def defvar(var):
    var_type_check(var["type"])
    variable = var_parse(var["value"])
    if variable["frame"] == "GF":
        if variable["name"] in frames["GF"]:
            # premenna v danom ramci uz existuje
            sys.exit(52)
        frames["GF"][variable["name"]] = {}
    elif variable["frame"] == "LF":
        if len(frames["LF"]) < 1:
            #LF nie je definovany
            sys.exit(55)
        if variable["name"] in frames["LF"][-1]:
             # premenna v danom ramci uz existuje
            sys.exit(52)
        frames["LF"][-1][variable["name"]] = {}
    else:
        if "TF" in frames:
            if variable["name"] in frames["TF"]:
                # premenna v danom ramci uz existuje
                sys.exit(52)
            frames["TF"][variable["name"]] = {}
        else:
            #TF nie je definovany
            sys.exit(55)



def call(label, position):
    label_check(label)
    if label["value"] not in labels:
        # nazov navestia nie je definovany
        sys.exit(52)
    callings_stack.append(position)
    return(labels[label["value"]]["order"])

def return_inst():
    try:
        result = callings_stack.pop()
    except:
        # callings_stack je prazdny
        sys.exit(56)
    return(result)

def pushs(symb):
    symbol = symbol_check(symb)
    datastack.append({})
    if "frame" not in symbol:
        datastack[-1]["value"] = symbol["value"]
        datastack[-1]["type"] = symbol["type"]
    else:
        var_check(symbol)
        if "LF" == symbol["frame"]:
            try:
                datastack[-1]["value"] = frames["LF"][-1][symbol["name"]]["value"]
                datastack[-1]["type"] = frames["LF"][-1][symbol["name"]]["type"]
            except:
                # hodnota premennej  nie je definovana
                sys.exit(56)
        else:
            try:
                datastack[-1]["value"] = frames[symbol["frame"]][symbol["name"]]["value"]
                datastack[-1]["type"] = frames[symbol["frame"]][symbol["name"]]["type"]
            except:
                # hodnota premennej  nie je definovana
                sys.exit(56)
def pops(var):
    var_type_check(var["type"])
    variable = var_parse(var["value"])
    var_check(variable)
    if len(datastack) < 1 :
        # zasobnik je prazdny
        sys.exit(56)
    if variable["frame"] == "LF":
        frames["LF"][-1][variable["name"]]["value"] = datastack[-1]["value"]
        frames["LF"][-1][variable["name"]]["type"] = datastack[-1]["type"]
    else:
        frames[variable["frame"]][variable["name"]]["value"] = datastack[-1]["value"]
        frames[variable["frame"]][variable["name"]]["type"] = datastack[-1]["type"]
    datastack.pop()

def add(var, symb1, symb2):
    var_type_check(var["type"])
    variable = var_parse(var["value"])
    var_check(variable)
    symbol1 = symbol_check(symb1)
    symbol2 = symbol_check(symb2)
    symb1_t, symb1_v = get_symbv_and_symbt(symbol1)
    symb2_t, symb2_v = get_symbv_and_symbt(symbol2)
    if symb1_t != "int" or symb2_t != "int":
        #vstupne symboly zleho typu
        sys.exit(53)
    result = int(symb1_v) + int(symb2_v)
    var_save(variable, "int", result)
def sub(var, symb1, symb2):
    var_type_check(var["type"])
    variable = var_parse(var["value"])
    var_check(variable)
    symbol1 = symbol_check(symb1)
    symbol2 = symbol_check(symb2)
    symb1_t, symb1_v = get_symbv_and_symbt(symbol1)
    symb2_t, symb2_v = get_symbv_and_symbt(symbol2)
    if symb1_t != "int" or symb2_t != "int":
        #vstupne symboly zleho typu
        sys.exit(53)
    result = int(symb1_v) - int(symb2_v)
    var_save(variable, "int", result)
def mul(var, symb1, symb2):
    var_type_check(var["type"])
    variable = var_parse(var["value"])
    var_check(variable)
    symbol1 = symbol_check(symb1)
    symbol2 = symbol_check(symb2)
    symb1_t, symb1_v = get_symbv_and_symbt(symbol1)
    symb2_t, symb2_v = get_symbv_and_symbt(symbol2)
    if symb1_t != "int" or symb2_t != "int":
        #vstupne symboly zleho typu
        sys.exit(53)
    result = int(symb1_v) * int(symb2_v)
    var_save(variable, "int", result)
def idiv(var, symb1, symb2):
    var_type_check(var["type"])
    variable = var_parse(var["value"])
    var_check(variable)
    symbol1 = symbol_check(symb1)
    symbol2 = symbol_check(symb2)
    symb1_t, symb1_v = get_symbv_and_symbt(symbol1)
    symb2_t, symb2_v = get_symbv_and_symbt(symbol2)
    if symb1_t != "int" or symb2_t != "int":
        #vstupne symboly zleho typu
        sys.exit(53)
    if int(symb2_v) == 0:
        # delenie 0
        sys.exit(57)
    result = int(symb1_v) // int(symb2_v)
    var_save(variable, "int", result)
def lt(var, symb1, symb2):
    var_type_check(var["type"])
    variable = var_parse(var["value"])
    var_check(variable)
    symbol1 = symbol_check(symb1)
    symbol2 = symbol_check(symb2)
    symb1_t, symb1_v = get_symbv_and_symbt(symbol1)
    symb2_t, symb2_v = get_symbv_and_symbt(symbol2)
    if symb1_t != symb2_t:
        #vstupne symboly zleho typu
        sys.exit(53)
    if symb1_t == "nil":
        # symbol je typu nil
        sys.exit(53)
    if symb1_t == "int":
        tmp = int(symb1_v) < int(symb2_v)
    else:
        tmp = symb1_v < symb2_v
    if tmp == True:
        result = "true"
    else:
        result = "false"
    var_save(variable, "bool", result)
def gt(var, symb1, symb2):
    lt(var, symb2, symb1)
def eq(var, symb1, symb2):
    var_type_check(var["type"])
    variable = var_parse(var["value"])
    var_check(variable)
    symbol1 = symbol_check(symb1)
    symbol2 = symbol_check(symb2)
    symb1_t, symb1_v = get_symbv_and_symbt(symbol1)
    symb2_t, symb2_v = get_symbv_and_symbt(symbol2)
    if symb1_t != symb2_t:
        if symb1_t != "nil" and symb2_t != "nil":
            #vstupne symboly zleho typu
            sys.exit(53)
    result = "false"
    if symb1_t == "int" and symb2_t == "int":
        if int(symb1_v) == int(symb2_v):
            result = "true"
    else:
         if symb1_v == symb2_v:
             result = "true"   
    var_save(variable, "bool", result)
def and_inst(var, symb1, symb2):
    var_type_check(var["type"])
    variable = var_parse(var["value"])
    var_check(variable)
    symbol1 = symbol_check(symb1)
    symbol2 = symbol_check(symb2)
    symb1_t, symb1_v = get_symbv_and_symbt(symbol1)
    symb2_t, symb2_v = get_symbv_and_symbt(symbol2)
    if symb1_t != "bool" or symb2_t != "bool":
        #vstupne symboly zleho typu
        sys.exit(53)
    result = "false"
    if symb1_v == "true" and symb2_v == "true":
        result = "true"
    var_save(variable, "bool", result)
def or_inst(var, symb1, symb2):
    var_type_check(var["type"])
    variable = var_parse(var["value"])
    var_check(variable)
    symbol1 = symbol_check(symb1)
    symbol2 = symbol_check(symb2)
    symb1_t, symb1_v = get_symbv_and_symbt(symbol1)
    symb2_t, symb2_v = get_symbv_and_symbt(symbol2)
    if symb1_t != "bool" or symb2_t != "bool":
        #vstupne symboly zleho typu
        sys.exit(53)
    result = "true"
    if symb1_v == "false" and symb2_v == "false":
        result = "false"
    var_save(variable, "bool", result)
def not_inst(var, symb):
    var_type_check(var["type"])
    variable = var_parse(var["value"])
    var_check(variable)
    symbol = symbol_check(symb)
    symb_t, symb_v = get_symbv_and_symbt(symbol)
    if symb_t != "bool":
        #vstupny symbol zleho typu
        sys.exit(53)
    result = "false"
    if symb_v == "false":
        result = "true"
    var_save(variable, "bool", result)       
def int2char(var, symb):
    var_type_check(var["type"])
    variable = var_parse(var["value"])
    var_check(variable)
    symbol = symbol_check(symb)
    symb_t, symb_v = get_symbv_and_symbt(symbol)
    if symb_t != "int":
        #vstupny symbol zleho typu
        sys.exit(53)
    try:
        tmp = chr(int(symb_v))
    except:
        #honota symbolu nie je validna
        sys.exit(58)
    var_save(variable, "string", tmp)
def stri2int(var, symb1, symb2):
    var_type_check(var["type"])
    variable = var_parse(var["value"])
    var_check(variable)
    symbol1 = symbol_check(symb1)
    symbol2 = symbol_check(symb2)
    symb1_t, symb1_v = get_symbv_and_symbt(symbol1)
    symb2_t, symb2_v = get_symbv_and_symbt(symbol2)
    if symb1_t != "string" or symb2_t != "int":
        #vstupne symboly zleho typu
        sys.exit(53)
    if int(symb2_v) < 0:
        sys.exit(58)
    try:
        char = symb1_v[int(symb2_v)]
    except:
        # indexovanie mimo rozsahu
        sys.exit(58)
    var_save(variable, "int", ord(char))

def read(var, type, inputfile):
    var_type_check(var["type"])
    variable = var_parse(var["value"])
    var_check(variable)
    if type["type"] != "type":
        # zly typ vstupu
        sys.exit(53)
    if type["value"] != "string" and type["value"] != "int" and type["value"] != "bool":
        # yla hodnota vstupu
        sys.exit(53)
    if inputfile == "":
        #na vstupe nebol zadany subor
        input_text = input()
    else:
        input_text = inputfile.readline()
    if len(input_text) > 1 and input_text[-1] == "\n":
        input_text = input_text[:-1]
    
    if re.match('^\s+$', input_text):
        var_save(variable, "nil", "nil")
        return(True)
    if input_text == "":
        var_save(variable, "nil", "nil")
        return(True)
    if type["value"] == "string":
        var_save(variable, "string", input_text)
    elif type["value"] == "bool":
        #print(input_text)
        if input_text.upper() == "TRUE":
            var_save(variable, "bool", "true")
        else:
            var_save(variable, "bool", "false")
    else:
        try:
            var_save(variable, "int", int(input_text))
        except:
            var_save(variable, "nil", "nil")
    
def write(symb):
    symbol = symbol_check(symb)
    symb_t, symb_v = get_symbv_and_symbt(symbol)
    if symb_t == "nil":
        print("", end='')
    else:
        print(symb_v, end='')
        
def concat(var, symb1, symb2):
    var_type_check(var["type"])
    variable = var_parse(var["value"])
    var_check(variable)
    symbol1 = symbol_check(symb1)
    symbol2 = symbol_check(symb2)
    symb1_t, symb1_v = get_symbv_and_symbt(symbol1)
    symb2_t, symb2_v = get_symbv_and_symbt(symbol2)
    if symb1_t == "string" and symb2_t == "string":
        result = symb1_v + symb2_v
        var_save(variable, "string", result)
    else:
        #symbol nie je string
        sys.exit(53)
          
def strlen(var, symb):
    var_type_check(var["type"])
    variable = var_parse(var["value"])
    var_check(variable)
    symbol = symbol_check(symb)
    symb_t, symb_v = get_symbv_and_symbt(symbol)
    if symb_t != "string":
        #symbol nie je string
        sys.exit(53)
    result = len(symb_v)
    var_save(variable, "int", result)
def getchar(var, symb1, symb2):
    var_type_check(var["type"])
    variable = var_parse(var["value"])
    var_check(variable)
    symbol1 = symbol_check(symb1)
    symbol2 = symbol_check(symb2)
    symb1_t, symb1_v = get_symbv_and_symbt(symbol1)
    symb2_t, symb2_v = get_symbv_and_symbt(symbol2)
    if symb1_t != "string" or symb2_t != "int":
        #vstupne symboly zleho typu
        sys.exit(53)
    if int(symb2_v) < 0:
        sys.exit(58)
    try:
        result = symb1_v[int(symb2_v)]
    except:
        #indexovanie mimo rozsahu
        sys.exit(58)
    var_save(variable, "string", result)
def setchar(var, symb1, symb2):
    var_type_check(var["type"])
    variable = var_parse(var["value"])
    var_check(variable)
    symbol1 = symbol_check(symb1)
    symbol2 = symbol_check(symb2)
    symb1_t, symb1_v = get_symbv_and_symbt(symbol1)
    symb2_t, symb2_v = get_symbv_and_symbt(symbol2)
    if variable["frame"] == "LF":
        try:
            var_t = frames["LF"][-1][variable["name"]]["type"]
            var_v = frames["LF"][-1][variable["name"]]["value"]
        except:
            sys.exit(56)
    else:
        try:
            var_t = frames[variable["frame"]][variable["name"]]["type"]
            var_v = frames[variable["frame"]][variable["name"]]["value"]
        except:
            sys.exit(56)
    if var_t != "string" or symb1_t != "int" or symb2_t != "string":
        sys.exit(53)
    if symb2_v == "":
        # symb2 je prazdny retazec
        sys.exit(58)
    if int(symb1_v) < 0:
        sys.exit(58)
    if int(symb1_v) > len(var_v) - 1:
        sys.exit(58)
    try:
        x = var_v[:int(symb1_v)]
        y  = var_v[int(symb1_v) + 1:]
        result = x + symb2_v[0] + y
    except:
        # zle indexovanie
        sys.exit(58)
    var_save(variable, "string", result)
def type_inst(var, symb):
    var_type_check(var["type"])
    variable = var_parse(var["value"])
    var_check(variable)
    symbol = symbol_check(symb)
    # symb is var
    if "frame" in symbol:
        var_check(symbol)
        result = ""
        # symb je premenna v LF
        if symbol["frame"] == "LF":
            # is defined
            if "type" in frames["LF"][-1][symbol["name"]]:
                result = frames["LF"][-1][symbol["name"]]["type"]
        # symb je premenna v GF/TF
        else:
            if "type" in frames[symbol["frame"]][symbol["name"]]:
                result = frames[symbol["frame"]][symbol["name"]]["type"]
    # symb is const
    else:
        result = symbol["type"]
    var_save(variable, "string", result)
def label(label, order):
    label_check(label)
    if label["value"] in labels:
        # nazov navestia (label) je uz definovany
        sys.exit(52)
    labels[label["value"]] ={"order": order}
    
def jump(label):
    label_check(label)
    if label["value"] not in labels:
        # nazov navestia nie je definovany
        sys.exit(52)
    result = labels[label["value"]]["order"]
    return(result)
    
def jumpifeq(label, symb1, symb2, position):
    label_check(label)
    symbol1 = symbol_check(symb1)
    symbol2 = symbol_check(symb2)
    symb1_t, symb1_v = get_symbv_and_symbt(symbol1)
    symb2_t, symb2_v = get_symbv_and_symbt(symbol2)
    if label["value"] not in labels:
        #nazov navestia nie je definovany
        sys.exit(52)
    if symb1_t != symb2_t and symb1_t != "nil" and symb2_t != "nil":
        #vstupne symboly zleho typu
        sys.exit(53)
    if symb1_t == symb2_t:
        if symb1_t == "int":
            if int(symb1_v) == int(symb2_v):
                return(labels[label["value"]]["order"])
        if symb1_v == symb2_v:
            return(labels[label["value"]]["order"])
    return(position)
def jumpifneq(label, symb1, symb2, position):
    label_check(label)
    symbol1 = symbol_check(symb1)
    symbol2 = symbol_check(symb2)
    symb1_t, symb1_v = get_symbv_and_symbt(symbol1)
    symb2_t, symb2_v = get_symbv_and_symbt(symbol2)
    if label["value"] not in labels:
        # nazov navestia nie je definovany
        sys.exit(52)
    if symb1_t != symb2_t and symb1_t != "nil" and symb2_t != "nil":
        #vstupne symboly zleho typu
        sys.exit(53)
    if symb1_t == symb2_t:
        if symb1_t == "int":
            if int(symb1_v) == int(symb2_v):
                return(position)
        if symb1_v == symb2_v:
            return(position)
    return(labels[label["value"]]["order"])
def exit_inst(symb):
    symbol = symbol_check(symb)
    symb_t, symb_v = get_symbv_and_symbt(symbol)
    if symb_t != "int":
        #vstupny symbol zleho typu
        sys.exit(53)
    if int(symb_v) >= 0 and int(symb_v) < 50:
        sys.exit(int(symb_v))
    #zla vstupna hodnota
    sys.exit(57)
    
def dprint(symb):
    symbol = symbol_check(symb)
    if "frame" in symbol:
        var_check(symbol)
        
def break_inst():
    pass

#skontroluje ci pre danu instrukciu je spravne cislo argumentov + skontroluje nazvy elementov arg
def arg_cnt_check(instruction, number, cnt):
    if len(instruction) - 2 != number:
        # zly pocet argumentov ku danej instrukcii
        sys.exit(32)
    if number == 1:
        if "arg1" not in instruction_dict["inst"+ str(inst_order[cnt])]:
            sys.exit(32)
    if number > 1:
        if "arg2" not in instruction_dict["inst"+ str(inst_order[cnt])]:
            sys.exit(32)
    if number == 3:
        if "arg3" not in instruction_dict["inst"+ str(inst_order[cnt])]:
            sys.exit(32)
        
    return(True)

#interpretuje dane instrukcie/ vola pomocne funkcie pre interpretaciu instrukcii
def interpret(inputfile):
    #zoradi poradie instrukcii
    inst_order.sort()    
    position = 0
    while(position < len (inst_order)):
        current_inst = instruction_dict["inst"+ str(inst_order[position])]["opcode"]
        if current_inst == "LABEL":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[position])], 1, position)
            label(instruction_dict["inst"+ str(inst_order[position])]["arg1"], position)
        position += 1
    cnt = 0
    
    while cnt < len(inst_order):
        current_inst = instruction_dict["inst"+ str(inst_order[cnt])]["opcode"]
        if current_inst == "MOVE":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 2, cnt)
            move(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"], instruction_dict["inst"+ str(inst_order[cnt])]["arg2"])
        elif current_inst == "CREATEFRAME":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 0, cnt)
            createframe()
        elif current_inst == "PUSHFRAME":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 0, cnt)
            pushframe()
        elif current_inst == "POPFRAME":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 0, cnt)
            popframe()
        elif current_inst == "DEFVAR": 
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 1, cnt)
            defvar(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"])
        elif current_inst == "CALL":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 1, cnt)
            cnt = call(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"], cnt)
        elif current_inst == "RETURN":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 0, cnt)
            cnt = return_inst()
        elif current_inst == "PUSHS":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 1, cnt)
            pushs(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"])
        elif current_inst == "POPS":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 1, cnt)
            pops(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"])
        elif current_inst == "ADD":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 3, cnt)
            add(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"], instruction_dict["inst"+ str(inst_order[cnt])]["arg2"], instruction_dict["inst"+ str(inst_order[cnt])]["arg3"])
        elif current_inst == "SUB":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 3, cnt)
            sub(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"], instruction_dict["inst"+ str(inst_order[cnt])]["arg2"], instruction_dict["inst"+ str(inst_order[cnt])]["arg3"])
        elif current_inst == "MUL":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 3, cnt)
            mul(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"], instruction_dict["inst"+ str(inst_order[cnt])]["arg2"], instruction_dict["inst"+ str(inst_order[cnt])]["arg3"])
        elif current_inst == "IDIV":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 3, cnt)
            idiv(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"], instruction_dict["inst"+ str(inst_order[cnt])]["arg2"], instruction_dict["inst"+ str(inst_order[cnt])]["arg3"])
        elif current_inst == "LT":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 3, cnt)
            lt(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"], instruction_dict["inst"+ str(inst_order[cnt])]["arg2"], instruction_dict["inst"+ str(inst_order[cnt])]["arg3"])
        elif current_inst == "GT":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 3, cnt)
            gt(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"], instruction_dict["inst"+ str(inst_order[cnt])]["arg2"], instruction_dict["inst"+ str(inst_order[cnt])]["arg3"])
        elif current_inst == "EQ":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 3, cnt)
            eq(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"], instruction_dict["inst"+ str(inst_order[cnt])]["arg2"], instruction_dict["inst"+ str(inst_order[cnt])]["arg3"])
        elif current_inst == "AND":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 3, cnt)
            and_inst(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"], instruction_dict["inst"+ str(inst_order[cnt])]["arg2"], instruction_dict["inst"+ str(inst_order[cnt])]["arg3"])
        elif current_inst == "OR":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 3, cnt)
            or_inst(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"], instruction_dict["inst"+ str(inst_order[cnt])]["arg2"], instruction_dict["inst"+ str(inst_order[cnt])]["arg3"])
        elif current_inst == "NOT":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 2, cnt)
            not_inst(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"], instruction_dict["inst"+ str(inst_order[cnt])]["arg2"])
        elif current_inst == "INT2CHAR":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 2, cnt)
            int2char(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"], instruction_dict["inst"+ str(inst_order[cnt])]["arg2"])
        elif current_inst == "STRI2INT":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 3, cnt)
            stri2int(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"], instruction_dict["inst"+ str(inst_order[cnt])]["arg2"], instruction_dict["inst"+ str(inst_order[cnt])]["arg3"])
        elif current_inst == "READ":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 2, cnt)
            read(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"], instruction_dict["inst"+ str(inst_order[cnt])]["arg2"], inputfile)
        elif current_inst == "WRITE":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 1, cnt)
            write(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"])
        elif current_inst == "CONCAT":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 3, cnt)
            concat(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"], instruction_dict["inst"+ str(inst_order[cnt])]["arg2"], instruction_dict["inst"+ str(inst_order[cnt])]["arg3"])
        elif current_inst == "STRLEN":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 2, cnt)
            strlen(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"], instruction_dict["inst"+ str(inst_order[cnt])]["arg2"])
        elif current_inst == "GETCHAR":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 3, cnt)
            getchar(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"], instruction_dict["inst"+ str(inst_order[cnt])]["arg2"], instruction_dict["inst"+ str(inst_order[cnt])]["arg3"])
        elif current_inst == "SETCHAR":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 3, cnt)
            setchar(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"], instruction_dict["inst"+ str(inst_order[cnt])]["arg2"], instruction_dict["inst"+ str(inst_order[cnt])]["arg3"])
        elif current_inst == "TYPE":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 2, cnt)
            type_inst(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"], instruction_dict["inst"+ str(inst_order[cnt])]["arg2"])
        elif current_inst == "LABEL":
            pass
        elif current_inst == "JUMP":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 1, cnt)
            cnt = jump(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"])
        elif current_inst == "JUMPIFEQ":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 3, cnt)
            cnt = jumpifeq(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"], instruction_dict["inst"+ str(inst_order[cnt])]["arg2"], instruction_dict["inst"+ str(inst_order[cnt])]["arg3"], cnt)
        elif current_inst == "JUMPIFNEQ":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 3, cnt)
            cnt = jumpifneq(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"], instruction_dict["inst"+ str(inst_order[cnt])]["arg2"], instruction_dict["inst"+ str(inst_order[cnt])]["arg3"], cnt)
        elif current_inst == "EXIT":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 1, cnt)
            exit_inst(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"])
        elif current_inst == "DPRINT":
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 1, cnt)
            dprint(instruction_dict["inst"+ str(inst_order[cnt])]["arg1"])
        else:
            arg_cnt_check(instruction_dict["inst"+ str(inst_order[cnt])], 0, cnt)
            break_inst()
        cnt += 1
        
def main():
    srcfile, inputfile = arg_parse()
    build_and_save_xmltree(srcfile)
    interpret(inputfile)

    sys.exit(0)
    
if __name__ == '__main__':
    main()