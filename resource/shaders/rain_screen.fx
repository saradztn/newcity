//--------------------------------------------------------------------------------------
// rain_screen.fx - Camera Lens Raindrop Distortion & Atmospheric Storm Haze Shader
// Renders camera droplets, sliding streaks, and refractive distortion during rain/storms.
//--------------------------------------------------------------------------------------

float  gRainIntensity;   // 0.0 dry, 1.0 storm
float  gCameraSpeed;     // Distorts and wipes drops with vehicle/camera speed
float  gTime;

texture gTexture;         // Screen Color Buffer
sampler2D ScreenSampler = sampler_state
{
    Texture = <gTexture>;
    MinFilter = Linear;
    MagFilter = Linear;
    MipFilter = None;
    AddressU = Clamp;
    AddressV = Clamp;
};

texture gDropletTexture;  // Normal / droplet mask
sampler2D DropletSampler = sampler_state
{
    Texture = <gDropletTexture>;
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
    float4 sceneColor = tex2D(ScreenSampler, input.TexCoord);

    if (gRainIntensity <= 0.01)
    {
        return sceneColor;
    }

    // Scrolling droplet trails
    float2 dropUV = input.TexCoord * 1.5 + float2(0.0, gTime * 0.12 * (1.0 + gCameraSpeed * 0.05));
    float4 dropNormal = tex2D(DropletSampler, dropUV);

    // Refractive displacement (tangent XY offset)
    float2 distortion = (dropNormal.xy * 2.0 - 1.0) * 0.022 * gRainIntensity;

    // Distorted screen sample inside water droplets
    float3 refractedColor = tex2D(ScreenSampler, saturate(input.TexCoord + distortion)).rgb;

    // Specular highlight on drop edges
    float dropEdge = saturate(dropNormal.a * 2.0);
    float3 highlight = float3(1.0, 1.0, 1.0) * dropEdge * 0.25;

    float3 finalColor = lerp(sceneColor.rgb, refractedColor + highlight, dropNormal.a * gRainIntensity);

    return float4(finalColor, sceneColor.a);
}

technique RainScreen
{
    pass P0
    {
        PixelShader = compile ps_3_0 PixelShaderFunction();
    }
}

technique RainScreen_SM2
{
    pass P0
    {
        PixelShader = compile ps_2_0 PixelShaderFunction();
    }
}
