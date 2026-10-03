//--------------------------------------------------------------------------------------
// street_light.fx - Volumetric Light Cone & Streetlight Halo Shader for MTA:SA
// Renders realistic street illumination cones, ground illumination attenuation,
// and color temperature transitions (sodium amber, halogen, cool LED).
//--------------------------------------------------------------------------------------

float4x4 gWorld : WORLD;
float4x4 gWorldViewProjection : WORLDVIEWPROJECTION;

float3 gLightPosition;
float3 gLightColor;       // Color temperature RGB (sodium, halogen, or LED)
float  gLightIntensity;   // Dynamic on/off intensity modulated by time of day
float  gLightRadius;

texture gTexture;         // Light Cone Falloff Texture
sampler2D ConeSampler = sampler_state
{
    Texture = <gTexture>;
    MinFilter = Linear;
    MagFilter = Linear;
    MipFilter = Linear;
    AddressU = Clamp;
    AddressV = Clamp;
};

struct VS_INPUT
{
    float4 Position : POSITION0;
    float2 TexCoord : TEXCOORD0;
    float4 Color    : COLOR0;
};

struct VS_OUTPUT
{
    float4 Position : POSITION0;
    float2 TexCoord : TEXCOORD0;
    float4 Color    : COLOR0;
};

VS_OUTPUT VertexShaderFunction(VS_INPUT input)
{
    VS_OUTPUT output;
    output.Position = mul(input.Position, gWorldViewProjection);
    output.TexCoord = input.TexCoord;
    output.Color = input.Color;
    return output;
}

float4 PixelShaderFunction(VS_OUTPUT input) : COLOR0
{
    float4 coneSample = tex2D(ConeSampler, input.TexCoord);

    // Modulate by dynamic light color and time-of-day intensity
    float3 finalColor = gLightColor * gLightIntensity * coneSample.rgb;
    float alpha = coneSample.a * gLightIntensity;

    return float4(finalColor, alpha);
}

technique StreetLight
{
    pass P0
    {
        VertexShader = compile vs_3_0 VertexShaderFunction();
        PixelShader  = compile ps_3_0 PixelShaderFunction();
    }
}

technique StreetLight_SM2
{
    pass P0
    {
        VertexShader = compile vs_2_0 VertexShaderFunction();
        PixelShader  = compile ps_2_0 PixelShaderFunction();
    }
}
