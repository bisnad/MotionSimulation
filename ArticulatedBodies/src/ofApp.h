#pragma once

#include "ofMain.h"
#include "ofxImGui.h"
#include "ofVectorMath.h"
#include "ofShader.h"
#include "ofVbo.h"
#include "dab_vis_body_shape.h"
#include "dab_vis_body_part.h"
#include "dab_physics_behavior.h"
#include "dab_physics_state.h"

class ofApp : public ofBaseApp{

	public:
		void setup();
		void update();
		void draw();

		void keyPressed(int key);
		void keyReleased(int key);
		void mouseMoved(int x, int y );
		void mouseDragged(int x, int y, int button);
		void mousePressed(int x, int y, int button);
		void mouseReleased(int x, int y, int button);
		void mouseEntered(int x, int y);
		void mouseExited(int x, int y);
		void windowResized(int w, int h);
		void dragEvent(ofDragInfo dragInfo);
		void gotMessage(ofMessage msg);

	protected:
		void setupPhysics();
		void setupStates();
		void setupGraphics();
		void setupOsc();

		void resetPhysics();

		void updatePhysics();
		void updateGraphics();
		void updateOsc();

		std::shared_ptr<dab::physics::StateMachine> mStateMachine;

		ofShader mShader;

		bool loadShader(ofShader& pShader, const std::string& pVertexShader, const std::string& pFragShader);
		std::string shaderErrorMessage(ofShader& pShader, GLenum pShaderType);

		glm::vec3 mVisLightPosition = glm::vec3(1.0, 2.0, -1.0);

		// GUI
		ofxImGui::Gui mGui;

		// debug
		bool mApplyExternalForce = false;
		//dab::physics::Behavior* mBehavior;

};
