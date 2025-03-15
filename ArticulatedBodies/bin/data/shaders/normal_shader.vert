#version 330

// these are for the programmable pipeline system and are passed in
// by default from OpenFrameworks
layout(location = 0) in vec4 vertexPosition_ModelSpace;
layout(location = 2) in vec3 vertexNormal_ModelSpace;

out vec3 normal_CameraSpace;

uniform vec4 Color;
uniform mat4 ProjectionMatrix;
uniform mat4 ModelMatrix;
uniform mat4 ViewMatrix;

void main()
{
	gl_Position =  ProjectionMatrix * ViewMatrix * ModelMatrix * vertexPosition_ModelSpace;

	// Only correct if ModelMatrix does not scale the model ! Use its inverse transpose if not.
	normal_CameraSpace = ( ViewMatrix * ModelMatrix * vec4(vertexNormal_ModelSpace,0)).xyz; 
}