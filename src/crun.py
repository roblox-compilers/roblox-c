cruntime = """
--// cruntime.lua \\\\--
-- This file is apart of the RCC project.
-- specifically the roblox-c compiler.

-- CASTING
function cast(type, value)
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
function switch(value, cases)
    if cases[value] then
        returnv = cases[value]()
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
        end
    elseif cases[def] then
        cases[def]()
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
    cast = cast
}
"""