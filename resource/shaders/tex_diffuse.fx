//--------------------------------------------------------------------------------------
// tex_diffuse.fx - Universal Direct Texture Mapper for MTA:SA
// Guarantees all world objects receive high-resolution photorealistic textures
// directly via DirectX 9 hardware samplers without depending solely on TXD.
//--------------------------------------------------------------------------------------

texture gTexture;
sampler2D Sampler0 = sampler_state
{
    Texture = <gTexture>;
    MinFilter = Linear;
    MagFilter = Linear;
    MipFilter = Linear;
    AddressU = Wrap;
    AddressV = Wrap;
};

struct VS_OUTPUT
{
    float4 Position : POSITION0;
    float2 TexCoord : TEXCOORD0;
    float4 Color    : COLOR0;
};

float4 PixelShaderFunction(VS_OUTPUT input) : COLOR0
{
    float4 texColor = tex2D(Sampler0, input.TexCoord);
    return texColor * input.Color;
}

technique TexDiffuse
{
    pass P0
    {
        PixelShader = compile ps_2_0 PixelShaderFunction();
    }
}
