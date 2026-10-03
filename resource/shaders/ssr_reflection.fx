//--------------------------------------------------------------------------------------
// ssr_reflection.fx - Screen-Space Reflection (SSR) Approximation for MTA:SA
// Approximates real-time reflections on wet asphalt, road puddles, glass, and water.
// Uses view-reflection projection, screen-edge attenuation, and roughness blurring.
// Fully compliant with DirectX 9 SM 3.0 and SM 2.0 limits.
//--------------------------------------------------------------------------------------

float  gReflectionStrength; // 0.0 to 1.0 (set by weather wetness)
float  gSurfaceRoughness;   // 0.0 = mirror puddle, 1.0 = matte dry road
float3 gCameraDirection;

texture gTexture;           // Scene Color Buffer / Render Target
sampler2D SceneSampler = sampler_state
{
    Texture = <gTexture>;
    MinFilter = Linear;
    MagFilter = Linear;
    MipFilter = None;
    AddressU = Clamp;
    AddressV = Clamp;
};

texture gNormalTexture;      // Surface Normal & Puddle Mask
sampler2D NormalSampler = sampler_state
{
    Texture = <gNormalTexture>;
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

// Shader Model 3.0: 4-tap blur reflection
float4 PixelShaderFunction_SM3(PS_INPUT input) : COLOR0
{
    float4 originalColor = tex2D(SceneSampler, input.TexCoord);

    if (gReflectionStrength <= 0.005)
    {
        return originalColor;
    }

    float3 normalSample = tex2D(NormalSampler, input.TexCoord).xyz * 2.0 - 1.0;
    float puddleMask = tex2D(NormalSampler, input.TexCoord).a;

    float2 reflectCoord = float2(input.TexCoord.x, 1.0 - input.TexCoord.y);
    reflectCoord.x += normalSample.x * 0.035;
    reflectCoord.y += normalSample.y * 0.035;

    float2 edgeDist = min(reflectCoord, 1.0 - reflectCoord);
    float edgeFade = saturate(min(edgeDist.x, edgeDist.y) * 8.0);

    float blurRadius = gSurfaceRoughness * 0.012;
    float3 blurredReflection = float3(0, 0, 0);

    blurredReflection += tex2D(SceneSampler, reflectCoord + float2(-blurRadius, -blurRadius)).rgb * 0.25;
    blurredReflection += tex2D(SceneSampler, reflectCoord + float2( blurRadius, -blurRadius)).rgb * 0.25;
    blurredReflection += tex2D(SceneSampler, reflectCoord + float2(-blurRadius,  blurRadius)).rgb * 0.25;
    blurredReflection += tex2D(SceneSampler, reflectCoord + float2( blurRadius,  blurRadius)).rgb * 0.25;

    float grazing = saturate(1.0 - abs(input.TexCoord.y - 0.5) * 2.0);
    float fresnel = 0.04 + 0.96 * pow(grazing, 3.0);

    float reflectionWeight = gReflectionStrength * edgeFade * fresnel;
    reflectionWeight *= lerp(0.35, 1.0, puddleMask);
    reflectionWeight *= (1.0 - gSurfaceRoughness * 0.7);

    float3 finalColor = lerp(originalColor.rgb, originalColor.rgb + blurredReflection * 0.65, saturate(reflectionWeight));
    return float4(finalColor, originalColor.a);
}

// Shader Model 2.0: Single-tap reflection fallback (< 20 instructions)
float4 PixelShaderFunction_SM2(PS_INPUT input) : COLOR0
{
    float4 originalColor = tex2D(SceneSampler, input.TexCoord);
    if (gReflectionStrength <= 0.005) return originalColor;

    float2 reflectCoord = float2(input.TexCoord.x, 1.0 - input.TexCoord.y);
    float3 refCol = tex2D(SceneSampler, reflectCoord).rgb;
    float3 finalColor = lerp(originalColor.rgb, originalColor.rgb + refCol * 0.5, gReflectionStrength * 0.5);
    return float4(finalColor, originalColor.a);
}

technique SSRReflection
{
    pass P0
    {
        PixelShader = compile ps_3_0 PixelShaderFunction_SM3();
    }
}

technique SSRReflection_SM2
{
    pass P0
    {
        PixelShader = compile ps_2_0 PixelShaderFunction_SM2();
    }
}
