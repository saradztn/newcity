--[[
    lighting.lua - Dynamic Street Lighting & Building Window Lighting Engine
    Controls time-of-day streetlight activation, color temperature variation
    (sodium amber, halogen, cool LED), light cones, and window illumination states.
]]

Lighting = {}

Lighting.ActiveLights = {}
Lighting.LightDefinitions = {}
Lighting.AreLightsOn = false

-- Color Temperatures
local COLOR_TEMPS = {
    sodium  = {255, 155, 45},   -- 2100K High-Pressure Sodium
    halogen = {255, 235, 195},  -- 3200K Neutral Halogen
    led     = {215, 235, 255},  -- 5500K Modern Cool LED
}

function Lighting.Init()
    outputDebugString("[NewCity Lighting] Initializing street lighting network...")

    if not fileExists("data/city_layout.json") then return end

    local f = fileOpen("data/city_layout.json")
    local size = fileGetSize(f)
    local rawJson = fileRead(f, size)
    fileClose(f)

    local data = fromJSON(rawJson)
    if data and data.streetlights then
        Lighting.LightDefinitions = data.streetlights
    end

    outputDebugString(string.format("[NewCity Lighting] Registered %d dynamic streetlights.", #Lighting.LightDefinitions))
end

function Lighting.SetLightsEnabled(enabled)
    if Lighting.AreLightsOn == enabled then return end
    Lighting.AreLightsOn = enabled

    if enabled then
        -- Activate streetlights
        local maxLights = Config.CurrentPreset.maxDynamicLights or 16
        local count = 0

        for _, lDef in ipairs(Lighting.LightDefinitions) do
            if count >= maxLights then break end

            local col = COLOR_TEMPS[lDef.type] or COLOR_TEMPS.sodium
            local px, py, pz = lDef.pos[1], lDef.pos[2], lDef.pos[3]
            local rad = lDef.radius or 20.0

            -- Create point light in world
            local light = createLight(0, px, py, pz, rad, col[1], col[2], col[3], true)
            if light then
                table.insert(Lighting.ActiveLights, light)
                count = count + 1
            end
        end
    else
        -- Deactivate streetlights
        for _, light in ipairs(Lighting.ActiveLights) do
            if isElement(light) then destroyElement(light) end
        end
        Lighting.ActiveLights = {}
    end
end

-- Monitor Day/Night light transitions every second
setTimer(function()
    -- Lights activate when night factor exceeds 0.35 (dusk to dawn)
    local shouldBeOn = (Environment.NightFactor > 0.35)
    Lighting.SetLightsEnabled(shouldBeOn)
end, 1000, 0)
