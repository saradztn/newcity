//--------------------------------------------------------------------------------------
// sky_atmosphere.fx - Dynamic Atmospheric Scattering, Sun Disc & Cloud Shader
// Implements Rayleigh / Mie scattering approximations, dynamic sun disc with
// limb darkening, scrolling multi-layer clouds, and sunset horizon scattering.
// Fully compliant with DirectX 9 SM 3.0 and SM 2.0 limits.
//--------------------------------------------------------------------------------------

float2 gSunScreenPos;      // Normalized screen position of sun
float  gSunElevation;      // Sun angle above horizon in radians
float3 gSunColor;          // Sun core & corona color
float3 gSkyZenithColor;    // Deep upper sky color
float3 gSkyHorizonColor;   // Horizon haze / scattering color
float  gCloudCoverage;     // 0.0 = clear sky, 1.0 = full storm overcast
float  gTime;
float  gAspectRatio;

texture gCloudTexture;     // Cloud density map
sampler2D CloudSampler = sampler_state
{
    Texture = <gCloudTexture>;
    MinFilter = Linear;
    MagFilter = Linear;
    MipFilter = Linear;
    AddressU = Wrap;
    AddressV = Wrap;
};

struct PS_INPUT
{
    float4 Position : POSITION0;
    float2 TexCoord : TEXCOORD0;
};

// Shader Model 3.0: Full Sky Atmosphere
float4 PixelShaderFunction_SM3(PS_INPUT input) : COLOR0
{
    float horizonT = pow(saturate(input.TexCoord.y), 1.6);
    float3 skyColor = lerp(gSkyZenithColor, gSkyHorizonColor, horizonT);

    float2 delta = input.TexCoord - gSunScreenPos;
    delta.x *= gAspectRatio;
    float distToSun = length(delta);

    float sunDiscRadius = 0.024;
    float inDisc = saturate(1.0 - (distToSun / sunDiscRadius));
    float limbDarkening = pow(inDisc, 0.45);
    float3 sunCore = gSunColor * limbDarkening * 4.0 * step(distToSun, sunDiscRadius);

    float coronaGlow = 0.022 / (distToSun * distToSun + 0.0035);
    float3 coronaColor = gSunColor * coronaGlow * 0.45;

    float2 cloudUV1 = input.TexCoord * 1.5 + float2(gTime * 0.004, gTime * 0.002);
    float2 cloudUV2 = input.TexCoord * 3.0 + float2(-gTime * 0.002, gTime * 0.005);

    float cloudDensity1 = tex2D(CloudSampler, cloudUV1).a;
    float cloudDensity2 = tex2D(CloudSampler, cloudUV2).a;
    float totalCloud = saturate((cloudDensity1 * 0.65 + cloudDensity2 * 0.35) * gCloudCoverage * 2.0);

    float3 cloudSunlit = lerp(float3(0.95, 0.95, 0.95), gSunColor * 1.4, saturate(1.0 - gSunElevation * 1.5));
    float3 cloudShadowed = gSkyHorizonColor * 0.45;
    float3 cloudFinalColor = lerp(cloudShadowed, cloudSunlit, cloudDensity1);

    float3 backgroundWithSun = skyColor + coronaColor + sunCore;
    float3 finalColor = lerp(backgroundWithSun, cloudFinalColor, totalCloud);

    return float4(finalColor, 1.0);
}

// Shader Model 2.0: Optimized Fallback (< 25 instructions)
float4 PixelShaderFunction_SM2(PS_INPUT input) : COLOR0
{
    float horizonT = saturate(input.TexCoord.y * 1.3);
    float3 skyColor = lerp(gSkyZenithColor, gSkyHorizonColor, horizonT);

    float2 delta = input.TexCoord - gSunScreenPos;
    float distToSun = length(delta);
    float inDisc = saturate(1.0 - (distToSun / 0.035));
    float3 sunDisc = gSunColor * inDisc * 2.5;

    float2 cloudUV = input.TexCoord * 1.5 + float2(gTime * 0.003, 0.0);
    float cloudA = tex2D(CloudSampler, cloudUV).a * gCloudCoverage;

    float3 finalColor = lerp(skyColor + sunDisc, float3(0.85, 0.85, 0.85), cloudA);
    return float4(finalColor, 1.0);
}

technique SkyAtmosphere
{
    pass P0
    {
        PixelShader = compile ps_3_0 PixelShaderFunction_SM3();
    }
}

technique SkyAtmosphere_SM2
{
    pass P0
    {
        PixelShader = compile ps_2_0 PixelShaderFunction_SM2();
    }
}
