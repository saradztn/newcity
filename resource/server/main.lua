--[[
    main.lua - Server-Side Lifecycle & Player Synchronization
    Provides teleportation commands to the new American city, global time/weather sync,
    and server administration commands.
]]

-- Downtown Grand Boulevard Spawn Coordinates
local CITY_POIS = {
    center     = {-4076.838, 492.024, 162.6},
    spawn      = {-4076.838, 492.024, 162.6},
    plaza      = {-4076.838, 492.024, 162.6},
    downtown   = {-4076.838, 572.024, 162.6},
    hotel      = {-4076.838, 412.024, 162.6},
    waterfront = {-4076.838, 672.024, 162.6},
    bridge     = {-4076.838, 732.024, 176.6},
    expressway = {-3876.838, 492.024, 174.6},
    tunnel     = {-4076.838, 292.024, 162.6},
    industrial = {-3956.838, 372.024, 162.6},
    park       = {-4156.838, 652.024, 162.6},
    cityhall   = {-4236.838, 652.024, 162.6},
}

addEventHandler("onResourceStart", resourceRoot, function()
    outputServerLog("[NewAmericanCity] Resource started successfully. Procedural metropolis ready.")
    -- Set default morning time and clear weather
    setTime(8, 0)
    setWeather(0)
    setMinuteDuration(1000) -- Smooth time passage
end)

-- Teleport command to spawn in the new city
addCommandHandler("citytp", function(player, cmd, locName)
    locName = locName and string.lower(locName) or "center"
    local coords = CITY_POIS[locName] or CITY_POIS["center"]

    if isElement(player) then
        setElementPosition(player, coords[1], coords[2], coords[3])
        outputChatBox(string.format("[NewCity] Welcome to New American City! Location: %s", locName), player, 100, 220, 255)
    end
end)

-- Time change command
addCommandHandler("citytime", function(player, cmd, hourStr, minStr)
    local h = tonumber(hourStr)
    local m = tonumber(minStr) or 0
    if h and h >= 0 and h <= 23 then
        setTime(h, m)
        outputChatBox(string.format("[NewCity] Server time updated to %02d:%02d", h, m), root, 255, 220, 100)
    else
        outputChatBox("Usage: /citytime <0-23> [minute]", player, 255, 120, 120)
    end
end)

-- Weather change command
addCommandHandler("cityweather", function(player, cmd, weatherId)
    local w = tonumber(weatherId)
    if w and w >= 0 and w <= 20 then
        setWeather(w)
        outputChatBox(string.format("[NewCity] Server weather updated to ID %d", w), root, 255, 220, 100)
    else
        outputChatBox("Usage: /cityweather <0-20>", player, 255, 120, 120)
    end
end)
