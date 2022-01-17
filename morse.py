morse_alphabet = {
"A" : "x xxx ",
"B" : "xxx x x x ", 
"C" : "xxx x xxx x ", 
"D" : "xxx x x ", 
"E" : "x ", 
"F" : "x x xxx x ", 
"G" : "xxx xxx x ", 
"H" : "x x x x ", 
"I" : "x x ",
"J" : "x xxx xxx xxx ",
"K" : "xxx x xxx ",
"L" : "x xxx x xxx ",
"M" : "xxx xxx ",
"N" : "xxx x ",
"O" : "xxx xxx xxx ",
"P" : "x xxx xxx x ",
"Q" : "xxx xxx x xxx ",
"R" : "x xxx x ",
"S" : "x x x ",
"T" : "xxx ",
"U" : "x x xxx ",
"V" : "x x x xxx ",
"W" : "x xxx xxx ",
"X" : "xxx x x xxx ",
"Y" : "xxx x xxx xxx ",
"Z" : "xxx xxx x x ",
}

def morseTranslator(input):
    print("Translate:", input)
    res = ""
    for c in input.upper():
        res += morse_alphabet[c]
    return res