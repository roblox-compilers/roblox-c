import sys, os, json

#### LOG #####
def error(msg):
    print("\033[91;1merror\033[0m \033[90mC roblox-c:\033[0m " + msg)
def warn(msg):
    sys.stderr.write("\033[1;33m" + "warning: " + "\033[0m" + "\033[90mC roblox-c:\033[0m " + msg)
def info(msg):
    sys.stderr.write("\033[1;32m" + "info: " + "\033[0m" + "\033[90mC roblox-c:\033[0m " + msg)
    
    
#### CONSTANTS ####
CONFIG_FILE = os.path.expanduser('~/.config/rbxc/config.json')
VERSION = "1.0.0"
TAB = "\t\b\b\b\b"

#### DEPENDENCIES ####
try:
    import clang.cindex as clang
    from clang.cindex import Config
except ImportError:
    error("libclang could not be resolved")
    
#### COMPILER PARSER ####
def get_ast(file_path, c):
    test(file_path, c)
    try:
        index = clang.Index.create()
        translation_unit = index.parse(file_path)
        return translation_unit.cursor
    except clang.LibclangError as e:
        error("libclang error: " + str(e))
        sys.exit(1)
def print_ast(node, depth=0):
    print('  ' * depth + str(node.kind) + ' : ' + node.spelling)
    for child in node.get_children():
        print_ast(child, depth + 1)
def test(file_path, c):
    # Runs gcc on the file to check for errors, if there is an error sys.exit(1)
    if c:
        iserrors = os.system("gcc -fsyntax-only " + file_path)
    else:
        iserrors = os.system("g++ -fsyntax-only " + file_path)
    if iserrors != 0:
        sys.exit(1)
#### GENERATOR ####
class NodeVisitor(object):
    def __init__(self):
        self.indent = 0
        self.code = ""

    ### VISITORS ###
    def visit_translation_unit(self, node):
        for child in node.get_children():
            self.visit(child)
    def visit_function_decl(self, node):
        self.pushline("function " + node.spelling)
        for child in node.get_children():
            self.visit(child)
        self.pushline(")")
    def visit_parm_decl(self, node):
        self.pushexp(node.spelling)
        
    
    
    ### NODESYSTEM ###
    def visit(self, node):
        method = 'visit_' + node.kind.name.lower()
        visitor = getattr(self, method, self.generic_visit)
        if not getattr(visitor, 'visit_' + node.kind.name.lower(), None):
            error('{} unsupported'.format(node.kind.name.lower()))
            sys.exit(1)
        return visitor(node)
    def generic_visit(self, node):
        for child in node.get_children():
            self.visit(child)
    def pushline(self, code):
        self.code += "\n"+("\t"*self.indent)+code
    def pushexp(self, code):
        self.code += code

    
#### INTERFACE #### 
def check():
    if not os.path.exists(os.path.expanduser('~/.config/rbxc')):
        os.makedirs(os.path.expanduser('~/.config/rbxc'))
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            json.dump({}, f)
def config(key, value):
    check()
    # Load existing config file or create a new one if it doesn't exist
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config_data = json.load(f)
    else:
        config_data = {}

    # Update the config with the new key-value pair
    config_data[key] = value

    # Save the updated config to disk
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f)
def isconfig(key):
    check()
    # Load the config file
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config_data = json.load(f)
    else:
        config_data = {}

    # Return the value of the specified key, or None if it doesn't exist
    return config_data.get(key)  

def usage():
    print("\n"+f"""usage: \033[1;94mrbxc\033[0m [file] [options] -o [gen]
\033[1mOptions:\033[0m
{TAB}\033[1m-v\033[0m        show version information
{TAB}\033[1m-vd\033[0m       show version number only
{TAB}\033[1m-p\033[0m        set libclang path
{TAB}\033[1m-u\033[0m        open this""")
    sys.exit()
def version():
    print("\033[1;34m" + "copyright:" + "\033[0m" + " roblox-py " + "\033[1m" + VERSION + "\033[0m" + " licensed under the MIT License by " + "\033[1m" + "@AsynchronousAI" + "\033[0m")
    sys.exit(0)
def main():
    # read args
    args = sys.argv[1:]
    flags = []
    inputf = None
    outputf = None

    lookForOutput = False
    skip = False
    
    if isconfig("lclang"):
        Config.set_library_file(isconfig("lclang"))
        
    for i, arg in enumerate(args):
        if arg == "-o":
            lookForOutput = True
        elif arg == "-p":
            if len(args) > 1:
                Config.set_library_file(args[i+1])
                config("lclang", args[i+1])
                skip = True
            else:
                error("no path specified")
                sys.exit(1)
        elif arg == "-v":
            version()
        elif arg == "-vd":
            print(VERSION)
            sys.exit(0)
        elif arg == "-u":
            usage()
        elif arg.startswith("-"):
            flags.append(arg)
        elif inputf is None:
            inputf = arg
        elif lookForOutput:
            outputf = arg
            lookForOutput = False
        elif skip:
            skip = False
        else:
            error("too many arguments")
            sys.exit(1)
    
    if inputf is None:
        usage()
        sys.exit(1)
    
    if outputf is None:
        error("no output file specified")
        sys.exit(1)
    
    isC = None
    if inputf.endswith(".c"):
        isC = True
    elif inputf.endswith(".cpp") or inputf.endswith(".cxx") or inputf.endswith(".cc") or inputf.endswith(".C"):
        isC = False
    else:
        error("file must end with '.c', '.cpp', '.cxx', '.cc', or '.C'")
        sys.exit(1)
        
    parsed = get_ast(inputf, isC)
    print_ast(parsed)
    NodeVisitor().visit(parsed)
    
if __name__ == "__main__":
    main()