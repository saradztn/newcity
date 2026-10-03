--[[
    renderer.lua - Graphics Engine Renderer & Post-Processing Pipeline
    Manages HLSL DirectX 9 shaders, Render Targets, dynamic uniform updates,
    screen-space light shafts, SSR approximation, and weather effects.
]]

Renderer = {}

Renderer.Shaders = {}
Renderer.Textures = {}
Renderer.RenderTargets = {}

local sw, sh = guiGetScreenSize()

function Renderer.Init()
    outputDebugString("[NewCity Renderer] Initializing DX9 Graphics Engine...")

    -- 1. Load PBR Textures
    Renderer.Textures.normalAsphalt = dxCreateTexture("textures/asphalt_normal.dds", "dxt1")
    Renderer.Textures.puddleAsphalt = dxCreateTexture("textures/asphalt_puddle.dds", "dxt1")
    Renderer.Textures.emissiveGlass = dxCreateTexture("textures/bldg_glass_emissive.dds", "dxt1")
    Renderer.Textures.cloudsCumulus = dxCreateTexture("textures/clouds_cumulus.dds", "dxt5")
    Renderer.Textures.cloudsStorm = dxCreateTexture("textures/clouds_storm.dds", "dxt5")
    Renderer.Textures.dither = dxCreateTexture("textures/godray_dither.dds", "dxt1")
    Renderer.Textures.rainDroplets = dxCreateTexture("textures/rain_lens_droplets.dds", "dxt5")
    Renderer.Textures.waterNormal = dxCreateTexture("textures/water_normal.dds", "dxt1")

    -- 2. Create Shaders
    Renderer.Shaders.road = dxCreateShader("shaders/road_pbr.fx", 0, 0, false, "world,object")
    Renderer.Shaders.building = dxCreateShader("shaders/building_facade.fx", 0, 0, false, "world,object")
    Renderer.Shaders.water = dxCreateShader("shaders/water_surface.fx", 0, 0, false, "world,object")

    -- Post-processing shaders
    Renderer.Shaders.sunShafts = dxCreateShader("shaders/sun_shafts.fx")
    Renderer.Shaders.ssr = dxCreateShader("shaders/ssr_reflection.fx")
    Renderer.Shaders.rainScreen = dxCreateShader("shaders/rain_screen.fx")

    -- 3. Bind Samplers
    if Renderer.Shaders.road and Renderer.Textures.normalAsphalt then
        dxSetShaderValue(Renderer.Shaders.road, "gNormalMap", Renderer.Textures.normalAsphalt)
        dxSetShaderValue(Renderer.Shaders.road, "gPuddleTexture", Renderer.Textures.puddleAsphalt)

        -- Apply road shader to world road textures
        engineApplyShaderToWorldTexture(Renderer.Shaders.road, "asphalt*")
        engineApplyShaderToWorldTexture(Renderer.Shaders.road, "highway*")
        engineApplyShaderToWorldTexture(Renderer.Shaders.road, "sidewalk*")
        engineApplyShaderToWorldTexture(Renderer.Shaders.road, "concrete*")
    end

    if Renderer.Shaders.building and Renderer.Textures.emissiveGlass then
        dxSetShaderValue(Renderer.Shaders.building, "gEmissiveTexture", Renderer.Textures.emissiveGlass)
        engineApplyShaderToWorldTexture(Renderer.Shaders.building, "bldg*")
    end

    if Renderer.Shaders.water and Renderer.Textures.waterNormal then
        dxSetShaderValue(Renderer.Shaders.water, "gNormalTexture", Renderer.Textures.waterNormal)
        engineApplyShaderToWorldTexture(Renderer.Shaders.water, "water*")
    end

    -- 4. Create Post-Processing Render Target
    local rtScale = Config.CurrentPreset.renderTargetScale or 0.75
    local rtw = math.floor(sw * rtScale)
    local rth = math.floor(sh * rtScale)
    Renderer.RenderTargets.scene = dxCreateRenderTarget(rtw, rth, true)

    outputDebugString("[NewCity Renderer] Shaders initialized and mapped successfully.")
end

function Renderer.UpdateUniforms()
    local cx, cy, cz = getCameraMatrix()
    local sunDir = Environment.SunDirection
    local sunCol = Environment.SunColor
    local ambCol = Environment.AmbientColor
    local wetness = PuddleSystem.SurfaceWetness
    local puddleAmt = PuddleSystem.PuddleDepth
    local night = Environment.NightFactor
    local timeSec = getTickCount() / 1000.0

    -- 1. Update Road Shader
    if Renderer.Shaders.road and Config.CurrentPreset.enableRoadShader then
        dxSetShaderValue(Renderer.Shaders.road, "gCameraPosition", cx, cy, cz)
        dxSetShaderValue(Renderer.Shaders.road, "gSunDirection", sunDir[1], sunDir[2], sunDir[3])
        dxSetShaderValue(Renderer.Shaders.road, "gSunColor", sunCol[1], sunCol[2], sunCol[3])
        dxSetShaderValue(Renderer.Shaders.road, "gAmbientColor", ambCol[1], ambCol[2], ambCol[3])
        dxSetShaderValue(Renderer.Shaders.road, "gWetness", wetness)
        dxSetShaderValue(Renderer.Shaders.road, "gPuddleAmount", puddleAmt)
        dxSetShaderValue(Renderer.Shaders.road, "gTime", timeSec)
    end

    -- 2. Update Building Facade Shader
    if Renderer.Shaders.building and Config.CurrentPreset.enableBuildingShader then
        dxSetShaderValue(Renderer.Shaders.building, "gCameraPosition", cx, cy, cz)
        dxSetShaderValue(Renderer.Shaders.building, "gSunDirection", sunDir[1], sunDir[2], sunDir[3])
        dxSetShaderValue(Renderer.Shaders.building, "gSunColor", sunCol[1], sunCol[2], sunCol[3])
        dxSetShaderValue(Renderer.Shaders.building, "gAmbientColor", ambCol[1], ambCol[2], ambCol[3])
        dxSetShaderValue(Renderer.Shaders.building, "gNightFactor", night)
        dxSetShaderValue(Renderer.Shaders.building, "gTime", timeSec)
    end

    -- 3. Update Water Surface Shader
    if Renderer.Shaders.water and Config.CurrentPreset.enableWaterShader then
        dxSetShaderValue(Renderer.Shaders.water, "gCameraPosition", cx, cy, cz)
        dxSetShaderValue(Renderer.Shaders.water, "gSunDirection", sunDir[1], sunDir[2], sunDir[3])
        dxSetShaderValue(Renderer.Shaders.water, "gSunColor", sunCol[1], sunCol[2], sunCol[3])
        dxSetShaderValue(Renderer.Shaders.water, "gAmbientColor", ambCol[1], ambCol[2], ambCol[3])
        dxSetShaderValue(Renderer.Shaders.water, "gTime", timeSec)
    end
end

-- Render Post-Processing Effects Pass
addEventHandler("onClientRender", root, function()
    Renderer.UpdateUniforms()

    local preset = Config.CurrentPreset
    local cx, cy, cz = getCameraMatrix()
    local sunDir = Environment.SunDirection
    local timeSec = getTickCount() / 1000.0

    -- 1. Screen-Space Sun Shafts / God Rays
    if preset.enableSunShafts and Renderer.Shaders.sunShafts and Renderer.Textures.dither then
        -- Project 3D Sun position into 2D Screen Coordinates
        local sunDist = 700.0
        local sunWorldX = cx + sunDir[1] * sunDist
        local sunWorldY = cy + sunDir[2] * sunDist
        local sunWorldZ = cz + sunDir[3] * sunDist

        local screenX, screenY = getScreenFromWorldPosition(sunWorldX, sunWorldY, sunWorldZ, 0.2)
        local isSunVisible = (screenX and screenY and Environment.SunElevation > 0.0)

        if isSunVisible and Weather.CloudCoverage < 0.75 then
            local normX = screenX / sw
            local normY = screenY / sh

            -- Golden hour enhances shaft warmth
            local sunsetBoost = math.max(0.0, 1.0 - Environment.SunElevation * 1.8)
            local shaftCol = {
                Environment.SunColor[1] * (1.0 + sunsetBoost * 0.4),
                Environment.SunColor[2] * (1.0 + sunsetBoost * 0.2),
                Environment.SunColor[3]
            }

            dxSetShaderValue(Renderer.Shaders.sunShafts, "gSunScreenPos", normX, normY)
            dxSetShaderValue(Renderer.Shaders.sunShafts, "gSunVisibility", 1.0 - Weather.CloudCoverage)
            dxSetShaderValue(Renderer.Shaders.sunShafts, "gSunShaftColor", shaftCol[1], shaftCol[2], shaftCol[3])
            dxSetShaderValue(Renderer.Shaders.sunShafts, "gShaftIntensity", 0.55 + sunsetBoost * 0.4)
            dxSetShaderValue(Renderer.Shaders.sunShafts, "gDecay", 0.93)
            dxSetShaderValue(Renderer.Shaders.sunShafts, "gDensity", 0.85)
            dxSetShaderValue(Renderer.Shaders.sunShafts, "gWeight", 0.38)
            dxSetShaderValue(Renderer.Shaders.sunShafts, "gDitherTexture", Renderer.Textures.dither)

            -- Render full-screen quad with blend
            dxDrawImage(0, 0, sw, sh, Renderer.Shaders.sunShafts, 0, 0, 0, tocolor(255, 255, 255, 255))
        end
    end

    -- 2. Screen-Space Reflection Pass for wet roads & glass
    if preset.enableSSR and Renderer.Shaders.ssr and PuddleSystem.SurfaceWetness > 0.05 then
        dxSetShaderValue(Renderer.Shaders.ssr, "gReflectionStrength", PuddleSystem.SurfaceWetness * 0.65)
        dxSetShaderValue(Renderer.Shaders.ssr, "gSurfaceRoughness", math.max(0.05, 0.85 - PuddleSystem.SurfaceWetness * 0.75))
        if Renderer.Textures.normalAsphalt then
            dxSetShaderValue(Renderer.Shaders.ssr, "gNormalTexture", Renderer.Textures.normalAsphalt)
        end
        dxDrawImage(0, 0, sw, sh, Renderer.Shaders.ssr, 0, 0, 0, tocolor(255, 255, 255, 255))
    end

    -- 3. Rain Screen Droplet Pass
    if preset.enableRainScreen and Renderer.Shaders.rainScreen and Weather.RainIntensity > 0.05 then
        dxSetShaderValue(Renderer.Shaders.rainScreen, "gRainIntensity", Weather.RainIntensity)
        dxSetShaderValue(Renderer.Shaders.rainScreen, "gCameraSpeed", 0.0)
        dxSetShaderValue(Renderer.Shaders.rainScreen, "gTime", timeSec)
        if Renderer.Textures.rainDroplets then
            dxSetShaderValue(Renderer.Shaders.rainScreen, "gDropletTexture", Renderer.Textures.rainDroplets)
        end
        dxDrawImage(0, 0, sw, sh, Renderer.Shaders.rainScreen, 0, 0, 0, tocolor(255, 255, 255, 255))
    end
end)
