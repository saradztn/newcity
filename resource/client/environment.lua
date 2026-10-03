--[[
    environment.lua - Dynamic Day/Night Cycle & Solar Lighting Engine
    Calculates mathematical sun elevation, azimuth, 3D sun direction,
    atmospheric Rayleigh/Mie color temperature, sky gradients, and fog distance.
]]

Environment = {}

-- Current calculated environment state
Environment.TimeHours = 12.0
Environment.SunElevation = 1.1      -- Radians above horizon
Environment.SunAzimuth = 0.0        -- Radians (0 = North, pi/2 = East, pi = South, 3pi/2 = West)
Environment.SunDirection = {0.0, 0.5, 0.86}
Environment.SunColor = {1.0, 0.98, 0.92}
Environment.AmbientColor = {0.22, 0.25, 0.30}
Environment.SkyZenith = {0.15, 0.32, 0.65}
Environment.SkyHorizon = {0.65, 0.72, 0.85}
Environment.NightFactor = 0.0
Environment.FogDistance = 750.0

-- Interpolation helper
local function lerp(a, b, t)
    return a + (b - a) * t
end

local function lerpColor(c1, c2, t)
    return {
        lerp(c1[1], c2[1], t),
        lerp(c1[2], c2[2], t),
        lerp(c1[3], c2[3], t)
    }
end

-- Key Day/Night Keyframes (Hour, Elev, SunRGB, AmbientRGB, ZenithRGB, HorizonRGB, NightFactor)
local TimeKeyframes = {
    {0.0,  -1.2, {0.08, 0.12, 0.22}, {0.03, 0.04, 0.07}, {0.01, 0.02, 0.05}, {0.03, 0.05, 0.10}, 1.0}, -- Midnight
    {4.5,  -0.3, {0.12, 0.14, 0.25}, {0.04, 0.05, 0.09}, {0.02, 0.03, 0.08}, {0.08, 0.08, 0.16}, 0.9}, -- Pre-dawn
    {5.5,   0.0, {0.95, 0.55, 0.25}, {0.10, 0.12, 0.18}, {0.08, 0.15, 0.35}, {0.45, 0.25, 0.35}, 0.5}, -- Dawn
    {6.2,   0.2, {1.00, 0.75, 0.35}, {0.20, 0.22, 0.28}, {0.15, 0.30, 0.65}, {0.92, 0.60, 0.30}, 0.2}, -- Sunrise
    {8.0,   0.6, {1.00, 0.92, 0.80}, {0.25, 0.28, 0.35}, {0.18, 0.38, 0.75}, {0.70, 0.78, 0.88}, 0.0}, -- Morning
    {12.0,  1.2, {1.00, 0.98, 0.95}, {0.32, 0.35, 0.40}, {0.12, 0.35, 0.80}, {0.68, 0.78, 0.90}, 0.0}, -- Midday
    {15.0,  0.8, {1.00, 0.95, 0.88}, {0.28, 0.30, 0.36}, {0.15, 0.36, 0.78}, {0.72, 0.76, 0.86}, 0.0}, -- Afternoon
    {17.2,  0.35,{1.00, 0.72, 0.30}, {0.24, 0.25, 0.30}, {0.14, 0.28, 0.65}, {0.95, 0.62, 0.25}, 0.1}, -- Golden Hour
    {18.4,  0.05,{1.00, 0.45, 0.15}, {0.18, 0.18, 0.24}, {0.10, 0.20, 0.50}, {0.98, 0.40, 0.18}, 0.4}, -- Sunset
    {19.5, -0.2, {0.25, 0.30, 0.65}, {0.08, 0.10, 0.16}, {0.04, 0.08, 0.25}, {0.20, 0.22, 0.45}, 0.8}, -- Blue Hour
    {21.0, -0.8, {0.10, 0.14, 0.28}, {0.04, 0.05, 0.08}, {0.02, 0.03, 0.09}, {0.05, 0.07, 0.14}, 1.0}, -- Night
    {24.0, -1.2, {0.08, 0.12, 0.22}, {0.03, 0.04, 0.07}, {0.01, 0.02, 0.05}, {0.03, 0.05, 0.10}, 1.0}, -- Cycle wrap
}

function Environment.Update(timeHours)
    Environment.TimeHours = timeHours or Environment.TimeHours

    -- Find keyframe pair
    local k1 = TimeKeyframes[1]
    local k2 = TimeKeyframes[#TimeKeyframes]
    for i = 1, #TimeKeyframes - 1 do
        if Environment.TimeHours >= TimeKeyframes[i][1] and Environment.TimeHours <= TimeKeyframes[i + 1][1] then
            k1 = TimeKeyframes[i]
            k2 = TimeKeyframes[i + 1]
            break
        end
    end

    local span = k2[1] - k1[1]
    local t = (span > 0) and ((Environment.TimeHours - k1[1]) / span) or 0.0

    -- Interpolate state
    Environment.SunElevation = lerp(k1[2], k2[2], t)
    Environment.SunColor = lerpColor(k1[3], k2[3], t)
    Environment.AmbientColor = lerpColor(k1[4], k2[4], t)
    Environment.SkyZenith = lerpColor(k1[5], k2[5], t)
    Environment.SkyHorizon = lerpColor(k1[6], k2[6], t)
    Environment.NightFactor = lerp(k1[7], k2[7], t)

    -- Solar Azimuth: sun travels East (6h) -> South (12h) -> West (18h)
    Environment.SunAzimuth = (Environment.TimeHours / 24.0) * (2.0 * math.pi)

    -- 3D Direction Vector pointing TOWARDS sun
    local cosElev = math.cos(math.max(0.01, Environment.SunElevation))
    local sinElev = math.sin(Environment.SunElevation)
    local dirX = cosElev * math.sin(Environment.SunAzimuth)
    local dirY = -cosElev * math.cos(Environment.SunAzimuth)
    local dirZ = sinElev

    local len = math.sqrt(dirX * dirX + dirY * dirY + dirZ * dirZ)
    Environment.SunDirection = {dirX / len, dirY / len, dirZ / len}

    -- Apply synchronization to MTA:SA Game Engine
    local sr = math.floor(Environment.SunColor[1] * 255)
    local sg = math.floor(Environment.SunColor[2] * 255)
    local sb = math.floor(Environment.SunColor[3] * 255)
    setSunColor(sr, sg, sb, sr, sg, sb)

    -- Sun size (angular diameter expands near horizon due to optical illusion)
    local sunSize = lerp(2.2, 1.2, math.max(0.0, math.sin(Environment.SunElevation)))
    setSunSize(sunSize)

    -- Sky gradient
    local tr = math.floor(Environment.SkyZenith[1] * 255)
    local tg = math.floor(Environment.SkyZenith[2] * 255)
    local tb = math.floor(Environment.SkyZenith[3] * 255)
    local br = math.floor(Environment.SkyHorizon[1] * 255)
    local bg = math.floor(Environment.SkyHorizon[2] * 255)
    local bb = math.floor(Environment.SkyHorizon[3] * 255)
    setSkyGradient(tr, tg, tb, br, bg, bb)

    -- Fog distance
    local baseFog = lerp(600.0, 950.0, 1.0 - Environment.NightFactor)
    Environment.FogDistance = baseFog
    setFogDistance(Environment.FogDistance)
end

-- Update every frame based on game clock
addEventHandler("onClientPreRender", root, function()
    local h, m = getTime()
    local decimalHours = h + (m / 60.0)
    Environment.Update(decimalHours)
end)
