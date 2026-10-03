//--------------------------------------------------------------------------------------
// sun_shafts.fx - Cinematic Dynamic God Rays / Light Shafts Shader for MTA:SA
// Performs screen-space radial integration from the 2D projected sun position,
// dithered sampling to eliminate banding, and atmospheric scattering attenuation.
//--------------------------------------------------------------------------------------

float2 gSunScreenPos;     // 2D Normalized screen coordinate of sun [0..1]
float  gSunVisibility;    // 0.0 = behind building/cloud, 1.0 = visible
float3 gSunShaftColor;    // Golden warm atmospheric scattering tint
float  gShaftIntensity;   // User quality / weather intensity multiplier
float  gDecay;            // Falloff per sample step (~0.94)
float  gDensity;          // Sampling ray step size (~0.85)
float  gWeight;           // Sample weight multiplier (~0.45)

texture gTexture;         // Screen Render Target / Scene Buffer
sampler2D ScreenSampler = sampler_state
{
    Texture = <gTexture>;
    MinFilter = Linear;
    MagFilter = Linear;
    MipFilter = None;
    AddressU = Clamp;
    AddressV = Clamp;
};

texture gDitherTexture;   // Blue Noise Dither Map
sampler2D DitherSampler = sampler_state
{
    Texture = <gDitherTexture>;
    MinFilter = Point;
    MagFilter = Point;
    MipFilter = None;
    AddressU = Wrap;
    AddressV = Wrap;
};

struct PS_INPUT
{
    float4 Position : POSITION0;
    float2 TexCoord : TEXCOORD0;
};

float4 PixelShaderFunction(PS_INPUT input) : COLOR0
{
    // If sun is fully invisible or behind the camera, skip ray marching
    if (gSunVisibility <= 0.001 || gShaftIntensity <= 0.001)
    {
        return tex2D(ScreenSampler, input.TexCoord);
    }

    // Direction vector from current pixel towards the sun screen position
    float2 deltaTexCoord = (input.TexCoord - gSunScreenPos);

    // Apply sampling density and step length
    deltaTexCoord *= 1.0 / 16.0 * gDensity;

    // Jitter initial step with dither noise to prevent radial banding artifacts
    float dither = tex2D(DitherSampler, input.TexCoord * 8.0).r;
    float2 curCoord = input.TexCoord + deltaTexCoord * (dither * 0.5);

    float4 originalColor = tex2D(ScreenSampler, input.TexCoord);
    float3 illuminationDecay = float3(1.0, 1.0, 1.0);
    float3 accumulatedShafts = float3(0.0, 0.0, 0.0);

    // 16 radial integration samples along ray towards sun
    [unroll]
    for (int i = 0; i < 16; i++)
    {
        curCoord -= deltaTexCoord;
        float3 sampleCol = tex2D(ScreenSampler, saturate(curCoord)).rgb;

        // Isolate bright elements (sky / sun disc) for scattering
        float luminance = dot(sampleCol, float3(0.299, 0.587, 0.114));
        sampleCol *= saturate((luminance - 0.45) * 2.0);

        sampleCol *= illuminationDecay * gWeight;
        accumulatedShafts += sampleCol;
        illuminationDecay *= gDecay;
    }

    // Colorize shafts with warm atmospheric Mie scattering tone
    float3 finalShafts = accumulatedShafts * gSunShaftColor * gShaftIntensity * gSunVisibility;

    // Blend additively onto original scene
    float3 finalColor = originalColor.rgb + finalShafts;

    return float4(finalColor, originalColor.a);
}

technique SunShafts
{
    pass P0
    {
        PixelShader = compile ps_3_0 PixelShaderFunction();
    }
}

technique SunShafts_SM2
{
    pass P0
    {
        PixelShader = compile ps_2_0 PixelShaderFunction();
    }
}
