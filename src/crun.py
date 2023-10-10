cruntime = """
--// cruntime.lua \\\\--
-- This file is apart of the RCC project.
-- specifically the roblox-c compiler.

-- CASTING
function cast(type, value)
    type = type:gsub("long", ""):gsub("short", "")
    if type == "int" then
        return tonumber(value)
    elseif type == "string" then
        return tostring(value)
    elseif type == "char" then
        return tostring(value)
    elseif type == "float" then
        return tonumber(value)
    elseif type == "double" then
        return tonumber(value)
    elseif type == "bool" then
        if value then
            return true
        else
            return false
        end
    else 
        error("[roblox-c] c-like-casting error: type '" .. type .. "' is not a supported type.")
    end
end

-- SWITCH
def = newproxy()
brk = newproxy()

function switch(value, cases)
    if cases[value] then
        local returnv = cases[value]()
        if returnv ~= nil then
            -- fallthrough
            start = false
            for i, v in cases do
                if i == value then
                    start = true
                end
                if start then
                    v()
                end
            end
        elseif returnv == brk then
            return nil
        else
            return returnv
        end
    elseif cases[def] then
        cases[def]()
    end
end

-- C++ 
construct = newproxy()
destruct = newproxy()

function new(methods, ...)
    if methods[construct] then
        methods[construct](...)
    end
    return methods 
end
function delete(obj)
    if obj[destruct] then
        obj[destruct]()
    end
end

-- MEMORY
-- todo: support directly modifying memory
_G.CMemory = _G.CMemory or {}

function malloc(size)
    _G.CMemory[#_G.CMemory+1] = table.create(size)
    return #_G.CMemory
end
function free(ptr)
    _G.CMemory[ptr] = nil
end
function realloc(ptr, size)
    _G.CMemory[ptr] = table.create(size)
    return #_G.CMemory
end
function calloc(size)
    _G.CMemory[#_G.CMemory+1] = table.create(size)
    return #_G.CMemory
end
function memset(ptr, value, size)
    for i = 1, size do
        _G.CMemory[ptr][i] = value
    end
end
function memcpy(dest, src, size)
    for i = 1, size do
        _G.CMemory[dest][i] = _G.CMemory[src][i]
    end
end
function memmove(dest, src, size)
    for i = 1, size do
        _G.CMemory[dest][i] = _G.CMemory[src][i]
    end
end
function memcmp(ptr1, ptr2, size)
    for i = 1, size do
        if _G.CMemory[ptr1][i] ~= _G.CMemory[ptr2][i] then
            return false
        end
    end
    return true
end
function memchr(ptr, value, size)
    for i = 1, size do
        if _G.CMemory[ptr][i] == value then
            return true
        end
    end
    return false
end

function ptr(value)
    _G.CMemory[_G.CMemory+1] = {value}
    return #_G.CMemory
end
function deref(ptr)
    return _G.CMemory[ptr]
end



return {
    -- INTERNAL
    cast = cast,
    switch = switch,
    new = new,
    delete = delete,
    ptr = ptr,
    deref = deref,
    
    -- STD
    malloc = malloc,
    free = free,
    realloc = realloc,
    calloc = calloc,
    memset = memset,
    memcpy = memcpy,
    memmove = memmove,
    memcmp = memcmp,
    memchr = memchr,
    printf = function(str, ...) print(str:format(...)) end,
    
    -- CONSTANTS
    construct = construct,
    destruct = destruct,
    def = def,
    brk = brk
}
"""