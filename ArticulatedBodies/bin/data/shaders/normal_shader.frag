#version 330

in vec3 normal_CameraSpace;

uniform vec4 Color;
out vec4 outputColor;
 
void main()
{
	outputColor = vec4(normal_CameraSpace, 1);
    //outputColor = Color;
}