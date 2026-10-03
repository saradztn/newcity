//--------------------------------------------------------------------------------------
// sky_atmosphere.fx - Dynamic Atmospheric Scattering, Sun Disc & Cloud Shader
// Implements Rayleigh / Mie scattering approximations, dynamic sun disc with
// limb darkening, scrolling multi-layer clouds, and sunset horizon scattering.
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

float4 PixelShaderFunction(PS_INPUT input) : COLOR0
{
    // 1. Vertical Sky Gradient (Rayleigh Scattering)
    // input.TexCoord.y = 0 at top of screen (zenith), 1 at bottom/horizon
    float horizonT = pow(saturate(input.TexCoord.y), 1.6);
    float3 skyColor = lerp(gSkyZenithColor, gSkyHorizonColor, horizonT);

    // 2. Dynamic Sun Disc & Corona Glow
    float2 delta = input.TexCoord - gSunScreenPos;
    delta.x *= gAspectRatio; // Correct for widescreen aspect ratio
    float distToSun = length(delta);

    // Sun core disc radius ~ 0.024 screen height (~0.5 degrees angular diameter)
    float sunDiscRadius = 0.024;
    float inDisc = saturate(1.0 - (distToSun / sunDiscRadius));
    // Limb darkening on disc
    float limbDarkening = pow(inDisc, 0.45);
    float3 sunCore = gSunColor * limbDarkening * 4.0 * step(distToSun, sunDiscRadius);

    // Mie scattering corona around the sun
    float coronaGlow = 0.022 / (distToSun * distToSun + 0.0035);
    float3 coronaColor = gSunColor * coronaGlow * 0.45;

    // 3. Cloud Layer with Scrolling UVs
    float2 cloudUV1 = input.TexCoord * 1.5 + float2(gTime * 0.004, gTime * 0.002);
    float2 cloudUV2 = input.TexCoord * 3.0 + float2(-gTime * 0.002, gTime * 0.005);

    float cloudDensity1 = tex2D(CloudSampler, cloudUV1).a;
    float cloudDensity2 = tex2D(CloudSampler, cloudUV2).a;
    float totalCloud = saturate((cloudDensity1 * 0.65 + cloudDensity2 * 0.35) * gCloudCoverage * 2.0);

    // Sunset cloud illumination: clouds illuminated by warm grazing sunlight
    float3 cloudSunlit = lerp(float3(0.95, 0.95, 0.95), gSunColor * 1.4, saturate(1.0 - gSunElevation * 1.5));
    float3 cloudShadowed = gSkyHorizonColor * 0.45;
    float3 cloudFinalColor = lerp(cloudShadowed, cloudSunlit, cloudDensity1);

    // Blend clouds over sky
    float3 backgroundWithSun = skyColor + coronaColor + sunCore;
    float3 finalColor = lerp(backgroundWithSun, cloudFinalColor, totalCloud);

    return float4(finalColor, 1.0);
}

technique SkyAtmosphere
{
    pass P0
    {
        PixelShader = compile ps_3_0 PixelShaderFunction();
    }
}

technique SkyAtmosphere_SM2
{
    pass P0
    {
        PixelShader = compile ps_2_0 PixelShaderFunction();
    }
}
