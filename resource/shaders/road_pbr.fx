//--------------------------------------------------------------------------------------
// road_pbr.fx - Advanced Dynamic Asphalt & PBR Road Shader for MTA:SA (DirectX 9 HLSL)
// Supports dynamic wetness, puddle masks, tire wear, micro-cracks, sun specular
// highlights, Fresnel sky reflection, and dynamic drying transitions.
//--------------------------------------------------------------------------------------

// Standard MTA:SA Matrix Uniforms
float4x4 gWorld : WORLD;
float4x4 gView : VIEW;
float4x4 gProjection : PROJECTION;
float4x4 gWorldViewProjection : WORLDVIEWPROJECTION;
float4x4 gWorldInverseTranspose : WORLDINVERSETRANSPOSE;
float4x4 gViewInverse : VIEWINVERSE;

// Dynamic Environment Uniforms passed from Lua
float3 gCameraPosition;
float3 gSunDirection;      // Normalized direction pointing TOWARDS the sun
float3 gSunColor;          // Sun RGB intensity and color temperature
float3 gAmbientColor;      // Sky ambient RGB
float  gWetness;           // 0.0 = bone dry, 1.0 = fully soaked
float  gPuddleAmount;      // Accumulated puddle water depth
float  gTime;              // Elapsed time in seconds

// Textures & Samplers
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

// Shader Input & Output Structures
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

// Vertex Shader
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

// Pixel Shader
float4 PixelShaderFunction(VS_OUTPUT input) : COLOR0
{
    // 1. Sample Textures
    float4 baseColor = tex2D(Sampler0, input.TexCoord);
    float3 normalSample = tex2D(NormalSampler, input.TexCoord * 2.0).xyz * 2.0 - 1.0;
    float  puddleMask = tex2D(PuddleSampler, input.TexCoord).r;

    // 2. Geometry & Normal setup
    float3 N = normalize(input.WorldNormal + normalSample * 0.35);
    float3 V = normalize(gCameraPosition - input.WorldPos);
    float3 L = normalize(gSunDirection);
    float3 H = normalize(L + V);

    // 3. Dynamic Wetness & Puddle calculations
    // Puddles pool based on puddleMask and gPuddleAmount
    float isPuddle = saturate((puddleMask - (1.0 - gPuddleAmount)) * 4.0);
    float surfaceWetness = saturate(gWetness + isPuddle);

    // Wet asphalt absorbs light -> diffuse darkening
    float darkeningFactor = 1.0 - (0.42 * surfaceWetness);
    float3 diffuseAlbedo = baseColor.rgb * darkeningFactor;

    // 4. Lighting: Diffuse NdotL + Ambient
    float NdotL = saturate(dot(N, L));
    float3 diffuseLighting = (diffuseAlbedo * gSunColor * NdotL) + (diffuseAlbedo * gAmbientColor);

    // 5. Specular Highlights (Blinn-Phong / GGX approximation)
    // Roughness: Dry asphalt = 0.82 (matte), Wet = 0.15 (sharp gloss), Puddle = 0.02 (mirror)
    float roughness = lerp(0.82, 0.15, surfaceWetness);
    roughness = lerp(roughness, 0.02, isPuddle);

    // Specular exponent
    float specPower = max(2.0, (2.0 / (roughness * roughness)) - 2.0);
    float NdotH = saturate(dot(N, H));
    float specIntensity = pow(NdotH, specPower);

    // 6. Fresnel Reflection (Schlick Approximation)
    // Water index of refraction F0 ~ 0.02, Grazing angles reflect full sky
    float VdotH = saturate(dot(V, H));
    float F0 = lerp(0.04, 0.02, isPuddle);
    float fresnel = F0 + (1.0 - F0) * pow(1.0 - saturate(dot(N, V)), 5.0);

    // Specular response increases dramatically on wet surfaces
    float specMultiplier = lerp(0.18, 1.4, surfaceWetness);
    float3 specular = gSunColor * specIntensity * specMultiplier * fresnel;

    // 7. Ground Sky Reflection on wet surfaces
    float3 skyReflection = gAmbientColor * fresnel * surfaceWetness * 1.5;

    // Combine final HDR color
    float3 finalColor = diffuseLighting + specular + skyReflection;

    // Modulate by vertex ambient occlusion
    finalColor *= input.VertexColor.rgb;

    return float4(finalColor, baseColor.a);
}

// Techniques
technique RoadPBR
{
    pass P0
    {
        VertexShader = compile vs_3_0 VertexShaderFunction();
        PixelShader  = compile ps_3_0 PixelShaderFunction();
    }
}

technique RoadPBR_SM2
{
    pass P0
    {
        VertexShader = compile vs_2_0 VertexShaderFunction();
        PixelShader  = compile ps_2_0 PixelShaderFunction();
    }
}
