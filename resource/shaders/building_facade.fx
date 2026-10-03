//--------------------------------------------------------------------------------------
// building_facade.fx - Dynamic Building Facade & Window Illumination Shader
// Handles architectural glass reflection, sun specular glints, and deterministic
// night window illumination (warm/cool interior lights modulated by time of day).
//--------------------------------------------------------------------------------------

float4x4 gWorld : WORLD;
float4x4 gWorldViewProjection : WORLDVIEWPROJECTION;
float4x4 gWorldInverseTranspose : WORLDINVERSETRANSPOSE;

float3 gCameraPosition;
float3 gSunDirection;
float3 gSunColor;
float3 gAmbientColor;
float  gNightFactor;       // 0.0 at noon, 1.0 at midnight
float  gTime;

texture gTexture;          // Facade Albedo
sampler2D Sampler0 = sampler_state
{
    Texture = <gTexture>;
    MinFilter = Linear;
    MagFilter = Linear;
    MipFilter = Linear;
    AddressU = Wrap;
    AddressV = Wrap;
};

texture gEmissiveTexture;  // Window Emissive Mask
sampler2D EmissiveSampler = sampler_state
{
    Texture = <gEmissiveTexture>;
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

float4 PixelShaderFunction(VS_OUTPUT input) : COLOR0
{
    float4 albedo = tex2D(Sampler0, input.TexCoord);
    float4 emissiveMask = tex2D(EmissiveSampler, input.TexCoord);

    float3 N = normalize(input.WorldNormal);
    float3 V = normalize(gCameraPosition - input.WorldPos);
    float3 L = normalize(gSunDirection);
    float3 H = normalize(L + V);

    // Diffuse sunlight
    float NdotL = saturate(dot(N, L));
    float3 diffuse = albedo.rgb * (gSunColor * NdotL + gAmbientColor);

    // Specular glass highlight (sharp on vertical glass facades)
    float NdotH = saturate(dot(N, H));
    float spec = pow(NdotH, 48.0) * 0.75;
    float fresnel = 0.05 + 0.95 * pow(1.0 - saturate(dot(N, V)), 5.0);
    float3 glassSpec = gSunColor * spec * fresnel;

    // Window Night Illumination:
    // Window interior warm glow (~2800K tungsten amber) or cool office fluorescent
    float3 windowTungsten = float3(1.0, 0.82, 0.55);
    float3 windowFluorescent = float3(0.85, 0.92, 1.0);
    // Alternate lighting tone based on floor coordinate
    float floorHash = frac(input.WorldPos.z * 0.31);
    float3 windowColor = lerp(windowTungsten, windowFluorescent, step(0.5, floorHash));

    float3 nightGlow = emissiveMask.r * windowColor * gNightFactor * 2.2;

    float3 finalColor = diffuse + glassSpec + nightGlow;
    finalColor *= input.VertexColor.rgb;

    return float4(finalColor, albedo.a);
}

technique BuildingFacade
{
    pass P0
    {
        VertexShader = compile vs_3_0 VertexShaderFunction();
        PixelShader  = compile ps_3_0 PixelShaderFunction();
    }
}

technique BuildingFacade_SM2
{
    pass P0
    {
        VertexShader = compile vs_2_0 VertexShaderFunction();
        PixelShader  = compile ps_2_0 PixelShaderFunction();
    }
}
