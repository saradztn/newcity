//--------------------------------------------------------------------------------------
// water_surface.fx - Photorealistic Animated Water Shader for MTA:SA
// Dual-scrolling wave normal maps, Fresnel sky reflection, sun specular glints,
// and depth absorption gradient (shallow turquoise to deep navy).
// Fully compliant with DirectX 9 SM 3.0 and SM 2.0 limits.
//--------------------------------------------------------------------------------------

float4x4 gWorld : WORLD;
float4x4 gWorldViewProjection : WORLDVIEWPROJECTION;
float4x4 gWorldInverseTranspose : WORLDINVERSETRANSPOSE;

float3 gCameraPosition;
float3 gSunDirection;
float3 gSunColor;
float3 gAmbientColor;
float  gTime;

texture gNormalTexture;      // Water wave normal map
sampler2D WaveSampler = sampler_state
{
    Texture = <gNormalTexture>;
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

// Shader Model 3.0: Dual-wave normal water
float4 PixelShaderFunction_SM3(VS_OUTPUT input) : COLOR0
{
    float2 uv1 = input.TexCoord * 3.0 + float2(gTime * 0.03, gTime * 0.015);
    float2 uv2 = input.TexCoord * 6.0 + float2(-gTime * 0.02, gTime * 0.025);

    float3 n1 = tex2D(WaveSampler, uv1).xyz * 2.0 - 1.0;
    float3 n2 = tex2D(WaveSampler, uv2).xyz * 2.0 - 1.0;
    float3 waveNormal = normalize(float3(n1.xy + n2.xy, n1.z * 1.5));

    float3 N = normalize(input.WorldNormal + waveNormal * 0.35);
    float3 V = normalize(gCameraPosition - input.WorldPos);
    float3 L = normalize(gSunDirection);
    float3 H = normalize(L + V);

    float3 deepWater = float3(0.04, 0.12, 0.22);
    float3 shallowWater = float3(0.08, 0.28, 0.38);
    float3 waterBase = lerp(deepWater, shallowWater, saturate(input.WorldPos.z * 0.2 + 0.5));

    float NdotV = saturate(dot(N, V));
    float fresnel = 0.02 + 0.98 * pow(1.0 - NdotV, 5.0);

    float NdotH = saturate(dot(N, H));
    float spec = pow(NdotH, 128.0) * 2.5;
    float3 sunGlint = gSunColor * spec * fresnel;

    float3 diffuseSky = gAmbientColor * fresnel * 1.4;
    float3 finalColor = waterBase * (1.0 - fresnel * 0.5) + diffuseSky + sunGlint;

    return float4(finalColor, 0.92);
}

// Shader Model 2.0: Single wave normal fallback (< 25 instructions)
float4 PixelShaderFunction_SM2(VS_OUTPUT input) : COLOR0
{
    float2 uv = input.TexCoord * 4.0 + float2(gTime * 0.02, gTime * 0.01);
    float3 waveNormal = tex2D(WaveSampler, uv).xyz * 2.0 - 1.0;
    float3 N = normalize(input.WorldNormal + waveNormal * 0.2);

    float3 waterBase = float3(0.06, 0.18, 0.28);
    float3 diffuse = waterBase + gAmbientColor * 0.5;
    return float4(diffuse, 0.92);
}

technique WaterSurface
{
    pass P0
    {
        VertexShader = compile vs_3_0 VertexShaderFunction();
        PixelShader  = compile ps_3_0 PixelShaderFunction_SM3();
    }
}

technique WaterSurface_SM2
{
    pass P0
    {
        VertexShader = compile vs_2_0 VertexShaderFunction();
        PixelShader  = compile ps_2_0 PixelShaderFunction_SM2();
    }
}
