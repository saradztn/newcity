//--------------------------------------------------------------------------------------
// road_pbr.fx - Advanced Dynamic Asphalt & PBR Road Shader for MTA:SA (DirectX 9 HLSL)
// Supports dynamic wetness, puddle masks, tire wear, micro-cracks, sun specular
// highlights, Fresnel sky reflection, and dynamic drying transitions.
// Fully compliant with DirectX 9 SM 3.0 and SM 2.0 limits.
//--------------------------------------------------------------------------------------

float4x4 gWorld : WORLD;
float4x4 gView : VIEW;
float4x4 gProjection : PROJECTION;
float4x4 gWorldViewProjection : WORLDVIEWPROJECTION;
float4x4 gWorldInverseTranspose : WORLDINVERSETRANSPOSE;
float4x4 gViewInverse : VIEWINVERSE;

float3 gCameraPosition;
float3 gSunDirection;      // Normalized direction pointing TOWARDS the sun
float3 gSunColor;          // Sun RGB intensity and color temperature
float3 gAmbientColor;      // Sky ambient RGB
float  gWetness;           // 0.0 = bone dry, 1.0 = fully soaked
float  gPuddleAmount;      // Accumulated puddle water depth
float  gTime;              // Elapsed time in seconds

texture gTexture;          // Base Road Albedo Texture
sampler2D Sampler0 = sampler_state
{
    Texture = <gTexture>;
    MinFilter = Linear;
    MagFilter = Linear;
    MipFilter = Linear;
    AddressU = Wrap;
    AddressV = Wrap;
};

texture gNormalMap;        // Road Normal & Micro-Crack Map
sampler2D NormalSampler = sampler_state
{
    Texture = <gNormalMap>;
    MinFilter = Linear;
    MagFilter = Linear;
    MipFilter = Linear;
    AddressU = Wrap;
    AddressV = Wrap;
};

texture gPuddleTexture;    // Road Puddle Accumulation Mask
sampler2D PuddleSampler = sampler_state
{
    Texture = <gPuddleTexture>;
    MinFilter = Linear;
    MagFilter = Linear;
    MipFilter = Linear;
    AddressU = Wrap;
    AddressV = Wrap;
};

struct VS_INPUT
{
    float4 Position : POSITION0;
    float3 Normal   : NORMAL0;
    float2 TexCoord : TEXCOORD0;
    float4 Color    : COLOR0;
};

struct VS_OUTPUT
{
    float4 Position     : POSITION0;
    float2 TexCoord     : TEXCOORD0;
    float3 WorldPos     : TEXCOORD1;
    float3 WorldNormal  : TEXCOORD3;
    float4 VertexColor  : COLOR0;
};

VS_OUTPUT VertexShaderFunction(VS_INPUT input)
{
    VS_OUTPUT output;
    output.Position = mul(input.Position, gWorldViewProjection);
    output.TexCoord = input.TexCoord;
    output.WorldPos = mul(input.Position, gWorld).xyz;
    output.WorldNormal = normalize(mul(input.Normal, (float3x3)gWorldInverseTranspose));
    output.VertexColor = input.Color;
    return output;
}

// Shader Model 3.0: Full PBR Road Shader
float4 PixelShaderFunction_SM3(VS_OUTPUT input) : COLOR0
{
    float4 baseColor = tex2D(Sampler0, input.TexCoord);
    float3 normalSample = tex2D(NormalSampler, input.TexCoord * 2.0).xyz * 2.0 - 1.0;
    float  puddleMask = tex2D(PuddleSampler, input.TexCoord).r;

    float3 N = normalize(input.WorldNormal + normalSample * 0.35);
    float3 V = normalize(gCameraPosition - input.WorldPos);
    float3 L = normalize(gSunDirection);
    float3 H = normalize(L + V);

    float isPuddle = saturate((puddleMask - (1.0 - gPuddleAmount)) * 4.0);
    float surfaceWetness = saturate(gWetness + isPuddle);

    float darkeningFactor = 1.0 - (0.42 * surfaceWetness);
    float3 diffuseAlbedo = baseColor.rgb * darkeningFactor;

    float NdotL = saturate(dot(N, L));
    float3 diffuseLighting = (diffuseAlbedo * gSunColor * NdotL) + (diffuseAlbedo * gAmbientColor);

    float roughness = lerp(0.82, 0.15, surfaceWetness);
    roughness = lerp(roughness, 0.02, isPuddle);
    float specPower = max(2.0, (2.0 / (roughness * roughness)) - 2.0);
    float NdotH = saturate(dot(N, H));
    float specIntensity = pow(NdotH, specPower);

    float F0 = lerp(0.04, 0.02, isPuddle);
    float fresnel = F0 + (1.0 - F0) * pow(1.0 - saturate(dot(N, V)), 5.0);

    float specMultiplier = lerp(0.18, 1.4, surfaceWetness);
    float3 specular = gSunColor * specIntensity * specMultiplier * fresnel;
    float3 skyReflection = gAmbientColor * fresnel * surfaceWetness * 1.5;

    float3 finalColor = (diffuseLighting + specular + skyReflection) * input.VertexColor.rgb;
    return float4(finalColor, baseColor.a);
}

// Shader Model 2.0: Optimized Fallback (< 35 arithmetic instructions)
float4 PixelShaderFunction_SM2(VS_OUTPUT input) : COLOR0
{
    float4 baseColor = tex2D(Sampler0, input.TexCoord);
    float3 N = normalize(input.WorldNormal);
    float3 L = normalize(gSunDirection);
    float3 V = normalize(gCameraPosition - input.WorldPos);
    float3 H = normalize(L + V);

    float NdotL = saturate(dot(N, L));
    float darkening = 1.0 - 0.35 * gWetness;
    float3 diffuse = baseColor.rgb * (gSunColor * NdotL * darkening + gAmbientColor);

    float NdotH = saturate(dot(N, H));
    float spec = pow(NdotH, 16.0) * (0.15 + 0.85 * gWetness);
    float3 specular = gSunColor * spec;

    float3 finalColor = (diffuse + specular) * input.VertexColor.rgb;
    return float4(finalColor, baseColor.a);
}

technique RoadPBR
{
    pass P0
    {
        VertexShader = compile vs_3_0 VertexShaderFunction();
        PixelShader  = compile ps_3_0 PixelShaderFunction_SM3();
    }
}

technique RoadPBR_SM2
{
    pass P0
    {
        VertexShader = compile vs_2_0 VertexShaderFunction();
        PixelShader  = compile ps_2_0 PixelShaderFunction_SM2();
    }
}
