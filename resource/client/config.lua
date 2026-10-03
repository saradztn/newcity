--[[
    config.lua - Graphics Engine Quality Presets & Runtime Configuration
    Provides LOW, MEDIUM, HIGH, and ULTRA performance tiers for MTA:SA (DirectX 9).
]]

Config = {}

Config.Presets = {
    LOW = {
        name = "LOW",
        enableRoadShader = false,
        enableBuildingShader = false,
        enableSunShafts = false,
        enableSSR = false,
        enableRainScreen = false,
        enableWaterShader = false,
        renderTargetScale = 0.5,
        streamDistance = 450.0,
        lodDistanceMultiplier = 0.75,
        maxDynamicLights = 4,
    },
    MEDIUM = {
        name = "MEDIUM",
        enableRoadShader = true,
        enableBuildingShader = true,
        enableSunShafts = false,
        enableSSR = false,
        enableRainScreen = true,
        enableWaterShader = true,
        renderTargetScale = 0.5,
        streamDistance = 650.0,
        lodDistanceMultiplier = 1.0,
        maxDynamicLights = 8,
    },
    HIGH = {
        name = "HIGH",
        enableRoadShader = true,
        enableBuildingShader = true,
        enableSunShafts = true,
        enableSSR = true,
        enableRainScreen = true,
        enableWaterShader = true,
        renderTargetScale = 0.75,
        streamDistance = 900.0,
        lodDistanceMultiplier = 1.25,
        maxDynamicLights = 16,
    },
    ULTRA = {
        name = "ULTRA",
        enableRoadShader = true,
        enableBuildingShader = true,
        enableSunShafts = true,
        enableSSR = true,
        enableRainScreen = true,
        enableWaterShader = true,
        renderTargetScale = 1.0,
        streamDistance = 1400.0,
        lodDistanceMultiplier = 1.6,
        maxDynamicLights = 32,
    }
}

-- Default to HIGH preset
Config.CurrentPreset = Config.Presets.HIGH

function setQualityPreset(presetName)
    local upper = string.upper(presetName)
    if Config.Presets[upper] then
        Config.CurrentPreset = Config.Presets[upper]
        outputChatBox("[NewCity Engine] Quality Preset set to: " .. upper, 100, 220, 255)
        triggerEvent("onQualityPresetChanged", localPlayer, upper)
        return true
    else
        outputChatBox("[NewCity Engine] Invalid preset. Use: LOW, MEDIUM, HIGH, ULTRA", 255, 100, 100)
        return false
    end
end

addCommandHandler("cityquality", function(cmd, preset)
    if preset then
        setQualityPreset(preset)
    else
        outputChatBox("[NewCity Engine] Current preset: " .. Config.CurrentPreset.name, 255, 220, 100)
        outputChatBox("Usage: /cityquality [low | med | high | ultra]", 200, 200, 200)
    end
end)
